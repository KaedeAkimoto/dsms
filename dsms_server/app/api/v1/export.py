"""
数据导出API路由
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse

from app.core.middlewares import require_permission
from app.core.system_roles import api
from app.services.export import export_service
from app.services.audit_log import audit_log_writer

router = APIRouter()


@api(
    path="/export/tables",
    method="GET",
    name="获取可导出的表列表",
    description="获取所有可导出的数据库表名",
    tags=["系统管理"]
)
@router.get("/export/tables")
async def get_export_tables(
    user: dict = Depends(require_permission)
):
    tables = export_service.get_all_table_names()
    audit_log_writer.write_success(
        user_id=user["user_id"],
        operation_type="获取导出表列表",
        operation_details=f"获取导出表列表，共 {len(tables)} 个表"
    )
    return {
        "code": 200,
        "message": "获取成功",
        "data": {
            "tables": tables,
            "total": len(tables)
        }
    }


@api(
    path="/export/all",
    method="GET",
    name="导出所有数据",
    description="导出数据库所有数据，支持JSON/CSV/Excel格式",
    tags=["系统管理"]
)
@router.get("/export/all")
async def export_all_data(
    format: str = Query(default="json", pattern="^(json|csv|excel)$"),
    user: dict = Depends(require_permission)
):
    audit_log_writer.write_success(
        user_id=user["user_id"],
        operation_type="导出数据",
        operation_details=f"导出所有数据，格式: {format}"
    )

    data = export_service.get_all_data()

    if format == "json":
        content = export_service.export_to_json(data)
        return StreamingResponse(
            iter([content]),
            media_type="application/json",
            headers={
                "Content-Disposition": "attachment; filename=export_all_data.json"
            }
        )

    elif format == "csv":
        csv_data = export_service.export_all_to_csv(data)
        return {
            "code": 200,
            "message": "CSV导出需要指定表名",
            "data": {
                "tables": list(csv_data.keys()),
                "note": "使用 /export/{table_name}?format=csv 导出单个表"
            }
        }

    elif format == "excel":
        content = export_service.export_to_excel(data)
        return StreamingResponse(
            iter([content]),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": "attachment; filename=export_all_data.xlsx"
            }
        )


@api(
    path="/export/{table_name}",
    method="GET",
    name="导出指定表数据",
    description="导出指定表的数据，支持JSON/CSV/Excel格式",
    tags=["系统管理"]
)
@router.get("/export/{table_name}")
async def export_table_data(
    table_name: str,
    format: str = Query(default="json", pattern="^(json|csv|excel)$"),
    user: dict = Depends(require_permission)
):
    available_tables = export_service.get_all_table_names()
    if table_name not in available_tables:
        audit_log_writer.write_failure(
            user_id=user["user_id"],
            operation_type="导出数据",
            operation_details=f"导出表 {table_name} 失败：无效的表名",
            error_msg=f"无效的表名: {table_name}"
        )
        raise HTTPException(status_code=400, detail=f"无效的表名。可用表: {available_tables}")

    data = export_service.get_table_data(table_name)

    audit_log_writer.write_success(
        user_id=user["user_id"],
        operation_type="导出数据",
        operation_details=f"导出表 {table_name}，格式: {format}"
    )

    if format == "json":
        content = export_service.export_to_json({table_name: data})
        return StreamingResponse(
            iter([content]),
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename={table_name}.json"
            }
        )

    elif format == "csv":
        content = export_service.export_table_to_csv(table_name, data)
        return StreamingResponse(
            iter([content]),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={table_name}.csv"
            }
        )

    elif format == "excel":
        content = export_service.export_table_to_excel(table_name, data)
        return StreamingResponse(
            iter([content]),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename={table_name}.xlsx"
            }
        )
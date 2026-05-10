from typing import Optional, List
from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse

from app.core.responses import SuccessResponse, CreatedResponse
from app.core.middlewares import require_permission
from app.core.system_roles import api
from app.schemas.device import (
    DeviceCreateRequest,
    DeviceUpdateRequest,
    DeviceResponse,
    DeviceListResponse,
    DeviceTokenResponse,
    DeviceTokenListResponse,
    BatchTokenGenerateRequest,
    BatchTokenGenerateResponse,
    ProductionLineCreateRequest,
    ProductionLineUpdateRequest,
    ProductionLineResponse,
    ProductionLineListResponse,
    DeviceApprovalRequest,
    DeviceApprovalResponse,
    DeviceApprovalListResponse,
    DeviceStatusHistoryResponse,
    DeviceStatusHistoryListResponse,
)
from app.services.device import (
    device_service,
    production_line_service,
    device_approval_service,
    device_status_history_service,
)
from app.services.audit_log import audit_log_writer
from app.services.message import user_message_service

router = APIRouter()


@api(
    path="/devices",
    method="POST",
    name="创建设备",
    description="创建设备",
    tags=["设备管理"]
)
@router.post("/devices")
async def create_device(
    request: DeviceCreateRequest,
    user: dict = Depends(require_permission)
):
    device = device_service.create_device(
        device_name=request.device_name,
        device_type=request.device_type,
        production_line_id=request.production_line_id,
        device_manager=request.device_manager,
        ip_addr=request.ip_addr,
        mac_addr=request.mac_addr,
        installation_date=request.installation_date
    )
    return CreatedResponse(
        data=DeviceResponse.from_orm(device).model_dump(mode="json"),
        message="设备创建成功"
    )


@api(
    path="/devices",
    method="GET",
    name="获取设备列表",
    description="分页获取设备列表",
    tags=["设备管理"]
)
@router.get("/devices")
async def get_devices(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    status: Optional[str] = Query(default=None),
    user: dict = Depends(require_permission)
):
    devices = device_service.get_all_devices(skip=skip, limit=limit, status=status)
    total = device_service.count_devices(status=status)
    return SuccessResponse(
        data={
            "total": total,
            "devices": [DeviceResponse.from_orm(d).model_dump(mode="json") for d in devices]
        },
        message="获取设备列表成功"
    )


@api(
    path="/devices/tokens/batch-generate",
    method="POST",
    name="批量生成设备Token",
    description="为多个设备批量生成上传Token",
    tags=["设备管理"]
)
@router.post("/devices/tokens/batch-generate")
async def batch_generate_device_tokens(
    request: BatchTokenGenerateRequest,
    user: dict = Depends(require_permission)
):
    results = device_service.batch_generate_upload_tokens(request.device_ids)

    audit_log_writer.write_success(
        user_id=user["user_id"],
        operation_type="批量生成设备Token",
        operation_details=f"批量生成Token：{len(results)} 个设备"
    )

    return SuccessResponse(
        data=BatchTokenGenerateResponse(
            total=len(results),
            success_count=len(results),
            failed_count=0,
            tokens=[DeviceTokenResponse(**d).model_dump(mode="json") for d in results]
        ).model_dump(mode="json"),
        message=f"成功为 {len(results)} 个设备生成Token"
    )


@api(
    path="/devices/tokens/export",
    method="GET",
    name="导出所有设备Token",
    description="导出所有已生成Token的设备信息（JSON格式）",
    tags=["设备管理"]
)
@router.get("/devices/tokens/export")
async def export_all_device_tokens(
    user: dict = Depends(require_permission)
):
    import json

    devices = device_service.get_all_devices_with_tokens()

    audit_log_writer.write_success(
        user_id=user["user_id"],
        operation_type="导出所有设备Token",
        operation_details=f"导出所有设备Token：共 {len(devices)} 个设备"
    )

    content = json.dumps(devices, ensure_ascii=False, indent=2)
    return StreamingResponse(
        iter([content]),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=device_tokens.json"}
    )


@api(
    path="/production-lines",
    method="POST",
    name="创建生产线",
    description="创建生产线",
    tags=["设备管理"]
)
@router.post("/device-production-lines")
async def create_production_line(
    request: ProductionLineCreateRequest,
    user: dict = Depends(require_permission)
):
    line = production_line_service.create_production_line(
        production_line_name=request.line_name,
        production_line_loc=request.line_code,
        production_line_manager=getattr(request, 'line_manager', None)
    )
    return CreatedResponse(
        data=ProductionLineResponse.from_orm(line).model_dump(mode="json"),
        message="生产线创建成功"
    )


@api(
    path="/production-lines",
    method="GET",
    name="获取生产线列表",
    description="分页获取生产线列表",
    tags=["设备管理"]
)
@router.get("/device-production-lines")
async def get_production_lines(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    user: dict = Depends(require_permission)
):
    lines = production_line_service.get_all_production_lines(skip=skip, limit=limit)
    total = production_line_service.count_production_lines()
    return SuccessResponse(
        data={
            "total": total,
            "production_lines": [ProductionLineResponse.from_orm(l).model_dump(mode="json") for l in lines]
        },
        message="获取生产线列表成功"
    )


@api(
    path="/devices/{device_id}",
    method="GET",
    name="获取设备详情",
    description="根据ID获取设备详情",
    tags=["设备管理"]
)
@router.get("/devices/{device_id}")
async def get_device(
    device_id: UUID,
    user: dict = Depends(require_permission)
):
    device = device_service.get_device_by_id(device_id)
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")
    return SuccessResponse(
        data=DeviceResponse.from_orm(device).model_dump(mode="json"),
        message="获取设备成功"
    )


@api(
    path="/devices/{device_id}",
    method="PUT",
    name="更新设备",
    description="更新设备信息",
    tags=["设备管理"]
)
@router.put("/devices/{device_id}")
async def update_device(
    device_id: UUID,
    request: DeviceUpdateRequest,
    user: dict = Depends(require_permission)
):
    old_device = device_service.get_device_by_id(device_id)
    if not old_device:
        raise HTTPException(status_code=404, detail="设备不存在")

    old_status = old_device.status

    device = device_service.update_device(
        device_id,
        device_name=request.device_name,
        device_type=request.device_type,
        production_line_id=request.production_line_id,
        device_manager=request.device_manager,
        ip_addr=request.ip_addr,
        mac_addr=request.mac_addr,
        status=request.status
    )
    if not device:
        audit_log_writer.write_failure(
            user_id=user["user_id"],
            operation_type="更新设备",
            operation_details=f"更新设备失败：设备ID {device_id} 不存在",
            error_msg="设备不存在"
        )
        raise HTTPException(status_code=404, detail="设备不存在")

    if request.status and request.status != old_status and device.device_manager:
        try:
            user_message_service.create_message(
                send_user=user["user_id"],
                receive_user=device.device_manager,
                content=f"您负责的设备 {device.device_name} 状态已变更为：{request.status}。"
            )
        except Exception:
            pass

    audit_log_writer.write_success(
        user_id=user["user_id"],
        operation_type="更新设备",
        operation_details=f"更新设备：设备ID {device_id}"
    )

    return SuccessResponse(
        data=DeviceResponse.from_orm(device).model_dump(mode="json"),
        message="设备更新成功"
    )


@api(
    path="/devices/{device_id}",
    method="DELETE",
    name="删除设备",
    description="删除设备",
    tags=["设备管理"]
)
@router.delete("/devices/{device_id}")
async def delete_device(
    device_id: UUID,
    user: dict = Depends(require_permission)
):
    success = device_service.delete_device(device_id)
    if not success:
        audit_log_writer.write_failure(
            user_id=user["user_id"],
            operation_type="删除设备",
            operation_details=f"删除设备失败：设备ID {device_id} 不存在",
            error_msg="设备不存在"
        )
        raise HTTPException(status_code=404, detail="设备不存在")

    audit_log_writer.write_success(
        user_id=user["user_id"],
        operation_type="删除设备",
        operation_details=f"删除设备：设备ID {device_id}"
    )

    return SuccessResponse(
        data=None,
        message="设备删除成功"
    )


@api(
    path="/devices/{device_id}/token",
    method="POST",
    name="生成设备上传Token",
    description="为指定设备生成上传Token",
    tags=["设备管理"]
)
@router.post("/devices/{device_id}/token")
async def generate_device_token(
    device_id: UUID,
    user: dict = Depends(require_permission)
):
    device = device_service.generate_upload_token(device_id)
    if not device:
        audit_log_writer.write_failure(
            user_id=user["user_id"],
            operation_type="生成设备Token",
            operation_details=f"生成Token失败：设备ID {device_id} 不存在",
            error_msg="设备不存在"
        )
        raise HTTPException(status_code=404, detail="设备不存在")

    audit_log_writer.write_success(
        user_id=user["user_id"],
        operation_type="生成设备Token",
        operation_details=f"生成设备上传Token：设备ID {device_id}"
    )

    return SuccessResponse(
        data=DeviceTokenResponse(
            device_id=device.device_id,
            device_name=device.device_name,
            device_upload_token=device.device_upload_token
        ).model_dump(mode="json"),
        message="Token生成成功"
    )


@api(
    path="/devices/{device_id}/token",
    method="GET",
    name="获取设备上传Token",
    description="获取指定设备的上传Token",
    tags=["设备管理"]
)
@router.get("/devices/{device_id}/token")
async def get_device_token(
    device_id: UUID,
    user: dict = Depends(require_permission)
):
    device = device_service.get_device_with_token(device_id)
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")

    audit_log_writer.write_success(
        user_id=user["user_id"],
        operation_type="获取设备Token",
        operation_details=f"获取设备上传Token：设备ID {device_id}"
    )

    return SuccessResponse(
        data=DeviceTokenResponse(**device).model_dump(mode="json"),
        message="获取成功"
    )


@api(
    path="/devices/{device_id}/token/export",
    method="GET",
    name="导出设备Token",
    description="导出单个设备的Token信息（JSON格式）",
    tags=["设备管理"]
)
@router.get("/devices/{device_id}/token/export")
async def export_device_token(
    device_id: UUID,
    user: dict = Depends(require_permission)
):
    import json

    device = device_service.get_device_with_token(device_id)
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")

    audit_log_writer.write_success(
        user_id=user["user_id"],
        operation_type="导出设备Token",
        operation_details=f"导出设备Token：设备ID {device_id}"
    )

    content = json.dumps(device, ensure_ascii=False, indent=2)
    return StreamingResponse(
        iter([content]),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename=device_token_{device_id}.json"}
    )


@api(
    path="/device-production-lines/search",
    method="GET",
    name="生产线模糊搜索",
    description="按生产线名称或编号模糊搜索",
    tags=["设备管理"]
)
@router.get("/device-production-lines/search")
async def search_production_lines(
    keyword: str = Query(..., min_length=1),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    user: dict = Depends(require_permission)
):
    lines = production_line_service.search_production_lines(keyword, skip=skip, limit=limit)
    total = production_line_service.count_search_production_lines(keyword)
    return SuccessResponse(
        data={
            "total": total,
            "production_lines": [ProductionLineResponse.from_orm(l).model_dump(mode="json") for l in lines]
        },
        message="搜索成功"
    )


@api(
    path="/device-production-lines/{production_line_id}",
    method="GET",
    name="获取生产线详情",
    description="根据ID获取生产线详情",
    tags=["设备管理"]
)
@router.get("/device-production-lines/{production_line_id}")
async def get_production_line(
    production_line_id: UUID,
    user: dict = Depends(require_permission)
):
    line = production_line_service.get_production_line_by_id(production_line_id)
    if not line:
        raise HTTPException(status_code=404, detail="生产线不存在")
    return SuccessResponse(
        data=ProductionLineResponse.from_orm(line).model_dump(mode="json"),
        message="获取生产线成功"
    )


@api(
    path="/device-production-lines/{production_line_id}",
    method="PUT",
    name="更新生产线",
    description="更新生产线信息",
    tags=["设备管理"]
)
@router.put("/device-production-lines/{production_line_id}")
async def update_production_line(
    production_line_id: UUID,
    request: ProductionLineUpdateRequest,
    user: dict = Depends(require_permission)
):
    line = production_line_service.update_production_line(
        production_line_id,
        production_line_name=request.line_name,
        production_line_loc=request.line_code,
        production_line_manager=getattr(request, 'line_manager', None)
    )
    if not line:
        audit_log_writer.write_failure(
            user_id=user["user_id"],
            operation_type="更新生产线",
            operation_details=f"更新生产线失败：生产线ID {production_line_id} 不存在",
            error_msg="生产线不存在"
        )
        raise HTTPException(status_code=404, detail="生产线不存在")

    audit_log_writer.write_success(
        user_id=user["user_id"],
        operation_type="更新生产线",
        operation_details=f"更新生产线：生产线ID {production_line_id}"
    )

    return SuccessResponse(
        data=ProductionLineResponse.from_orm(line).model_dump(mode="json"),
        message="生产线更新成功"
    )


@api(
    path="/device-production-lines/{production_line_id}",
    method="DELETE",
    name="删除生产线",
    description="删除生产线",
    tags=["设备管理"]
)
@router.delete("/device-production-lines/{production_line_id}")
async def delete_production_line(
    production_line_id: UUID,
    user: dict = Depends(require_permission)
):
    success = production_line_service.delete_production_line(production_line_id)
    if not success:
        audit_log_writer.write_failure(
            user_id=user["user_id"],
            operation_type="删除生产线",
            operation_details=f"删除生产线失败：生产线ID {production_line_id} 不存在",
            error_msg="生产线不存在"
        )
        raise HTTPException(status_code=404, detail="生产线不存在")

    audit_log_writer.write_success(
        user_id=user["user_id"],
        operation_type="删除生产线",
        operation_details=f"删除生产线：生产线ID {production_line_id}"
    )

    return SuccessResponse(
        data=None,
        message="生产线删除成功"
    )


@api(
    path="/device-approvals",
    method="POST",
    name="创建设备审批",
    description="创建设备审批记录",
    tags=["设备管理"]
)
@router.post("/device-approvals")
async def create_device_approval(
    request: DeviceApprovalRequest,
    user: dict = Depends(require_permission)
):
    device = device_service.create_device(
        device_name=request.device_name,
        device_type=request.device_type,
        production_line_id=request.production_line_id,
        device_manager=request.device_manager
    )
    
    approval = device_approval_service.create_approval(
        approval_send=user["user_id"],
        approval_by=request.approval_by,
        device_id=device.device_id
    )

    try:
        user_message_service.create_message(
            send_user=user["user_id"],
            receive_user=request.approval_by,
            content=f"您有一条新的设备审批待处理，请及时处理。"
        )
    except Exception as e:
        pass

    return CreatedResponse(
        data=DeviceApprovalResponse.from_orm(approval).model_dump(mode="json"),
        message="审批创建成功"
    )


@api(
    path="/device-approvals",
    method="GET",
    name="获取设备审批列表",
    description="分页获取设备审批列表",
    tags=["设备管理"]
)
@router.get("/device-approvals")
async def get_device_approvals(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    status: Optional[str] = Query(default=None),
    user: dict = Depends(require_permission)
):
    approvals = device_approval_service.get_all_approvals(skip=skip, limit=limit, status=status)
    total = device_approval_service.count_approvals(status=status)
    return SuccessResponse(
        data={
            "total": total,
            "approvals": [DeviceApprovalResponse.from_orm(a).model_dump(mode="json") for a in approvals]
        },
        message="获取审批列表成功"
    )


@api(
    path="/device-approvals/{device_approval_id}",
    method="PUT",
    name="处理设备审批",
    description="审批通过或拒绝",
    tags=["设备管理"]
)
@router.put("/device-approvals/{device_approval_id}")
async def process_device_approval(
    device_approval_id: UUID,
    approved: bool,
    user: dict = Depends(require_permission)
):
    approval = device_approval_service.process_approval(device_approval_id, approved)
    if not approval:
        audit_log_writer.write_failure(
            user_id=user["user_id"],
            operation_type="处理设备审批",
            operation_details=f"处理设备审批失败：审批ID {device_approval_id} 不存在",
            error_msg="审批记录不存在"
        )
        raise HTTPException(status_code=404, detail="审批记录不存在")

    audit_log_writer.write_success(
        user_id=user["user_id"],
        operation_type="处理设备审批",
        operation_details=f"处理设备审批：审批ID {device_approval_id}，结果 {'通过' if approved else '拒绝'}"
    )

    return SuccessResponse(
        data=DeviceApprovalResponse.from_orm(approval).model_dump(mode="json"),
        message="审批处理成功"
    )


@api(
    path="/device-status-history/{device_id}",
    method="GET",
    name="获取设备状态历史",
    description="获取设备状态历史记录",
    tags=["设备管理"]
)
@router.get("/device-status-history/{device_id}")
async def get_device_status_history(
    device_id: UUID,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    user: dict = Depends(require_permission)
):
    histories = device_status_history_service.get_device_history(
        device_id=device_id,
        skip=skip,
        limit=limit
    )
    total = device_status_history_service.count_device_history(device_id)
    return SuccessResponse(
        data={
            "total": total,
            "histories": [DeviceStatusHistoryResponse.from_orm(h).model_dump(mode="json") for h in histories]
        },
        message="获取设备状态历史成功"
    )


@api(
    path="/devices/query/by-production-line/{production_line_id}",
    method="GET",
    name="按生产线查询设备",
    description="根据生产线ID筛选设备列表",
    tags=["设备管理"]
)
@router.get("/devices/query/by-production-line/{production_line_id}")
async def get_devices_by_production_line(
    production_line_id: UUID,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    user: dict = Depends(require_permission)
):
    devices = device_service.get_devices_by_production_line(production_line_id, skip=skip, limit=limit)
    total = device_service.count_devices_by_production_line(production_line_id)
    return SuccessResponse(
        data={
            "total": total,
            "devices": [DeviceResponse.from_orm(d).model_dump(mode="json") for d in devices]
        },
        message="获取生产线设备成功"
    )


@api(
    path="/devices/query/by-type/{device_type}",
    method="GET",
    name="按设备类型查询",
    description="根据设备类型筛选设备列表",
    tags=["设备管理"]
)
@router.get("/devices/query/by-type/{device_type}")
async def get_devices_by_type(
    device_type: str,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    user: dict = Depends(require_permission)
):
    devices = device_service.get_devices_by_type(device_type, skip=skip, limit=limit)
    total = device_service.count_devices_by_type(device_type)
    return SuccessResponse(
        data={
            "total": total,
            "devices": [DeviceResponse.from_orm(d).model_dump(mode="json") for d in devices]
        },
        message="获取设备类型列表成功"
    )


@api(
    path="/devices/list/search",
    method="GET",
    name="设备模糊搜索",
    description="按设备名称模糊搜索设备",
    tags=["设备管理"]
)
@router.get("/devices/list/search")
async def search_devices(
    keyword: str = Query(..., min_length=1),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    user: dict = Depends(require_permission)
):
    devices = device_service.search_devices(keyword, skip=skip, limit=limit)
    total = device_service.count_search_devices(keyword)
    return SuccessResponse(
        data={
            "total": total,
            "devices": [DeviceResponse.from_orm(d).model_dump(mode="json") for d in devices]
        },
        message="搜索成功"
    )


@api(
    path="/devices/query/status-stats",
    method="GET",
    name="设备在线状态统计",
    description="获取设备在线/离线数量统计",
    tags=["设备管理"]
)
@router.get("/devices/query/status-stats")
async def get_device_status_stats(
    user: dict = Depends(require_permission)
):
    stats = device_service.get_device_status_stats()
    return SuccessResponse(
        data=stats,
        message="获取设备状态统计成功"
    )
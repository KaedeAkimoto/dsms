from datetime import datetime
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from app.core.responses import SuccessResponse
from app.core.middlewares import require_permission
from app.core.system_roles import api
from app.services.audit_log import audit_log_service
from app.schemas.audit_log import AuditLogResponse, AuditLogListResponse

router = APIRouter()


@api(
    path="/audit-logs/logs",
    method="GET",
    name="获取审计日志列表",
    description="分页查询审计日志列表",
    tags=["审计日志"]
)
@router.get("/logs")
async def get_audit_logs(
    skip: int = Query(default=0, ge=0, description="跳过记录数"),
    limit: int = Query(default=100, ge=1, le=1000, description="返回记录数"),
    user_id: Optional[UUID] = Query(None, description="按用户ID过滤"),
    operation_type: Optional[str] = Query(None, description="按操作类型过滤"),
    operation_result: Optional[str] = Query(None, description="按操作结果过滤"),
    start_date: Optional[datetime] = Query(None, description="开始时间"),
    end_date: Optional[datetime] = Query(None, description="结束时间"),
    user: dict = Depends(require_permission)
):
    """获取审计日志列表"""
    logs = audit_log_service.get_all(
        skip=skip,
        limit=limit,
        user_id=user_id,
        operation_type=operation_type,
        operation_result=operation_result,
        start_date=start_date,
        end_date=end_date
    )
    total = audit_log_service.count(
        user_id=user_id,
        operation_type=operation_type,
        operation_result=operation_result,
        start_date=start_date,
        end_date=end_date
    )
    return SuccessResponse(
        data=AuditLogListResponse(
            total=total,
            logs=[AuditLogResponse.model_validate(log).model_dump(mode='json') for log in logs]
        ).model_dump(mode='json'),
        message="Audit logs retrieved successfully"
    )


@api(
    path="/audit-logs/logs/{log_id}",
    method="GET",
    name="获取审计日志详情",
    description="根据ID获取单条审计日志",
    tags=["审计日志"]
)
@router.get("/logs/{log_id}")
async def get_audit_log(
    log_id: UUID,
    user: dict = Depends(require_permission)
):
    """获取指定审计日志"""
    log = audit_log_service.get_by_id(log_id)
    if not log:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Audit log not found")
    return SuccessResponse(
        data=AuditLogResponse.model_validate(log).model_dump(mode='json'),
        message="Audit log retrieved successfully"
    )


@api(
    path="/audit-logs/users/{user_id}/logs",
    method="GET",
    name="获取用户审计日志",
    description="获取指定用户的审计日志列表",
    tags=["审计日志"]
)
@router.get("/users/{user_id}/logs")
async def get_user_audit_logs(
    user_id: UUID,
    skip: int = Query(default=0, ge=0, description="跳过记录数"),
    limit: int = Query(default=100, ge=1, le=1000, description="返回记录数"),
    operation_type: Optional[str] = Query(None, description="按操作类型过滤"),
    operation_result: Optional[str] = Query(None, description="按操作结果过滤"),
    start_date: Optional[datetime] = Query(None, description="开始时间"),
    end_date: Optional[datetime] = Query(None, description="结束时间"),
    user: dict = Depends(require_permission)
):
    """获取指定用户的审计日志"""
    logs = audit_log_service.get_by_user(
        user_id=user_id,
        skip=skip,
        limit=limit,
        operation_type=operation_type,
        operation_result=operation_result,
        start_date=start_date,
        end_date=end_date
    )
    total = audit_log_service.count(
        user_id=user_id,
        operation_type=operation_type,
        operation_result=operation_result,
        start_date=start_date,
        end_date=end_date
    )
    return SuccessResponse(
        data=AuditLogListResponse(
            total=total,
            logs=[AuditLogResponse.model_validate(log).model_dump(mode='json') for log in logs]
        ).model_dump(mode='json'),
        message="User audit logs retrieved successfully"
    )

from fastapi import APIRouter
from app.core.responses import SuccessResponse
from app.core.system_roles import api

router = APIRouter()


@api(
    path="/common/health",
    method="GET",
    name="健康检查",
    description="服务健康检查接口",
    tags=["通用"],
    requires_auth=False
)
@router.get("/health")
async def health_check():
    """健康检查接口"""
    return SuccessResponse(
        data={"status": "healthy", "service": "DSMS API"},
        message="Service is running"
    )


@api(
    path="/debug/audit",
    method="GET",
    name="审计日志状态",
    description="调试接口：检查审计日志写入器状态",
    tags=["调试"],
    requires_auth=False
)
@router.get("/debug/audit")
async def debug_audit():
    """调试接口：检查审计日志写入器状态"""
    from app.services.audit_log import audit_log_writer
    return {
        "running": audit_log_writer._running,
        "queue_size": audit_log_writer.queue_size,
        "batch_size": audit_log_writer._batch_size,
        "flush_interval": audit_log_writer._flush_interval
    }


@api(
    path="/common/",
    method="GET",
    name="根路径",
    description="API根路径",
    tags=["通用"],
    requires_auth=False
)
@router.get("/")
async def root():
    """根路径接口"""
    return SuccessResponse(
        data={"message": "Welcome to DSMS API"},
        message="API is ready"
    )

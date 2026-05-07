from fastapi import APIRouter, Depends
from app.core.responses import SuccessResponse
from app.core import require_permission, role_cache
from app.core.system_roles import APIRegistry, api
from app.services.audit_log import audit_log_writer


router = APIRouter()


@api(
    path="/admin/role-cache/refresh",
    method="POST",
    name="刷新角色缓存",
    description="刷新角色权限缓存",
    tags=["系统管理"]
)
@router.post("/role-cache/refresh")
async def refresh_role_cache(user: dict = Depends(require_permission)):
    """刷新角色权限缓存

    当角色或权限数据被修改后，调用此接口刷新缓存
    """
    role_cache.reload()
    audit_log_writer.write_success(
        user_id=user["user_id"],
        operation_type="刷新角色缓存",
        operation_details=f"刷新角色缓存"
    )
    return SuccessResponse(
        data={
            "roles_count": role_cache.roles_count,
            "user_roles_count": role_cache.user_roles_count
        },
        message="Role cache refreshed successfully"
    )


@api(
    path="/admin/apis",
    method="GET",
    name="获取所有API列表",
    description="获取所有注册的API列表, 供前端使用",
    tags=["系统管理"]
)
@router.get("/apis")
async def get_all_apis(user: dict = Depends(require_permission)):
    """获取所有注册的 API 列表

    供前端使用，用于动态生成菜单和权限控制
    """
    apis = APIRegistry.get_all_apis()
    tags = APIRegistry.get_all_tags()
    return SuccessResponse(
        data={
            "apis": apis,
            "tags": tags
        },
        message="APIs retrieved successfully"
    )

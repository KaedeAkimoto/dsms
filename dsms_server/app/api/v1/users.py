from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends, Query

from app.core.responses import SuccessResponse
from app.core.middlewares import require_permission
from app.core.system_roles import api
from app.schemas.user import (
    UserResponse,
    UserUpdateRequest,
    PasswordChangeRequest,
    UserListResponse,
    BatchUserRegisterRequest,
    BatchUserRegisterResponse
)
from app.services.user import user_service
from app.services.audit_log import audit_log_writer
from app.services.message import system_message_service

router = APIRouter()


@api(
    path="/users/me",
    method="GET",
    name="获取当前用户",
    description="获取当前登录用户信息",
    tags=["用户管理"]
)
@router.get("/users/me")
async def get_current_user_endpoint(user=Depends(require_permission)):
    """获取当前登录用户信息"""
    user_info = user_service.get_user_by_id(user["user_id"])
    if not user_info:
        raise HTTPException(status_code=404, detail="用户不存在")

    return SuccessResponse(
        data=UserResponse.from_orm(user_info).model_dump(mode="json"),
        message="获取用户成功"
    )


@api(
    path="/users/me",
    method="PUT",
    name="更新当前用户",
    description="更新当前用户信息（不含角色）",
    tags=["用户管理"]
)
@router.put("/users/me")
async def update_current_user_endpoint(
    request: UserUpdateRequest,
    user=Depends(require_permission)
):
    """更新当前用户信息（仅个人信息，不含角色）"""
    updated_user = user_service.update_user(
        user_id=user["user_id"],
        real_name=request.real_name,
        email=request.email,
        phone=request.phone,
        department_id=request.department_id,
        title_id=request.title_id,
        avatar_url=request.avatar_url
    )

    if not updated_user:
        audit_log_writer.write_failure(
            user_id=user["user_id"],
            operation_type="更新个人信息",
            operation_details="更新个人信息失败：用户不存在",
            error_msg="用户不存在"
        )
        raise HTTPException(status_code=404, detail="用户不存在")

    audit_log_writer.write_success(
        user_id=user["user_id"],
        operation_type="更新个人信息",
        operation_details="更新当前用户个人信息"
    )

    return SuccessResponse(
        data=UserResponse.from_orm(updated_user).model_dump(mode="json"),
        message="用户信息更新成功"
    )


@api(
    path="/users/me/password",
    method="PUT",
    name="修改密码",
    description="修改当前用户密码",
    tags=["用户管理"]
)
@router.put("/users/me/password")
async def change_password_endpoint(
    request: PasswordChangeRequest,
    user=Depends(require_permission)
):
    """修改当前用户密码"""
    success = user_service.change_password(
        user_id=user["user_id"],
        old_password=request.old_password,
        new_password=request.new_password
    )

    if not success:
        audit_log_writer.write_failure(
            user_id=user["user_id"],
            operation_type="修改密码",
            operation_details="修改密码失败：旧密码错误",
            error_msg="旧密码错误"
        )
        raise HTTPException(status_code=400, detail="旧密码错误")

    audit_log_writer.write_success(
        user_id=user["user_id"],
        operation_type="修改密码",
        operation_details="成功修改用户密码"
    )

    return SuccessResponse(
        data=None,
        message="密码修改成功"
    )


@api(
    path="/users/batch",
    method="POST",
    name="批量添加用户",
    description="批量添加用户（管理员）",
    tags=["用户管理"]
)
@router.post("/users/batch")
async def batch_create_users_endpoint(
    request: BatchUserRegisterRequest,
    user=Depends(require_permission)
):
    """批量添加用户（管理员权限）"""
    # 将 Pydantic 模型转换为字典列表
    users_data = [
        {
            'user_name': u.user_name,
            'password': u.password,
            'real_name': u.real_name,
            'email': u.email,
            'phone': u.phone,
            'employee_id': u.employee_id,
            'department_id': u.department_id,
            'title_id': u.title_id
        }
        for u in request.users
    ]

    try:
        result = user_service.batch_create_users(
            users_data=users_data,
            default_role_id=request.default_role_id
        )
    except ValueError as e:
        raise BadRequestException(message=str(e))

    # 写入审计日志
    success_users = [u.user_name for u in result['success_users']]
    failed_users = [f['user_name'] for f in result['failed_users']]
    audit_log_writer.write_success(
        user_id=user["user_id"],
        operation_type="批量添加用户",
        operation_details=f"批量创建用户：成功 {result['success_count']} 人（{','.join(success_users)}），失败 {result['failed_count']} 人（{','.join(failed_users)}）"
    )

    response = BatchUserRegisterResponse(
        success_count=result['success_count'],
        failed_count=result['failed_count'],
        success_users=[UserResponse.from_orm(u).model_dump(mode="json") for u in result['success_users']],
        failed_users=result['failed_users']
    )

    message = f"批量创建完成：成功 {result['success_count']} 人，失败 {result['failed_count']} 人"

    return SuccessResponse(
        data=response.model_dump(mode='json'),
        message=message
    )


@api(
    path="/users",
    method="GET",
    name="获取用户列表",
    description="分页获取用户列表（管理员）",
    tags=["用户管理"]
)
@router.get("/users")
async def get_users_endpoint(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    user=Depends(require_permission)
):
    """获取用户列表（管理员权限）"""
    users = user_service.get_all_users(skip=skip, limit=limit)
    total = user_service.count_users()

    return SuccessResponse(
        data=UserListResponse(
            total=total,
            users=[UserResponse.from_orm(u) for u in users]
        ).model_dump(mode='json'),
        message="获取用户列表成功"
    )


@api(
    path="/users/by-department/{department_id}",
    method="GET",
    name="按部门查询用户",
    description="根据部门ID筛选用户列表",
    tags=["用户管理"]
)
@router.get("/users/by-department/{department_id}")
async def get_users_by_department_endpoint(
    department_id: int,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    user=Depends(require_permission)
):
    """根据部门ID筛选用户列表"""
    users = user_service.get_users_by_department(department_id, skip=skip, limit=limit)
    total = user_service.count_users_by_department(department_id)

    return SuccessResponse(
        data=UserListResponse(
            total=total,
            users=[UserResponse.from_orm(u) for u in users]
        ).model_dump(mode='json'),
        message="获取部门用户成功"
    )


@api(
    path="/users/by-title/{title_id}",
    method="GET",
    name="按职称查询用户",
    description="根据职称ID筛选用户列表",
    tags=["用户管理"]
)
@router.get("/users/by-title/{title_id}")
async def get_users_by_title_endpoint(
    title_id: int,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    user=Depends(require_permission)
):
    """根据职称ID筛选用户列表"""
    users = user_service.get_users_by_title(title_id, skip=skip, limit=limit)
    total = user_service.count_users_by_title(title_id)

    return SuccessResponse(
        data=UserListResponse(
            total=total,
            users=[UserResponse.from_orm(u) for u in users]
        ).model_dump(mode='json'),
        message="获取职称用户成功"
    )


@api(
    path="/users/by-role/{role_id}",
    method="GET",
    name="按角色查询用户",
    description="根据角色ID筛选用户列表",
    tags=["用户管理"]
)
@router.get("/users/by-role/{role_id}")
async def get_users_by_role_endpoint(
    role_id: int,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    user=Depends(require_permission)
):
    """根据角色ID筛选用户列表"""
    users = user_service.get_users_by_role(role_id, skip=skip, limit=limit)
    total = user_service.count_users_by_role(role_id)

    return SuccessResponse(
        data=UserListResponse(
            total=total,
            users=[UserResponse.from_orm(u) for u in users]
        ).model_dump(mode='json'),
        message="获取角色用户成功"
    )


@api(
    path="/users/search",
    method="GET",
    name="用户模糊搜索",
    description="按用户名/姓名/工号模糊搜索用户",
    tags=["用户管理"]
)
@router.get("/users/search")
async def search_users_endpoint(
    keyword: str = Query(..., min_length=1),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    user=Depends(require_permission)
):
    """按用户名/姓名/工号模糊搜索用户"""
    users = user_service.search_users(keyword, skip=skip, limit=limit)
    total = user_service.count_search_users(keyword)

    return SuccessResponse(
        data=UserListResponse(
            total=total,
            users=[UserResponse.from_orm(u) for u in users]
        ).model_dump(mode='json'),
        message="搜索成功"
    )


@api(
    path="/users/{user_id}",
    method="GET",
    name="获取用户详情",
    description="获取指定用户详情",
    tags=["用户管理"]
)
@router.get("/users/{user_id}")
async def get_user_endpoint(
    user_id: UUID,
    user=Depends(require_permission)
):
    """获取用户详情"""
    user_info = user_service.get_user_by_id(user_id)
    if not user_info:
        raise HTTPException(status_code=404, detail="用户不存在")

    return SuccessResponse(
        data=UserResponse.from_orm(user_info).model_dump(mode="json"),
        message="获取用户成功"
    )


@api(
    path="/users/{user_id}",
    method="PUT",
    name="更新用户信息",
    description="更新用户信息（管理员）",
    tags=["用户管理"]
)
@router.put("/users/{user_id}")
async def update_user_endpoint(
    user_id: UUID,
    request: UserUpdateRequest,
    user=Depends(require_permission)
):
    """更新用户信息（管理员权限）"""
    updated_user = user_service.update_user(
        user_id=user_id,
        real_name=request.real_name,
        email=request.email,
        phone=request.phone,
        department_id=request.department_id,
        title_id=request.title_id,
        role_id=request.role_id,
        avatar_url=request.avatar_url
    )

    if not updated_user:
        audit_log_writer.write_failure(
            user_id=user["user_id"],
            operation_type="更新用户信息",
            operation_details=f"更新用户信息失败：用户ID {user_id} 不存在",
            error_msg="用户不存在"
        )
        raise HTTPException(status_code=404, detail="用户不存在")

    audit_log_writer.write_success(
        user_id=user["user_id"],
        operation_type="更新用户信息",
        operation_details=f"更新用户信息：用户ID {user_id}"
    )

    return SuccessResponse(
        data=UserResponse.from_orm(updated_user).model_dump(mode="json"),
        message="用户信息更新成功"
    )


@api(
    path="/users/{user_id}/password",
    method="PUT",
    name="重置密码",
    description="重置用户密码（管理员）",
    tags=["用户管理"]
)
@router.put("/users/{user_id}/password")
async def reset_password_endpoint(
    user_id: UUID,
    new_password: str = Query(..., min_length=8, max_length=128),
    user=Depends(require_permission)
):
    """重置用户密码（管理员权限）"""
    from app.config.database import db_config
    from sqlmodel import select
    from app.models import User

    with db_config.get_session() as session:
        result = session.execute(
            select(User).where(User.user_id == user_id)
        )
        user_info = result.scalars().first()

        if not user_info:
            audit_log_writer.write_failure(
                user_id=user["user_id"],
                operation_type="重置密码",
                operation_details=f"重置密码失败：用户ID {user_id} 不存在",
                error_msg="用户不存在"
            )
            raise HTTPException(status_code=404, detail="用户不存在")

        user_info.password_hash = user_service.hash_password(new_password)
        session.commit()

        try:
            system_message_service.create_message(
                receive_user=user_id,
                content=f"您的密码已被管理员重置，请使用新密码登录。如有疑问请联系管理员。"
            )
        except Exception:
            pass

    audit_log_writer.write_success(
        user_id=user["user_id"],
        operation_type="重置密码",
        operation_details=f"重置用户密码：用户ID {user_id}"
    )

    return SuccessResponse(
        data=None,
        message="密码重置成功"
    )


@api(
    path="/users/{user_id}",
    method="DELETE",
    name="删除用户",
    description="删除用户（管理员）",
    tags=["用户管理"]
)
@router.delete("/users/{user_id}")
async def delete_user_endpoint(
    user_id: UUID,
    user=Depends(require_permission)
):
    """删除用户（管理员权限）"""
    success = user_service.delete_user(user_id)
    if not success:
        audit_log_writer.write_failure(
            user_id=user["user_id"],
            operation_type="删除用户",
            operation_details=f"删除用户失败：用户ID {user_id} 不存在",
            error_msg="用户不存在"
        )
        raise HTTPException(status_code=404, detail="用户不存在")

    audit_log_writer.write_success(
        user_id=user["user_id"],
        operation_type="删除用户",
        operation_details=f"删除用户：用户ID {user_id}"
    )

    return SuccessResponse(
        data=None,
        message="用户已离职（角色已更新为无权限用户）"
    )

from typing import Optional, List, Dict
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from sqlmodel import select, update, delete

from app.core.responses import SuccessResponse, CreatedResponse
from app.core.middlewares import require_permission
from app.core.system_roles import api
from app.core.role_cache import role_cache
from app.config.database import db_config
from app.models import Role
from app.services.audit_log import audit_log_writer

router = APIRouter()


class RoleCreateRequest(BaseModel):
    """创建角色请求"""
    role_name: str
    desc: Optional[str] = None
    permissions: Optional[List[Dict[str, str]]] = None


class RoleUpdateRequest(BaseModel):
    """更新角色请求"""
    role_name: Optional[str] = None
    desc: Optional[str] = None
    permissions: Optional[List[Dict[str, str]]] = None


@api(
    path="/roles",
    method="GET",
    name="获取角色列表",
    description="获取所有角色列表",
    tags=["角色管理"]
)
@router.get("/roles")
async def get_roles(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    user=Depends(require_permission)
):
    """获取角色列表"""
    with db_config.get_session() as session:
        result = session.execute(
            select(Role)
            .order_by(Role.role_id)
            .offset(skip)
            .limit(limit)
        )
        roles = result.scalars().all()
        
        result_count = session.execute(select(Role))
        total = len(result_count.scalars().all())

    return SuccessResponse(
        data={
            "total": total,
            "roles": [
                {
                    "role_id": r.role_id,
                    "role_name": r.role_name,
                    "desc": r.desc,
                    "is_system_role": r.is_system_role,
                    "permissions": r.permissions,
                    "created_at": r.created_at.isoformat() if r.created_at else None
                }
                for r in roles
            ]
        },
        message="获取角色列表成功"
    )


@api(
    path="/roles/{role_id}",
    method="GET",
    name="获取角色详情",
    description="根据ID获取角色详情",
    tags=["角色管理"]
)
@router.get("/roles/{role_id}")
async def get_role(
    role_id: int,
    user=Depends(require_permission)
):
    """获取角色详情"""
    with db_config.get_session() as session:
        result = session.execute(
            select(Role).where(Role.role_id == role_id)
        )
        role = result.scalars().first()

    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")

    return SuccessResponse(
        data={
            "role_id": role.role_id,
            "role_name": role.role_name,
            "desc": role.desc,
            "is_system_role": role.is_system_role,
            "permissions": role.permissions,
            "created_at": role.created_at.isoformat() if role.created_at else None
        },
        message="获取角色成功"
    )


@api(
    path="/roles",
    method="POST",
    name="创建角色",
    description="创建新角色",
    tags=["角色管理"]
)
@router.post("/roles")
async def create_role(
    request: RoleCreateRequest,
    user=Depends(require_permission)
):
    """创建角色"""
    # 检查角色名称是否已存在
    with db_config.get_session() as session:
        existing_role = session.execute(
            select(Role).where(Role.role_name == request.role_name)
        ).scalars().first()
        
        if existing_role:
            audit_log_writer.write_failure(
                user_id=user["user_id"],
                operation_type="创建角色",
                operation_details=f"创建角色失败：角色名称 '{request.role_name}' 已存在",
                error_msg="角色名称已存在"
            )
            raise HTTPException(status_code=400, detail="角色名称已存在")

        role = Role(
            role_name=request.role_name,
            desc=request.desc,
            is_system_role=False,
            permissions=request.permissions if request.permissions else []
        )
        session.add(role)
        session.commit()
        session.refresh(role)

    # 记录审计日志
    audit_log_writer.write_success(
        user_id=user["user_id"],
        operation_type="创建角色",
        operation_details=f"创建角色：角色ID {role.role_id}，角色名称 {role.role_name}"
    )

    # 更新角色缓存
    role_cache.reload()

    return CreatedResponse(
        data={
            "role_id": role.role_id,
            "role_name": role.role_name,
            "desc": role.desc,
            "is_system_role": role.is_system_role,
            "permissions": role.permissions,
            "created_at": role.created_at.isoformat() if role.created_at else None
        },
        message="角色创建成功"
    )


@api(
    path="/roles/{role_id}",
    method="PUT",
    name="更新角色",
    description="更新角色信息",
    tags=["角色管理"]
)
@router.put("/roles/{role_id}")
async def update_role(
    role_id: int,
    request: RoleUpdateRequest,
    user=Depends(require_permission)
):
    """更新角色"""
    with db_config.get_session() as session:
        result = session.execute(
            select(Role).where(Role.role_id == role_id)
        )
        role = result.scalars().first()

        if not role:
            audit_log_writer.write_failure(
                user_id=user["user_id"],
                operation_type="更新角色",
                operation_details=f"更新角色失败：角色ID {role_id} 不存在",
                error_msg="角色不存在"
            )
            raise HTTPException(status_code=404, detail="角色不存在")

        if role.is_system_role:
            audit_log_writer.write_failure(
                user_id=user["user_id"],
                operation_type="更新角色",
                operation_details=f"更新角色失败：角色ID {role_id} 是系统角色，不允许修改",
                error_msg="系统角色不允许修改"
            )
            raise HTTPException(status_code=400, detail="系统角色不允许修改")

        # 检查新角色名称是否与其他角色冲突
        if request.role_name and request.role_name != role.role_name:
            existing_role = session.execute(
                select(Role).where(Role.role_name == request.role_name)
            ).scalars().first()
            if existing_role:
                audit_log_writer.write_failure(
                    user_id=user["user_id"],
                    operation_type="更新角色",
                    operation_details=f"更新角色失败：角色名称 '{request.role_name}' 已存在",
                    error_msg="角色名称已存在"
                )
                raise HTTPException(status_code=400, detail="角色名称已存在")
            role.role_name = request.role_name

        if request.desc is not None:
            role.desc = request.desc
        
        if request.permissions is not None:
            role.permissions = request.permissions

        session.commit()
        session.refresh(role)

    # 记录审计日志
    audit_log_writer.write_success(
        user_id=user["user_id"],
        operation_type="更新角色",
        operation_details=f"更新角色：角色ID {role.role_id}，角色名称 {role.role_name}"
    )

    # 更新角色缓存
    role_cache.reload()

    return SuccessResponse(
        data={
            "role_id": role.role_id,
            "role_name": role.role_name,
            "desc": role.desc,
            "is_system_role": role.is_system_role,
            "permissions": role.permissions,
            "created_at": role.created_at.isoformat() if role.created_at else None
        },
        message="角色更新成功"
    )


@api(
    path="/roles/{role_id}",
    method="DELETE",
    name="删除角色",
    description="删除角色",
    tags=["角色管理"]
)
@router.delete("/roles/{role_id}")
async def delete_role(
    role_id: int,
    user=Depends(require_permission)
):
    """删除角色"""
    with db_config.get_session() as session:
        result = session.execute(
            select(Role).where(Role.role_id == role_id)
        )
        role = result.scalars().first()

        if not role:
            audit_log_writer.write_failure(
                user_id=user["user_id"],
                operation_type="删除角色",
                operation_details=f"删除角色失败：角色ID {role_id} 不存在",
                error_msg="角色不存在"
            )
            raise HTTPException(status_code=404, detail="角色不存在")

        if role.is_system_role:
            audit_log_writer.write_failure(
                user_id=user["user_id"],
                operation_type="删除角色",
                operation_details=f"删除角色失败：角色ID {role_id} 是系统角色，不允许删除",
                error_msg="系统角色不允许删除"
            )
            raise HTTPException(status_code=400, detail="系统角色不允许删除")

        # 检查是否有用户使用该角色
        from app.models import User
        user_results = session.execute(
            select(User).where(User.role_id == role_id)
        ).scalars()
        user_count = len(list(user_results))
        
        if user_count > 0:
            audit_log_writer.write_failure(
                user_id=user["user_id"],
                operation_type="删除角色",
                operation_details=f"删除角色失败：角色ID {role_id} 仍有 {user_count} 个用户使用",
                error_msg="该角色仍有用户使用，无法删除"
            )
            raise HTTPException(status_code=400, detail="该角色仍有用户使用，无法删除")

        session.delete(role)
        session.commit()

    # 记录审计日志
    audit_log_writer.write_success(
        user_id=user["user_id"],
        operation_type="删除角色",
        operation_details=f"删除角色：角色ID {role_id}，角色名称 {role.role_name}"
    )

    # 更新角色缓存
    role_cache.reload()

    return SuccessResponse(
        data=None,
        message="角色删除成功"
    )
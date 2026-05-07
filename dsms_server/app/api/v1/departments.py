from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from sqlmodel import select
from sqlalchemy import func

from app.core.responses import SuccessResponse, CreatedResponse
from app.core.middlewares import require_permission
from app.core.system_roles import api
from app.config.database import db_config
from app.models import Department
from app.services.audit_log import audit_log_writer

router = APIRouter()


class DepartmentCreateRequest(BaseModel):
    """创建部门请求"""
    department_code: str
    department_name: str
    parent_id: Optional[int] = None


class DepartmentUpdateRequest(BaseModel):
    """更新部门请求"""
    department_code: Optional[str] = None
    department_name: Optional[str] = None
    parent_id: Optional[int] = None


@api(
    path="/departments",
    method="GET",
    name="获取部门列表",
    description="获取所有部门列表",
    tags=["部门管理"]
)
@router.get("/departments")
async def get_departments(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    user=Depends(require_permission)
):
    """获取部门列表"""
    with db_config.get_session() as session:
        result = session.execute(
            select(Department)
            .order_by(Department.department_id)
            .offset(skip)
            .limit(limit)
        )
        departments = result.scalars().all()
        
        result_count = session.execute(select(Department))
        total = len(result_count.scalars().all())

    return SuccessResponse(
        data={
            "total": total,
            "departments": [
                {
                    "department_id": d.department_id,
                    "department_code": d.department_code,
                    "department_name": d.department_name,
                    "parent_id": d.parent_id,
                    "created_at": d.created_at.isoformat() if d.created_at else None
                }
                for d in departments
            ]
        },
        message="获取部门列表成功"
    )


@api(
    path="/departments/search",
    method="GET",
    name="部门模糊搜索",
    description="按部门名称或编号模糊搜索",
    tags=["部门管理"]
)
@router.get("/departments/search")
async def search_departments(
    keyword: str = Query(..., min_length=1),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    user=Depends(require_permission)
):
    """按部门名称或编号模糊搜索"""
    from sqlalchemy import or_
    with db_config.get_session() as session:
        query = (
            select(Department)
            .where(
                or_(
                    Department.department_name.ilike(f"%{keyword}%"),
                    Department.department_code.ilike(f"%{keyword}%")
                )
            )
            .order_by(Department.department_id)
            .offset(skip)
            .limit(limit)
        )
        result = session.execute(query)
        departments = result.scalars().all()

        count_query = (
            select(Department)
            .where(
                or_(
                    Department.department_name.ilike(f"%{keyword}%"),
                    Department.department_code.ilike(f"%{keyword}%")
                )
            )
        )
        count_result = session.execute(count_query)
        total = len(count_result.scalars().all())

    return SuccessResponse(
        data={
            "total": total,
            "departments": [
                {
                    "department_id": d.department_id,
                    "department_code": d.department_code,
                    "department_name": d.department_name,
                    "parent_id": d.parent_id,
                    "created_at": d.created_at.isoformat() if d.created_at else None
                }
                for d in departments
            ]
        },
        message="搜索成功"
    )


@api(
    path="/departments/{department_id}",
    method="GET",
    name="获取部门详情",
    description="根据ID获取部门详情",
    tags=["部门管理"]
)
@router.get("/departments/{department_id}")
async def get_department(
    department_id: int,
    user=Depends(require_permission)
):
    """获取部门详情"""
    with db_config.get_session() as session:
        result = session.execute(
            select(Department).where(Department.department_id == department_id)
        )
        department = result.scalars().first()

    if not department:
        raise HTTPException(status_code=404, detail="部门不存在")

    return SuccessResponse(
        data={
            "department_id": department.department_id,
            "department_code": department.department_code,
            "department_name": department.department_name,
            "parent_id": department.parent_id,
            "created_at": department.created_at.isoformat() if department.created_at else None
        },
        message="获取部门成功"
    )


@api(
    path="/departments",
    method="POST",
    name="创建部门",
    description="创建新部门",
    tags=["部门管理"]
)
@router.post("/departments")
async def create_department(
    request: DepartmentCreateRequest,
    user=Depends(require_permission)
):
    """创建部门"""
    # 检查部门编码是否已存在
    with db_config.get_session() as session:
        existing_department = session.execute(
            select(Department).where(Department.department_code == request.department_code)
        ).scalars().first()
        
        if existing_department:
            raise HTTPException(status_code=400, detail="部门编码已存在")
        
        # 检查上级部门是否存在
        if request.parent_id is not None:
            parent = session.execute(
                select(Department).where(Department.department_id == request.parent_id)
            ).scalars().first()
            if not parent:
                raise HTTPException(status_code=404, detail="上级部门不存在")

        department = Department(
            department_code=request.department_code,
            department_name=request.department_name,
            parent_id=request.parent_id
        )
        session.add(department)
        session.commit()
        session.refresh(department)

    # 记录审计日志（仅成功）
    audit_log_writer.write_success(
        user_id=user["user_id"],
        operation_type="创建部门",
        operation_details=f"创建部门：部门ID {department.department_id}，部门名称 {department.department_name}"
    )

    return CreatedResponse(
        data={
            "department_id": department.department_id,
            "department_code": department.department_code,
            "department_name": department.department_name,
            "parent_id": department.parent_id,
            "created_at": department.created_at.isoformat() if department.created_at else None
        },
        message="部门创建成功"
    )


@api(
    path="/departments/{department_id}",
    method="PUT",
    name="更新部门",
    description="更新部门信息",
    tags=["部门管理"]
)
@router.put("/departments/{department_id}")
async def update_department(
    department_id: int,
    request: DepartmentUpdateRequest,
    user=Depends(require_permission)
):
    """更新部门"""
    with db_config.get_session() as session:
        result = session.execute(
            select(Department).where(Department.department_id == department_id)
        )
        department = result.scalars().first()

        if not department:
            raise HTTPException(status_code=404, detail="部门不存在")

        # 检查新部门编码是否与其他部门冲突
        if request.department_code and request.department_code != department.department_code:
            existing_department = session.execute(
                select(Department).where(Department.department_code == request.department_code)
            ).scalars().first()
            if existing_department:
                raise HTTPException(status_code=400, detail="部门编码已存在")
            department.department_code = request.department_code

        if request.department_name is not None:
            department.department_name = request.department_name
        
        if request.parent_id is not None:
            # 检查上级部门是否存在
            if request.parent_id is not None:
                parent = session.execute(
                    select(Department).where(Department.department_id == request.parent_id)
                ).scalars().first()
                if not parent:
                    raise HTTPException(status_code=404, detail="上级部门不存在")
            # 检查是否设置自己为上级
            if request.parent_id == department_id:
                raise HTTPException(status_code=400, detail="不能设置自己为上级部门")
            department.parent_id = request.parent_id

        session.commit()
        session.refresh(department)

    # 记录审计日志（仅成功）
    audit_log_writer.write_success(
        user_id=user["user_id"],
        operation_type="更新部门",
        operation_details=f"更新部门：部门ID {department.department_id}，部门名称 {department.department_name}"
    )

    return SuccessResponse(
        data={
            "department_id": department.department_id,
            "department_code": department.department_code,
            "department_name": department.department_name,
            "parent_id": department.parent_id,
            "created_at": department.created_at.isoformat() if department.created_at else None
        },
        message="部门更新成功"
    )


@api(
    path="/departments/{department_id}",
    method="DELETE",
    name="删除部门",
    description="删除部门（同时将关联用户的部门设为NULL）",
    tags=["部门管理"]
)
@router.delete("/departments/{department_id}")
async def delete_department(
    department_id: int,
    user=Depends(require_permission)
):
    """删除部门"""
    with db_config.get_session() as session:
        result = session.execute(
            select(Department).where(Department.department_id == department_id)
        )
        department = result.scalars().first()

        if not department:
            raise HTTPException(status_code=404, detail="部门不存在")

        child_count = session.execute(
            select(func.count()).select_from(Department).where(Department.parent_id == department_id)
        ).scalar()

        if child_count > 0:
            raise HTTPException(status_code=400, detail="该部门仍有下级部门，无法删除")

        from app.models import User
        from sqlalchemy import update

        update_query = (
            update(User)
            .where(User.department_id == department_id)
            .values(department_id=None)
        )
        session.execute(update_query)

        session.delete(department)
        session.commit()

    # 记录审计日志（仅成功）
    audit_log_writer.write_success(
        user_id=user["user_id"],
        operation_type="删除部门",
        operation_details=f"删除部门：部门ID {department_id}，部门名称 {department.department_name}"
    )

    return SuccessResponse(
        data=None,
        message="部门删除成功"
    )


@api(
    path="/departments/list/tree",
    method="GET",
    name="获取部门树形结构",
    description="获取部门的树形结构列表",
    tags=["部门管理"]
)
@router.get("/departments/list/tree")
async def get_department_tree(user=Depends(require_permission)):
    """获取部门树形结构"""
    with db_config.get_session() as session:
        result = session.execute(select(Department).order_by(Department.department_id))
        departments = result.scalars().all()

    def build_tree(parent_id: Optional[int] = None):
        children = []
        for dept in departments:
            if dept.parent_id == parent_id:
                child = {
                    "department_id": dept.department_id,
                    "department_code": dept.department_code,
                    "department_name": dept.department_name,
                    "parent_id": dept.parent_id,
                    "created_at": dept.created_at.isoformat() if dept.created_at else None,
                    "children": build_tree(dept.department_id)
                }
                children.append(child)
        return children

    tree = build_tree(None)

    return SuccessResponse(
        data=tree,
        message="获取部门树形结构成功"
    )


@api(
    path="/departments/query/children/{department_id}",
    method="GET",
    name="获取子部门列表",
    description="获取指定部门的所有子部门",
    tags=["部门管理"]
)
@router.get("/departments/query/children/{department_id}")
async def get_department_children(
    department_id: int,
    user=Depends(require_permission)
):
    """获取指定部门的子部门列表"""
    with db_config.get_session() as session:
        result = session.execute(
            select(Department).where(Department.parent_id == department_id)
        )
        children = result.scalars().all()

    return SuccessResponse(
        data=[
            {
                "department_id": d.department_id,
                "department_code": d.department_code,
                "department_name": d.department_name,
                "parent_id": d.parent_id,
                "created_at": d.created_at.isoformat() if d.created_at else None
            }
            for d in children
        ],
        message="获取子部门列表成功"
    )
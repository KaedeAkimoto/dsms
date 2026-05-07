from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from sqlmodel import select
from sqlalchemy import func

from app.core.responses import SuccessResponse, CreatedResponse
from app.core.middlewares import require_permission
from app.core.system_roles import api
from app.config.database import db_config
from app.models import Title
from app.services.audit_log import audit_log_writer

router = APIRouter()


class TitleCreateRequest(BaseModel):
    """创建职称请求"""
    title_name: str


class TitleUpdateRequest(BaseModel):
    """更新职称请求"""
    title_name: Optional[str] = None


@api(
    path="/titles",
    method="GET",
    name="获取职称列表",
    description="获取所有职称列表",
    tags=["职称管理"]
)
@router.get("/titles")
async def get_titles(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    user=Depends(require_permission)
):
    """获取职称列表"""
    with db_config.get_session() as session:
        result = session.execute(
            select(Title)
            .order_by(Title.title_id)
            .offset(skip)
            .limit(limit)
        )
        titles = result.scalars().all()
        
        result_count = session.execute(select(Title))
        total = len(result_count.scalars().all())

    return SuccessResponse(
        data={
            "total": total,
            "titles": [
                {
                    "title_id": t.title_id,
                    "title_name": t.title_name
                }
                for t in titles
            ]
        },
        message="获取职称列表成功"
    )


@api(
    path="/titles/{title_id}",
    method="GET",
    name="获取职称详情",
    description="根据ID获取职称详情",
    tags=["职称管理"]
)
@router.get("/titles/{title_id}")
async def get_title(
    title_id: int,
    user=Depends(require_permission)
):
    """获取职称详情"""
    with db_config.get_session() as session:
        result = session.execute(
            select(Title).where(Title.title_id == title_id)
        )
        title = result.scalars().first()

    if not title:
        raise HTTPException(status_code=404, detail="职称不存在")

    return SuccessResponse(
        data={
            "title_id": title.title_id,
            "title_name": title.title_name
        },
        message="获取职称成功"
    )


@api(
    path="/titles",
    method="POST",
    name="创建职称",
    description="创建新职称",
    tags=["职称管理"]
)
@router.post("/titles")
async def create_title(
    request: TitleCreateRequest,
    user=Depends(require_permission)
):
    """创建职称"""
    # 检查职称名称是否已存在
    with db_config.get_session() as session:
        existing_title = session.execute(
            select(Title).where(Title.title_name == request.title_name)
        ).scalars().first()
        
        if existing_title:
            raise HTTPException(status_code=400, detail="职称名称已存在")

        title = Title(
            title_name=request.title_name
        )
        session.add(title)
        session.commit()
        session.refresh(title)

    # 记录审计日志（仅成功）
    audit_log_writer.write_success(
        user_id=user["user_id"],
        operation_type="创建职称",
        operation_details=f"创建职称：职称ID {title.title_id}，职称名称 {title.title_name}"
    )

    return CreatedResponse(
        data={
            "title_id": title.title_id,
            "title_name": title.title_name
        },
        message="职称创建成功"
    )


@api(
    path="/titles/{title_id}",
    method="PUT",
    name="更新职称",
    description="更新职称信息",
    tags=["职称管理"]
)
@router.put("/titles/{title_id}")
async def update_title(
    title_id: int,
    request: TitleUpdateRequest,
    user=Depends(require_permission)
):
    """更新职称"""
    with db_config.get_session() as session:
        result = session.execute(
            select(Title).where(Title.title_id == title_id)
        )
        title = result.scalars().first()

        if not title:
            raise HTTPException(status_code=404, detail="职称不存在")

        # 检查新职称名称是否与其他职称冲突
        if request.title_name and request.title_name != title.title_name:
            existing_title = session.execute(
                select(Title).where(Title.title_name == request.title_name)
            ).scalars().first()
            if existing_title:
                raise HTTPException(status_code=400, detail="职称名称已存在")
            title.title_name = request.title_name

        session.commit()
        session.refresh(title)

    # 记录审计日志（仅成功）
    audit_log_writer.write_success(
        user_id=user["user_id"],
        operation_type="更新职称",
        operation_details=f"更新职称：职称ID {title.title_id}，职称名称 {title.title_name}"
    )

    return SuccessResponse(
        data={
            "title_id": title.title_id,
            "title_name": title.title_name
        },
        message="职称更新成功"
    )


@api(
    path="/titles/{title_id}",
    method="DELETE",
    name="删除职称",
    description="删除职称（同时将关联用户的外键设为默认值）",
    tags=["职称管理"]
)
@router.delete("/titles/{title_id}")
async def delete_title(
    title_id: int,
    user=Depends(require_permission)
):
    """删除职称"""
    with db_config.get_session() as session:
        result = session.execute(
            select(Title).where(Title.title_id == title_id)
        )
        title = result.scalars().first()

        if not title:
            raise HTTPException(status_code=404, detail="职称不存在")

        from app.models import User
        from app.config.server import server_config
        from sqlalchemy import update

        default_title_id = server_config.settings.default_title_id
        if title_id == default_title_id:
            raise HTTPException(status_code=400, detail="不能删除默认职称")

        update_query = (
            update(User)
            .where(User.title_id == title_id)
            .values(title_id=default_title_id)
        )
        session.execute(update_query)

        session.delete(title)
        session.commit()

    # 记录审计日志（仅成功）
    audit_log_writer.write_success(
        user_id=user["user_id"],
        operation_type="删除职称",
        operation_details=f"删除职称：职称ID {title_id}，职称名称 {title.title_name}"
    )

    return SuccessResponse(
        data=None,
        message="职称删除成功"
    )
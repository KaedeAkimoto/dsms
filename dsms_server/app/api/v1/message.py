"""
消息管理API路由
"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends, Query, Request
from fastapi.responses import StreamingResponse
import asyncio
import json

from app.core.responses import SuccessResponse, CreatedResponse
from app.core.middlewares import require_permission
from app.core.system_roles import api
from app.core.connection_manager import sse_connection_manager
from app.schemas.message import (
    SystemMessageResponse,
    SystemMessageListResponse,
    SystemMessageCreateRequest,
    SystemMessageBatchCreateRequest,
    AnnouncementResponse,
    AnnouncementListResponse,
    AnnouncementCreateRequest,
    AnnouncementUpdateRequest,
    UserMessageResponse,
    UserMessageListResponse,
    UserMessageCreateRequest,
)
from app.services.message import (
    system_message_service,
    announcement_service,
    user_message_service,
)
from app.services.audit_log import audit_log_writer

router = APIRouter()


@api(
    path="/sse/connect",
    method="GET",
    name="建立SSE连接",
    description="建立服务端推送（SSE）连接，接收实时消息通知",
    tags=["消息管理"]
)
@router.get("/sse/connect")
async def sse_connect(request: Request, user: dict = Depends(require_permission)):
    user_id = user["user_id"]

    async def event_generator():
        queue = asyncio.Queue()
        sse_connection_manager.active_connections.setdefault(str(user_id), set()).add(queue)

        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    message = await asyncio.wait_for(queue.get(), timeout=30)
                    yield f"data: {json.dumps(message, default=str)}\n\n"
                except asyncio.TimeoutError:
                    yield f"data: {json.dumps({'type': 'heartbeat', 'message': 'ping'})}\n\n"
        except Exception as e:
            pass
        finally:
            if str(user_id) in sse_connection_manager.active_connections:
                sse_connection_manager.active_connections[str(user_id)].discard(queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@api(
    path="/sse/send/{target_user_id}",
    method="POST",
    name="发送SSE测试消息",
    description="通过SSE发送测试消息（内部使用）",
    tags=["消息管理"]
)
@router.post("/sse/send/{target_user_id}")
async def send_sse_message(
    target_user_id: UUID,
    message: dict,
    user: dict = Depends(require_permission)
):
    await sse_connection_manager.send_personal_message(message, target_user_id)
    return SuccessResponse(data={"status": "sent"}, message="消息已发送")


# ==================== 系统消息接口 ====================

@api(
    path="/system-messages",
    method="POST",
    name="发送系统消息",
    description="向指定用户发送系统消息",
    tags=["消息管理"]
)
@router.post("/system-messages")
async def create_system_message(
    request: SystemMessageCreateRequest,
    user: dict = Depends(require_permission)
):
    message = system_message_service.create_message(
        receive_user=request.receive_user,
        content=request.content
    )
    audit_log_writer.write_success(
        user_id=user["user_id"],
        operation_type="发送系统消息",
        operation_details=f"发送系统消息给用户 {request.receive_user}"
    )
    return CreatedResponse(
        data=SystemMessageResponse.from_orm(message).model_dump(mode="json"),
        message="系统消息发送成功"
    )


@api(
    path="/system-messages/batch",
    method="POST",
    name="批量发送系统消息",
    description="向多个用户批量发送系统消息",
    tags=["消息管理"]
)
@router.post("/system-messages/batch")
async def batch_create_system_message(
    request: SystemMessageBatchCreateRequest,
    user: dict = Depends(require_permission)
):
    messages = system_message_service.batch_create_messages(
        user_ids=request.user_ids,
        content=request.content
    )
    audit_log_writer.write_success(
        user_id=user["user_id"],
        operation_type="批量发送系统消息",
        operation_details=f"批量发送系统消息给 {len(messages)} 个用户"
    )
    return CreatedResponse(
        data={"count": len(messages)},
        message=f"成功向 {len(messages)} 个用户发送系统消息"
    )


@api(
    path="/system-messages/my",
    method="GET",
    name="获取我的系统消息",
    description="获取当前登录用户的系统消息",
    tags=["消息管理"]
)
@router.get("/system-messages/my")
async def get_my_system_messages(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    status: Optional[str] = Query(default=None),
    user: dict = Depends(require_permission)
):
    user_info = user
    messages = system_message_service.get_user_messages(
        user_id=user_info["user_id"],
        skip=skip,
        limit=limit
    )
    total = system_message_service.count_user_messages(
        user_id=user_info["user_id"],
        status=status
    )
    return SuccessResponse(
        data=SystemMessageListResponse(
            total=total,
            messages=[SystemMessageResponse.from_orm(m) for m in messages]
        ).model_dump(mode="json"),
        message="获取系统消息成功"
    )


@api(
    path="/system-messages/{msg_id}",
    method="GET",
    name="获取系统消息详情",
    description="根据ID获取系统消息详情",
    tags=["消息管理"]
)
@router.get("/system-messages/{msg_id}")
async def get_system_message(
    msg_id: UUID,
    user: dict = Depends(require_permission)
):
    message = system_message_service.get_message_by_id(msg_id)
    if not message:
        raise HTTPException(status_code=404, detail="消息不存在")
    return SuccessResponse(
        data=SystemMessageResponse.from_orm(message).model_dump(mode="json"),
        message="获取消息详情成功"
    )


@api(
    path="/system-messages/{msg_id}/read",
    method="PUT",
    name="标记系统消息已读",
    description="标记系统消息为已读状态",
    tags=["消息管理"]
)
@router.put("/system-messages/{msg_id}/read")
async def mark_system_message_read(
    msg_id: UUID,
    user: dict = Depends(require_permission)
):
    success = system_message_service.mark_as_read(msg_id)
    if not success:
        raise HTTPException(status_code=404, detail="消息不存在")
    return SuccessResponse(
        data=None,
        message="标记已读成功"
    )


@api(
    path="/system-messages/my/read-all",
    method="PUT",
    name="标记所有系统消息已读",
    description="标记当前用户所有系统消息为已读",
    tags=["消息管理"]
)
@router.put("/system-messages/my/read-all")
async def mark_all_system_messages_read(
    user: dict = Depends(require_permission)
):
    user_info = user
    count = system_message_service.mark_all_as_read(user_info["user_id"])
    return SuccessResponse(
        data={"count": count},
        message=f"已标记 {count} 条消息为已读"
    )


# ==================== 公告接口 ====================

@api(
    path="/announcements",
    method="POST",
    name="发布公告",
    description="发布新公告",
    tags=["消息管理"]
)
@router.post("/announcements")
async def create_announcement(
    request: AnnouncementCreateRequest,
    user: dict = Depends(require_permission)
):
    user_info = user
    announcement = announcement_service.create_announcement(
        receiver_type=request.receiver_type,
        receive_target=request.receive_target,
        content=request.content,
        send_user=user_info["user_id"],
        expired=request.expired
    )
    audit_log_writer.write_success(
        user_id=user["user_id"],
        operation_type="发布公告",
        operation_details=f"发布公告，ID: {announcement.announcement_id}"
    )
    return CreatedResponse(
        data=AnnouncementResponse.from_orm(announcement).model_dump(mode="json"),
        message="公告发布成功"
    )


@api(
    path="/announcements",
    method="GET",
    name="获取公告列表",
    description="获取所有公告列表（管理员）\n\n过期公告权限规则：\n- 未过期公告：所有用户可见\n- 已过期公告：仅发送者和管理员角色可见（hr_admin, senior_sys_admin, super_sys_admin）",
    tags=["消息管理"]
)
@router.get("/announcements")
async def get_all_announcements(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    user: dict = Depends(require_permission)
):
    user_info = user
    announcements = announcement_service.get_announcements_for_admin(
        user_id=user_info["user_id"],
        role_id=user_info["role_id"],
        skip=skip,
        limit=limit
    )

    result = []
    for announcement in announcements:
        read_count = announcement_service.get_read_count(announcement.announcement_id)
        response = AnnouncementResponse.from_orm(announcement).model_dump(mode="json")
        response["read_count"] = read_count
        result.append(response)

    return SuccessResponse(
        data=AnnouncementListResponse(
            total=len(result),
            announcements=result
        ).model_dump(mode="json"),
        message="获取公告列表成功"
    )


@api(
    path="/announcements/my",
    method="GET",
    name="获取我的公告",
    description="获取当前用户可见的公告",
    tags=["消息管理"]
)
@router.get("/announcements/my")
async def get_my_announcements(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    user: dict = Depends(require_permission)
):
    user_info = user
    announcements = announcement_service.get_user_announcements(
        user_id=user_info["user_id"],
        skip=skip,
        limit=limit
    )
    total = announcement_service.count_user_announcements(user_info["user_id"])
    
    result = []
    for announcement in announcements:
        read_count = announcement_service.get_read_count(announcement.announcement_id)
        is_read = announcement_service.is_read(announcement.announcement_id, user_info["user_id"])
        response = AnnouncementResponse.from_orm(announcement).model_dump(mode="json")
        response["read_count"] = read_count
        response["is_read"] = is_read
        result.append(response)
    
    return SuccessResponse(
        data=AnnouncementListResponse(
            total=total,
            announcements=result
        ).model_dump(mode="json"),
        message="获取公告列表成功"
    )


@api(
    path="/announcements/{announcement_id}",
    method="GET",
    name="获取公告详情",
    description="根据ID获取公告详情\n\n过期公告权限规则：\n- 未过期公告：所有能收到该公告的用户可查看\n- 已过期公告：仅发送者和管理员角色可见（hr_admin, senior_sys_admin, super_sys_admin）",
    tags=["消息管理"]
)
@router.get("/announcements/{announcement_id}")
async def get_announcement(
    announcement_id: UUID,
    user: dict = Depends(require_permission)
):
    user_info = user
    announcement = announcement_service.get_announcement_by_id(announcement_id)
    if not announcement:
        raise HTTPException(status_code=404, detail="公告不存在")

    if not announcement_service.can_view_announcement(
        announcement_id=announcement_id,
        user_id=user_info["user_id"],
        role_id=user_info["role_id"]
    ):
        raise HTTPException(status_code=403, detail="无权查看此公告")

    read_count = announcement_service.get_read_count(announcement.announcement_id)
    response = AnnouncementResponse.from_orm(announcement).model_dump(mode="json")
    response["read_count"] = read_count

    return SuccessResponse(
        data=response,
        message="获取公告详情成功"
    )


@api(
    path="/announcements/{announcement_id}",
    method="PUT",
    name="更新公告",
    description="更新公告内容",
    tags=["消息管理"]
)
@router.put("/announcements/{announcement_id}")
async def update_announcement(
    announcement_id: UUID,
    request: AnnouncementUpdateRequest,
    user: dict = Depends(require_permission)
):
    announcement = announcement_service.update_announcement(
        announcement_id=announcement_id,
        **request.dict(exclude_none=True)
    )
    if not announcement:
        raise HTTPException(status_code=404, detail="公告不存在")

    audit_log_writer.write_success(
        user_id=user["user_id"],
        operation_type="更新公告",
        operation_details=f"更新公告，ID: {announcement_id}"
    )

    read_count = announcement_service.get_read_count(announcement.announcement_id)
    response = AnnouncementResponse.from_orm(announcement).model_dump(mode="json")
    response["read_count"] = read_count

    return SuccessResponse(
        data=response,
        message="公告更新成功"
    )


@api(
    path="/announcements/{announcement_id}",
    method="DELETE",
    name="删除公告",
    description="删除指定公告（同时删除关联的已读记录）",
    tags=["消息管理"]
)
@router.delete("/announcements/{announcement_id}")
async def delete_announcement(
    announcement_id: UUID,
    user: dict = Depends(require_permission)
):
    success = announcement_service.delete_announcement(announcement_id)
    if not success:
        raise HTTPException(status_code=404, detail="公告不存在")

    audit_log_writer.write_success(
        user_id=user["user_id"],
        operation_type="删除公告",
        operation_details=f"删除公告，ID: {announcement_id}"
    )

    return SuccessResponse(
        data=None,
        message="公告删除成功"
    )


@api(
    path="/announcements/{announcement_id}/read",
    method="PUT",
    name="标记公告已读",
    description="标记公告为已读状态（仅限未过期公告）",
    tags=["消息管理"]
)
@router.put("/announcements/{announcement_id}/read")
async def mark_announcement_read(
    announcement_id: UUID,
    user: dict = Depends(require_permission)
):
    user_info = user
    announcement = announcement_service.get_announcement_by_id(announcement_id)
    if not announcement:
        raise HTTPException(status_code=404, detail="公告不存在")

    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    expired_time = announcement.expired
    if expired_time.tzinfo is None:
        expired_time = expired_time.replace(tzinfo=timezone.utc)
    if expired_time <= now:
        raise HTTPException(status_code=400, detail="已过期公告无法标记已读")

    success = announcement_service.mark_as_read(announcement_id, user_info["user_id"])
    if not success:
        raise HTTPException(status_code=404, detail="公告不存在")
    return SuccessResponse(
        data=None,
        message="标记已读成功"
    )


@api(
    path="/announcements/{announcement_id}/readers",
    method="GET",
    name="获取公告已读用户列表",
    description="获取指定公告的已读用户列表",
    tags=["消息管理"]
)
@router.get("/announcements/{announcement_id}/readers")
async def get_announcement_readers(
    announcement_id: UUID,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    user: dict = Depends(require_permission)
):
    """获取公告已读用户列表"""
    announcement = announcement_service.get_announcement_by_id(announcement_id)
    if not announcement:
        raise HTTPException(status_code=404, detail="公告不存在")

    readers_data = announcement_service.get_readers(announcement_id, skip=skip, limit=limit)

    return SuccessResponse(
        data={
            "total": readers_data["total"],
            "readers": readers_data["readers"]
        },
        message="查询成功"
    )


@api(
    path="/announcements/{announcement_id}/read-status",
    method="GET",
    name="查询公告已读状态",
    description="查询当前用户是否已阅读指定公告",
    tags=["消息管理"]
)
@router.get("/announcements/{announcement_id}/read-status")
async def check_announcement_read_status(
    announcement_id: UUID,
    user: dict = Depends(require_permission)
):
    """查询当前用户是否已读公告"""
    announcement = announcement_service.get_announcement_by_id(announcement_id)
    if not announcement:
        raise HTTPException(status_code=404, detail="公告不存在")

    is_read = announcement_service.is_read(announcement_id, user["user_id"])

    return SuccessResponse(
        data={"is_read": is_read},
        message="查询成功"
    )


# ==================== 用户消息接口 ====================

@api(
    path="/user-messages",
    method="POST",
    name="发送用户消息",
    description="用户之间发送消息",
    tags=["消息管理"]
)
@router.post("/user-messages")
async def create_user_message(
    request: UserMessageCreateRequest,
    user: dict = Depends(require_permission)
):
    user_info = user
    message = user_message_service.create_message(
        send_user=user_info["user_id"],
        receive_user=request.receive_user,
        content=request.content
    )
    audit_log_writer.write_success(
        user_id=user["user_id"],
        operation_type="发送用户消息",
        operation_details=f"发送消息给用户 {request.receive_user}"
    )
    return CreatedResponse(
        data=UserMessageResponse.from_orm(message).model_dump(mode="json"),
        message="消息发送成功"
    )


@api(
    path="/user-messages/sent",
    method="GET",
    name="获取我发送的消息",
    description="获取当前用户发送的消息",
    tags=["消息管理"]
)
@router.get("/user-messages/sent")
async def get_my_sent_messages(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    user: dict = Depends(require_permission)
):
    user_info = user
    messages = user_message_service.get_user_sent_messages(
        user_id=user_info["user_id"],
        skip=skip,
        limit=limit
    )
    total = user_message_service.count_user_messages(
        user_id=user_info["user_id"],
        is_sent=True
    )
    return SuccessResponse(
        data=UserMessageListResponse(
            total=total,
            messages=[UserMessageResponse.from_orm(m).model_dump(mode="json") for m in messages]
        ).model_dump(mode="json"),
        message="获取发送消息成功"
    )


@api(
    path="/user-messages/received",
    method="GET",
    name="获取我接收的消息",
    description="获取当前用户接收的消息",
    tags=["消息管理"]
)
@router.get("/user-messages/received")
async def get_my_received_messages(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    status: Optional[str] = Query(default=None),
    user: dict = Depends(require_permission)
):
    user_info = user
    messages = user_message_service.get_user_received_messages(
        user_id=user_info["user_id"],
        skip=skip,
        limit=limit
    )
    total = user_message_service.count_user_messages(
        user_id=user_info["user_id"],
        status=status,
        is_sent=False
    )
    return SuccessResponse(
        data=UserMessageListResponse(
            total=total,
            messages=[UserMessageResponse.from_orm(m).model_dump(mode="json") for m in messages]
        ).model_dump(mode="json"),
        message="获取接收消息成功"
    )


@api(
    path="/user-messages/{msg_id}",
    method="GET",
    name="获取用户消息详情",
    description="根据ID获取用户消息详情",
    tags=["消息管理"]
)
@router.get("/user-messages/{msg_id}")
async def get_user_message(
    msg_id: UUID,
    user: dict = Depends(require_permission)
):
    message = user_message_service.get_message_by_id(msg_id)
    if not message:
        raise HTTPException(status_code=404, detail="消息不存在")
    return SuccessResponse(
        data=UserMessageResponse.from_orm(message).model_dump(mode="json"),
        message="获取消息详情成功"
    )


@api(
    path="/user-messages/{msg_id}/read",
    method="PUT",
    name="标记用户消息已读",
    description="标记用户消息为已读状态",
    tags=["消息管理"]
)
@router.put("/user-messages/{msg_id}/read")
async def mark_user_message_read(
    msg_id: UUID,
    user: dict = Depends(require_permission)
):
    success = user_message_service.mark_as_read(msg_id)
    if not success:
        raise HTTPException(status_code=404, detail="消息不存在")
    return SuccessResponse(
        data=None,
        message="标记已读成功"
    )


@api(
    path="/user-messages/received/read-all",
    method="PUT",
    name="标记所有用户消息已读",
    description="标记当前用户所有接收消息为已读",
    tags=["消息管理"]
)
@router.put("/user-messages/received/read-all")
async def mark_all_user_messages_read(
    user: dict = Depends(require_permission)
):
    user_info = user
    count = user_message_service.mark_all_received_as_read(user_info["user_id"])
    return SuccessResponse(
        data={"count": count},
        message=f"已标记 {count} 条消息为已读"
    )

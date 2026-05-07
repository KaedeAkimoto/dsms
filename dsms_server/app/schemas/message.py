"""
消息相关的Pydantic模型定义
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field


class SystemMessageResponse(BaseModel):
    """系统消息响应模型"""
    msg_id: UUID = Field(description="消息ID")
    receive_user: UUID = Field(description="接收用户ID")
    content: str = Field(description="消息内容")
    created_at: datetime = Field(description="发送时间")
    status: str = Field(description="消息状态: read(已读), unread(未读)")
    readed_at: Optional[datetime] = Field(description="阅读时间")

    @classmethod
    def from_orm(cls, obj):
        """从ORM模型创建响应"""
        return cls.model_validate({
            'msg_id': str(obj.msg_id),
            'receive_user': str(obj.receive_user),
            'content': obj.content,
            'created_at': obj.created_at,
            'status': obj.status,
            'readed_at': obj.readed_at
        })


class SystemMessageListResponse(BaseModel):
    """系统消息列表响应模型"""
    total: int = Field(description="消息总数")
    messages: List[SystemMessageResponse] = Field(description="消息列表")


class SystemMessageCreateRequest(BaseModel):
    """系统消息创建请求模型"""
    receive_user: UUID = Field(description="接收用户ID")
    content: str = Field(description="消息内容")


class SystemMessageBatchCreateRequest(BaseModel):
    """批量发送系统消息请求模型"""
    user_ids: List[UUID] = Field(description="接收用户ID列表")
    content: str = Field(description="消息内容")


class AnnouncementResponse(BaseModel):
    """公告响应模型"""
    announcement_id: UUID = Field(description="公告ID")
    receiver_type: str = Field(description="接收类型: all(全部), department(部门), role(角色), title(职称)")
    receive_target: Optional[int] = Field(description="接收目标ID")
    content: str = Field(description="公告内容")
    created_at: datetime = Field(description="发布时间")
    send_user: UUID = Field(description="发布用户ID")
    expired: datetime = Field(description="过期时间")
    read_count: int = Field(default=0, description="已读人数")

    class Config:
        from_attributes = True


class AnnouncementListResponse(BaseModel):
    """公告列表响应模型"""
    total: int = Field(description="公告总数")
    announcements: List[AnnouncementResponse] = Field(description="公告列表")


class AnnouncementCreateRequest(BaseModel):
    """公告创建请求模型"""
    receiver_type: str = Field(default="all", description="接收类型: all(全部), department(部门), role(角色), title(职称)")
    receive_target: Optional[int] = Field(default=None, description="接收目标ID, all时为NULL")
    content: str = Field(description="公告内容")
    expired: Optional[datetime] = Field(default=None, description="过期时间，默认7天后")


class AnnouncementUpdateRequest(BaseModel):
    """公告更新请求模型"""
    receiver_type: Optional[str] = Field(description="接收类型")
    receive_target: Optional[int] = Field(description="接收目标ID")
    content: Optional[str] = Field(description="公告内容")
    expired: Optional[datetime] = Field(description="过期时间")


class UserMessageResponse(BaseModel):
    """用户消息响应模型"""
    msg_id: UUID = Field(description="消息ID")
    send_user: UUID = Field(description="发送用户ID")
    receive_user: UUID = Field(description="接收用户ID")
    content: str = Field(description="消息内容")
    created_at: datetime = Field(description="发送时间")
    status: str = Field(description="消息状态: read(已读), unread(未读)")
    readed_at: Optional[datetime] = Field(description="阅读时间")
    sender_name: Optional[str] = Field(description="发送者姓名")
    receiver_name: Optional[str] = Field(description="接收者姓名")

    @classmethod
    def from_orm(cls, obj):
        """从ORM模型创建响应"""
        return cls.model_validate({
            'msg_id': str(obj.msg_id),
            'send_user': str(obj.send_user),
            'receive_user': str(obj.receive_user),
            'content': obj.content,
            'created_at': obj.created_at,
            'status': obj.status,
            'readed_at': obj.readed_at,
            'sender_name': getattr(obj, 'sender_name', None),
            'receiver_name': getattr(obj, 'receiver_name', None)
        })


class UserMessageListResponse(BaseModel):
    """用户消息列表响应模型"""
    total: int = Field(description="消息总数")
    messages: List[UserMessageResponse] = Field(description="消息列表")


class UserMessageCreateRequest(BaseModel):
    """用户消息创建请求模型"""
    receive_user: UUID = Field(description="接收用户ID")
    content: str = Field(description="消息内容")

from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field


class AuditLogCreate(BaseModel):
    """创建审计日志的请求Schema"""
    user_id: UUID = Field(description="用户ID")
    operation_type: str = Field(max_length=50, description="操作类型")
    operation_details: Optional[str] = Field(None, description="操作详情")
    ip_addr: Optional[str] = Field(None, description="IP地址")
    operation_result: str = Field(default="success", description="操作结果: success(成功), fail(失败)")
    error_msg: Optional[str] = Field(None, description="错误信息")


class AuditLogResponse(BaseModel):
    """审计日志响应Schema"""
    log_id: UUID = Field(description="日志ID")
    user_id: UUID = Field(description="用户ID")
    operation_type: str = Field(description="操作类型")
    operation_details: Optional[str] = Field(None, description="操作详情")
    ip_addr: Optional[str] = Field(None, description="IP地址")
    operation_result: str = Field(description="操作结果")
    error_msg: Optional[str] = Field(None, description="错误信息")
    created_at: datetime = Field(description="创建时间")

    class Config:
        from_attributes = True


class AuditLogQuery(BaseModel):
    """审计日志查询参数Schema"""
    skip: int = Field(default=0, ge=0, description="跳过记录数")
    limit: int = Field(default=100, ge=1, le=1000, description="返回记录数")
    user_id: Optional[UUID] = Field(None, description="按用户ID过滤")
    operation_type: Optional[str] = Field(None, description="按操作类型过滤")
    operation_result: Optional[str] = Field(None, description="按操作结果过滤 (success/fail)")
    start_date: Optional[datetime] = Field(None, description="开始时间")
    end_date: Optional[datetime] = Field(None, description="结束时间")


class AuditLogListResponse(BaseModel):
    """审计日志列表响应Schema"""
    total: int = Field(description="总记录数")
    logs: List[AuditLogResponse] = Field(description="日志列表")

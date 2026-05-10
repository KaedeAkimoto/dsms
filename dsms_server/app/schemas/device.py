from datetime import date, datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field


class DeviceCreateRequest(BaseModel):
    device_name: str = Field(min_length=1, max_length=100, description="设备名称")
    device_type: str = Field(min_length=1, max_length=50, description="设备类型")
    production_line_id: UUID = Field(description="所属生产线ID")
    device_manager: UUID = Field(description="设备负责人ID")
    ip_addr: Optional[str] = Field(None, max_length=50, description="设备IP地址")
    mac_addr: Optional[str] = Field(None, max_length=17, description="设备MAC地址")
    installation_date: Optional[date] = Field(None, description="设备安装日期")


class DeviceUpdateRequest(BaseModel):
    device_name: Optional[str] = Field(None, min_length=1, max_length=100, description="设备名称")
    device_type: Optional[str] = Field(None, min_length=1, max_length=50, description="设备类型")
    production_line_id: Optional[UUID] = Field(None, description="所属生产线ID")
    device_manager: Optional[UUID] = Field(None, description="设备负责人ID")
    ip_addr: Optional[str] = Field(None, max_length=50, description="设备IP地址")
    mac_addr: Optional[str] = Field(None, max_length=17, description="设备MAC地址")
    status: Optional[str] = Field(None, description="设备状态")


def convert_datetime_to_string(dt):
    if isinstance(dt, datetime):
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    return dt


class DeviceResponse(BaseModel):
    device_id: UUID
    device_name: str
    device_type: str
    device_upload_token: Optional[str] = None
    production_line_id: UUID
    device_manager: UUID
    ip_addr: Optional[str] = None
    mac_addr: Optional[str] = None
    status: str
    device_approval_id: Optional[UUID] = None
    installation_date: Optional[str] = None
    created_at: Optional[str] = None

    @classmethod
    def from_orm(cls, obj):
        return cls.model_validate({
            'device_id': str(obj.device_id),
            'device_name': obj.device_name,
            'device_type': obj.device_type,
            'device_upload_token': obj.device_upload_token,
            'production_line_id': str(obj.production_line_id),
            'device_manager': str(obj.device_manager),
            'ip_addr': obj.ip_addr,
            'mac_addr': obj.mac_addr,
            'status': obj.status,
            'device_approval_id': str(obj.device_approval_id) if obj.device_approval_id else None,
            'installation_date': str(obj.installation_date) if obj.installation_date else None,
            'created_at': convert_datetime_to_string(obj.created_at) if hasattr(obj, 'created_at') and obj.created_at else None,
        })


class DeviceListResponse(BaseModel):
    total: int
    devices: List[DeviceResponse]


class DeviceTokenResponse(BaseModel):
    device_id: UUID
    device_name: str
    device_upload_token: Optional[str] = None


class DeviceTokenListResponse(BaseModel):
    total: int
    devices: List[DeviceTokenResponse]


class BatchTokenGenerateRequest(BaseModel):
    device_ids: List[UUID] = Field(min_length=1, description="设备ID列表")


class BatchTokenGenerateResponse(BaseModel):
    total: int
    success_count: int
    failed_count: int
    tokens: List[DeviceTokenResponse]


class ProductionLineCreateRequest(BaseModel):
    line_name: str = Field(description="生产线名称")
    line_code: str = Field(description="生产线编码")
    description: Optional[str] = Field(None, description="生产线描述")


class ProductionLineUpdateRequest(BaseModel):
    line_name: Optional[str] = Field(None, description="生产线名称")
    description: Optional[str] = Field(None, description="生产线描述")


class ProductionLineResponse(BaseModel):
    production_line_id: UUID
    line_name: str
    line_code: str
    description: Optional[str] = None
    created_at: Optional[str] = None

    @classmethod
    def from_orm(cls, obj):
        return cls.model_validate({
            'production_line_id': str(obj.production_line_id),
            'line_name': obj.production_line_name,
            'line_code': obj.production_line_loc,
            'description': getattr(obj, 'description', None),
            'created_at': convert_datetime_to_string(obj.created_at) if hasattr(obj, 'created_at') and obj.created_at else None,
        })


class ProductionLineListResponse(BaseModel):
    total: int
    production_lines: List[ProductionLineResponse]


class DeviceApprovalRequest(BaseModel):
    device_name: str = Field(description="设备名称")
    device_type: str = Field(description="设备类型")
    production_line_id: UUID = Field(description="生产线ID")
    device_manager: UUID = Field(description="设备管理员ID")
    approval_by: UUID = Field(description="审批人ID")
    reason: Optional[str] = Field(None, description="申请原因")


class DeviceApprovalResponse(BaseModel):
    device_approval_id: UUID
    device_id: Optional[UUID] = None
    approver_id: UUID
    status: str
    comment: Optional[str] = None
    created_at: Optional[str] = None

    @classmethod
    def from_orm(cls, obj):
        # 从关联的设备列表中获取第一个设备ID
        device_id = str(obj.devices[0].device_id) if obj.devices and len(obj.devices) > 0 else None
        
        return cls.model_validate({
            'device_approval_id': str(obj.device_approval_id),
            'device_id': device_id,
            'approver_id': str(obj.approval_by),
            'status': obj.approval_status,
            'comment': getattr(obj, 'comment', None),
            'created_at': convert_datetime_to_string(obj.created_at) if hasattr(obj, 'created_at') and obj.created_at else None,
        })


class DeviceApprovalListResponse(BaseModel):
    total: int
    approvals: List[DeviceApprovalResponse]


class DeviceStatusHistoryResponse(BaseModel):
    status_history_id: UUID
    device_id: UUID
    old_status: Optional[str] = None
    new_status: str
    changed_by: UUID
    changed_at: Optional[str] = None
    reason: Optional[str] = None

    @classmethod
    def from_orm(cls, obj):
        return cls.model_validate({
            'status_history_id': str(obj.status_history_id),
            'device_id': str(obj.device_id),
            'old_status': obj.old_status,
            'new_status': obj.new_status,
            'changed_by': str(obj.changed_by),
            'changed_at': convert_datetime_to_string(obj.changed_at) if hasattr(obj, 'changed_at') and obj.changed_at else None,
            'reason': obj.reason,
        })


class DeviceStatusHistoryListResponse(BaseModel):
    total: int
    history: List[DeviceStatusHistoryResponse]
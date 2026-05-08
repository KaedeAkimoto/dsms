import base64
from typing import Optional, List, Tuple
from datetime import datetime
from pydantic import BaseModel, Field
from uuid import UUID


def convert_datetime_to_string(dt: Optional[datetime]) -> Optional[str]:
    """将 datetime 转换为 ISO 格式字符串"""
    if dt is None:
        return None
    return dt.isoformat()


class DefectTypeResponse(BaseModel):
    """缺陷类型响应"""
    defect_type_id: int
    defect_type_name: str


class DefectDetailResponse(BaseModel):
    """缺陷详情响应"""
    defect_details_id: UUID
    record_batch_id: str
    image_base64: str
    image_format: str
    defect_count: Optional[int] = None
    details: Optional[List[dict]] = None
    created_at: Optional[str] = None


class DetectionRecordResponse(BaseModel):
    """检测记录响应"""
    record_batch_id: str
    device_id: UUID
    detect_count: Optional[int] = None
    pass_count: Optional[int] = None
    detect_info: List[dict] = []
    latest_upload_at: Optional[str] = None
    defect_details: List[DefectDetailResponse] = []

    @classmethod
    def from_orm(cls, obj):
        """从 ORM 模型创建响应"""
        return cls.model_validate({
            'record_batch_id': obj.record_batch_id,
            'device_id': str(obj.device_id),
            'detect_count': obj.detect_count,
            'pass_count': obj.pass_count,
            'detect_info': obj.detect_info if obj.detect_info else [],
            'latest_upload_at': convert_datetime_to_string(obj.latest_upload_at),
            'defect_details': [
                {
                    'defect_details_id': str(d.defect_details_id),
                    'record_batch_id': d.record_batch_id,
                    'image_base64': base64.b64encode(d.image).decode('utf-8') if d.image else '',
                    'image_format': d.image_format,
                    'defect_count': d.defect_count,
                    'details': d.details if d.details else [],
                    'created_at': None
                }
                for d in (obj.defect_details or [])
            ]
        })


class DetectionRecordListResponse(BaseModel):
    """检测记录列表响应"""
    total: int
    records: List[DetectionRecordResponse]


class DetectionRecordCreateRequest(BaseModel):
    """创建检测记录请求"""
    device_id: UUID = Field(description="设备ID")
    detect_count: Optional[int] = Field(None, description="检测总数")
    pass_count: Optional[int] = Field(None, description="通过数量")
    detect_info: List[dict] = Field(default=[], description="检测信息JSON数组")


class DefectDetailCreateRequest(BaseModel):
    """创建缺陷详情请求"""
    record_batch_id: str = Field(description="检测批次ID")
    image_base64: str = Field(description="原始图片base64编码")
    image_format: str = Field(description="图片格式: jpeg, png, webp")
    defect_count: Optional[int] = Field(None, description="缺陷数量")
    details: Optional[List[dict]] = Field(None, description="缺陷详情JSON数组")


class ReviewTaskResponse(BaseModel):
    """审查任务响应"""
    review_task_id: UUID
    defect_details_id: UUID
    assignee_id: UUID
    reviewer_id: Optional[UUID] = None
    review_status: str = "pending"
    review_result: Optional[str] = None
    review_defect_count: Optional[int] = None
    has_details: Optional[bool] = None
    review_details: Optional[List[dict]] = None
    review_comment: Optional[str] = None
    assignee_at: Optional[str] = None
    completed_at: Optional[str] = None

    @classmethod
    def from_orm(cls, obj):
        """从 ORM 模型创建响应"""
        return cls.model_validate({
            'review_task_id': str(obj.review_task_id),
            'defect_details_id': str(obj.defect_details_id),
            'assignee_id': str(obj.assignee_id),
            'reviewer_id': str(obj.reviewer_id) if obj.reviewer_id else None,
            'review_status': obj.review_status,
            'review_result': obj.review_result,
            'review_defect_count': obj.review_defect_count,
            'has_details': obj.has_details,
            'review_details': obj.review_details if obj.review_details else [],
            'review_comment': obj.review_comment,
            'assignee_at': convert_datetime_to_string(obj.assignee_at),
            'completed_at': convert_datetime_to_string(obj.completed_at)
        })


class ReviewTaskListResponse(BaseModel):
    """审查任务列表响应"""
    total: int
    tasks: List[ReviewTaskResponse]


class ReviewTaskUpdateRequest(BaseModel):
    """更新审查任务请求"""
    reviewer_id: Optional[UUID] = Field(None, description="审查员ID")
    review_status: Optional[str] = Field(None, description="审查状态")
    review_result: Optional[str] = Field(None, description="审查结果")
    review_defect_count: Optional[int] = Field(None, description="缺陷数量")
    has_details: Optional[bool] = Field(None, description="是否有详情")
    review_details: Optional[List[dict]] = Field(None, description="审查详情")
    review_comment: Optional[str] = Field(None, description="审查评论")


class ReviewTaskTransferRequest(BaseModel):
    """移交审查任务请求"""
    new_assignee_id: UUID = Field(description="新负责人ID")
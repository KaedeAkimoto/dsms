from typing import List, Tuple, Optional
from pydantic import BaseModel, Field, field_validator, RootModel
from pydantic.functional_validators import AfterValidator
from typing_extensions import Annotated


class DetectInfoItem(BaseModel):
    """检测信息项
    
    用于验证 DetectionRecord.detect_info 字段中的单个元素
    """
    defect_type_id: int = Field(description="缺陷类型ID")
    defect_count: int = Field(description="缺陷数量")
    
    @field_validator('defect_count')
    def defect_count_must_be_non_negative(cls, v):
        if v < 0:
            raise ValueError('缺陷数量不能为负数')
        return v


class DefectDetailItem(BaseModel):
    """缺陷详情项
    
    用于验证 DefectDetail.details 和 ReviewTask.review_details 字段中的单个元素
    """
    defect_type_id: int = Field(description="缺陷类型ID")
    # 缺陷位置和尺寸 (x, y, h, w), 值是归一化后的数据
    xyhw: Tuple[float, float, float, float] = Field(description="缺陷位置和尺寸 (x, y, h, w)")
    conf: float = Field(description="置信度 (0-1)")
    
    @field_validator('conf')
    def conf_must_be_between_0_and_1(cls, v):
        if not (0 <= v <= 1):
            raise ValueError('置信度必须在0到1之间')
        return v

    @field_validator('xyhw')
    def xyhw_must_be_normalized(cls, v):
        if not (0 <= v[0] <= 1 and v[1] <= 1 and v[2] <= 1 and v[3] <= 1):
            raise ValueError('位置和尺寸必须在0到1之间')
        return v


class PermissionItem(BaseModel):
    """权限项
    
    用于验证 Role.permissions 字段中的单个元素
    """
    api: str = Field(description="API路径")
    accessibility: str = Field(description="访问权限")
    
    @field_validator('accessibility')       
    def accessibility_must_be_valid(cls, v):
        valid_values = {'get', 'post', 'put', 'delete', 'options', 'GET', 'POST', 'PUT', 'DELETE', 'OPTIONS', '*'}
        if v.lower() not in valid_values and v != '*':
            raise ValueError(f'访问权限必须是 {valid_values} 之一')
        return v


class DetectInfoSchema(RootModel[List[DetectInfoItem]]):
    """检测信息列表
    
    用于验证 DetectionRecord.detect_info 字段
    格式: [{'defect_type_id': int, 'defect_count': int}, ...]
    无缺陷时为: []
    """
    model_config = {"json_schema_extra": {"description": "检测信息列表"}}


class DefectDetailsSchema(RootModel[List[DefectDetailItem]]):
    """缺陷详情列表
    
    用于验证 DefectDetail.details 和 ReviewTask.review_details 字段
    格式: [{'defect_type_id': int, 'xyhw': (float, float, float, float), 'conf': float}, ...]
    """
    model_config = {"json_schema_extra": {"description": "缺陷详情列表"}}


class PermissionsSchema(RootModel[List[PermissionItem]]):
    """权限列表
    
    用于验证 Role.permissions 字段
    格式: [{'api': str, 'accessibility': str}, ...]
    允许为空值
    """
    model_config = {"json_schema_extra": {"description": "权限列表"}}


# 类型别名，用于模型字段验证
DetectInfoList = Annotated[List[DetectInfoItem], AfterValidator(lambda x: x)]
DefectDetailList = Annotated[List[DefectDetailItem], AfterValidator(lambda x: x)]
PermissionList = Annotated[List[PermissionItem], AfterValidator(lambda x: x)]


class DeviceStatusEnum:
    """设备状态枚举"""
    INACTIVE = 'inactive'
    ACTIVE = 'active'
    MAINTENANCE = 'maintenance'
    FAULT = 'fault'
    REMOVED = 'removed'
    
    @classmethod
    def all(cls):
        return [cls.INACTIVE, cls.ACTIVE, cls.MAINTENANCE, cls.FAULT, cls.REMOVED]


class ApprovalStatusEnum:
    """审批状态枚举"""
    PENDING = 'pending'
    APPROVED = 'approved'
    REJECTED = 'rejected'
    
    @classmethod
    def all(cls):
        return [cls.PENDING, cls.APPROVED, cls.REJECTED]


class ReviewStatusEnum:
    """审查状态枚举"""
    PENDING = 'pending'
    COMPLETED = 'completed'
    CANCEL = 'cancel'
    TIMEOUT = 'timeout'
    
    @classmethod
    def all(cls):
        return [cls.PENDING, cls.COMPLETED, cls.CANCEL, cls.TIMEOUT]


class ReviewResultEnum:
    """审查结果枚举"""
    CONFIRMED = 'confirmed'
    FALSE_POSITIVE = 'false_positive'
    UNCERTAIN = 'uncertain'
    CONFUSION = 'confusion'
    
    @classmethod
    def all(cls):
        return [cls.CONFIRMED, cls.FALSE_POSITIVE, cls.UNCERTAIN, cls.CONFUSION]


class MessageStatusEnum:
    """消息状态枚举"""
    UNREAD = 'unread'
    READ = 'read'
    
    @classmethod
    def all(cls):
        return [cls.UNREAD, cls.READ]


class OperationResultEnum:
    """操作结果枚举"""
    SUCCESS = 'success'
    FAIL = 'fail'
    
    @classmethod
    def all(cls):
        return [cls.SUCCESS, cls.FAIL]

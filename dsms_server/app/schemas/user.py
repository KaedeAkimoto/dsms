from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr
from uuid import UUID


def convert_datetime_to_string(dt: Optional[datetime]) -> Optional[str]:
    """将 datetime 转换为 ISO 格式字符串"""
    if dt is None:
        return None
    return dt.isoformat()


class UserUpdateRequest(BaseModel):
    """用户更新请求"""
    real_name: Optional[str] = Field(None, min_length=1, max_length=50, description="真实姓名")
    email: Optional[EmailStr] = Field(None, description="邮箱")
    phone: Optional[str] = Field(None, max_length=20, description="联系电话")
    department_id: Optional[int] = Field(None, description="部门ID")
    title_id: Optional[int] = Field(None, description="职称ID")
    role_id: Optional[int] = Field(None, description="角色ID")
    avatar_url: Optional[str] = Field(None, description="头像URL")


class PasswordChangeRequest(BaseModel):
    """密码修改请求"""
    old_password: str = Field(description="旧密码")
    new_password: str = Field(min_length=8, max_length=128, description="新密码")


class UserRegisterRequest(BaseModel):
    """用户注册请求

    注意: 注册用户将被分配无权限角色(no_permission_user)，需要管理员分配有效角色后才能正常使用系统
    """
    user_name: str = Field(min_length=3, max_length=50, description="用户名")
    password: str = Field(min_length=8, max_length=128, description="密码")
    real_name: str = Field(min_length=1, max_length=50, description="真实姓名")
    email: Optional[EmailStr] = Field(None, description="邮箱")
    phone: Optional[str] = Field(None, max_length=20, description="联系电话")
    employee_id: Optional[str] = Field(None, max_length=20, description="工号")
    department_id: Optional[int] = Field(None, description="部门ID")
    title_id: Optional[int] = Field(default=9, description="职称ID（默认9=注册员工）")


class BatchUserRegisterRequest(BaseModel):
    """批量用户注册请求"""
    users: list[UserRegisterRequest] = Field(description="用户列表")
    default_role_id: Optional[int] = Field(default=None, description="默认角色ID（不填则自动获取无权限用户角色）")


class UserLoginRequest(BaseModel):
    """用户登录请求"""
    user_name: str = Field(description="用户名")
    password: str = Field(description="密码")


class UserResponse(BaseModel):
    """用户响应"""
    user_id: UUID
    user_name: str
    real_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    employee_id: Optional[str] = None
    department_id: Optional[int] = None
    title_id: int
    role_id: int
    avatar_url: Optional[str] = None
    last_login: Optional[str] = None
    created_at: Optional[str] = None

    @classmethod
    def from_orm(cls, obj):
        """从 ORM 模型创建响应，转换 datetime 字段"""
        return cls.model_validate({
            'user_id': str(obj.user_id),
            'user_name': obj.user_name,
            'real_name': obj.real_name,
            'email': obj.email,
            'phone': obj.phone,
            'employee_id': obj.employee_id,
            'department_id': obj.department_id,
            'title_id': obj.title_id,
            'role_id': obj.role_id,
            'avatar_url': obj.avatar_url,
            'last_login': convert_datetime_to_string(obj.last_login) if obj.last_login else None,
            'created_at': convert_datetime_to_string(obj.created_at) if obj.created_at else None,
        })

    model_config = {"from_attributes": True}


class BatchUserRegisterResponse(BaseModel):
    """批量用户注册响应"""
    success_count: int = Field(description="成功创建的用户数量")
    failed_count: int = Field(description="创建失败的用户数量")
    success_users: list[UserResponse] = Field(description="成功创建的用户列表")
    failed_users: list[dict] = Field(description="创建失败的用户及原因")


class UserListResponse(BaseModel):
    """用户列表响应"""
    total: int
    users: list[UserResponse]


class LoginResponse(BaseModel):
    """登录响应"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse
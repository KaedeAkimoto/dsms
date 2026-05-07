from fastapi import APIRouter, HTTPException, status
from app.core.responses import SuccessResponse, CreatedResponse
from app.core.security import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from app.core.system_roles import api
from app.schemas.user import (
    UserRegisterRequest,
    UserLoginRequest,
    UserResponse,
    LoginResponse
)
from app.services.user import user_service, REGISTERED_EMPLOYEE_TITLE_ID
from app.services.audit_log import audit_log_writer
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()


@api(
    path="/auth/register",
    method="POST",
    name="用户注册",
    description="新用户注册接口",
    tags=["认证"],
    requires_auth=False
)
@router.post("/register")
async def register(request: UserRegisterRequest):
    """用户注册"""
    existing_user = user_service.get_user_by_username(request.user_name)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )

    user = user_service.create_user(
        user_name=request.user_name,
        password=request.password,
        real_name=request.real_name,
        email=request.email,
        phone=request.phone,
        employee_id=request.employee_id,
        department_id=request.department_id,
        title_id=REGISTERED_EMPLOYEE_TITLE_ID
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="用户创建失败"
        )

    audit_log_writer.write_success(
        user_id=user.user_id,
        operation_type="用户注册",
        operation_details=f"用户注册成功：用户名 {user.user_name}，真实姓名 {user.real_name}"
    )

    return CreatedResponse(
        data=UserResponse.from_orm(user).model_dump(mode="json"),
        message="用户注册成功"
    )


@api(
    path="/auth/login",
    method="POST",
    name="用户登录",
    description="用户登录获取Token",
    tags=["认证"],
    requires_auth=False
)
@router.post("/login")
async def login(request: UserLoginRequest):
    """用户登录"""
    user = user_service.authenticate(request.user_name, request.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )

    access_token = create_access_token(
        data={
            "user_id": str(user.user_id),
            "user_name": user.user_name,
            "role_id": user.role_id
        }
    )

    return SuccessResponse(
        data=LoginResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserResponse.from_orm(user).model_dump(mode="json")
        ).model_dump(mode='json'),
        message="登录成功"
    )


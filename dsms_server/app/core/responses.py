from typing import Any, Dict, Optional, Generic, TypeVar
from fastapi import status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# 泛型类型变量
T = TypeVar('T')


# Pydantic 响应模型（用于 response_model 参数）
class SuccessResponseModel(BaseModel, Generic[T]):
    """成功响应模型"""
    code: int = Field(default=200, description="状态码")
    message: str = Field(default="Success", description="提示信息")
    data: Optional[T] = Field(default=None, description="响应数据")

    model_config = {"json_schema_extra": {"description": "成功响应"}}


class PaginatedResponseModel(BaseModel, Generic[T]):
    """分页响应模型"""
    code: int = Field(default=200, description="状态码")
    message: str = Field(default="Success", description="提示信息")
    data: Dict[str, Any] = Field(description="响应数据")

    model_config = {"json_schema_extra": {"description": "分页响应"}}


# 响应类（用于直接返回）
class APIResponse(JSONResponse):
    """API 响应基类"""

    def __init__(
        self,
        content: Any = None,
        status_code: int = status.HTTP_200_OK,
        message: str = "Success",
        **kwargs
    ):
        response_data = {
            "code": status_code,
            "message": message,
            "data": content
        }
        super().__init__(content=response_data, status_code=status_code, **kwargs)


class SuccessResponse(APIResponse):
    """成功响应"""
    
    def __init__(self, data: Any = None, message: str = "Success", **kwargs):
        super().__init__(content=data, message=message, **kwargs)


class CreatedResponse(APIResponse):
    """创建成功响应"""
    
    def __init__(self, data: Any = None, message: str = "Created successfully", **kwargs):
        super().__init__(
            content=data,
            status_code=status.HTTP_201_CREATED,
            message=message,** kwargs
        )


class NoContentResponse(APIResponse):
    """无内容响应"""
    
    def __init__(self, message: str = "No content", **kwargs):
        super().__init__(
            content=None,
            status_code=status.HTTP_204_NO_CONTENT,
            message=message,
            **kwargs
        )


class PaginatedResponse(APIResponse):
    """分页响应"""
    
    def __init__(
        self,
        items: list,
        total: int,
        page: int,
        page_size: int,
        message: str = "Success",
        **kwargs
    ):
        data = {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": (total + page_size - 1) // page_size
        }
        super().__init__(content=data, message=message, **kwargs)

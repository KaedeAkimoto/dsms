from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from typing import Callable, Optional, List, Dict
from functools import wraps
from jose import JWTError, jwt
import re
import asyncio
from app.config.server import server_config
from app.core.role_cache import role_cache
from app.utils.logger import get_logger

logger = get_logger(__name__)

security = HTTPBearer(auto_error=False)


class TimeoutMiddleware(BaseHTTPMiddleware):
    """请求超时中间件，确保所有请求在指定秒数内完成"""

    def __init__(self, app, timeout_seconds: int = 10):
        super().__init__(app)
        self.timeout_seconds = timeout_seconds

    async def dispatch(self, request: Request, call_next):
        """处理请求，设置超时限制"""
        try:
            response = await asyncio.wait_for(
                call_next(request),
                timeout=self.timeout_seconds
            )
            return response
        except asyncio.TimeoutError:
            logger.warning(f"Request timeout: {request.method} {request.url.path}")
            return JSONResponse(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                content={
                    "code": 504,
                    "message": f"Request timeout after {self.timeout_seconds} seconds",
                    "data": None
                }
            )


class PermissionChecker:
    """基于 API 路径和方法的权限验证器"""

    @staticmethod
    def match_api_path(permission_api: str, request_path: str) -> bool:
        """匹配 API 路径，支持通配符

        示例:
            permission_api="/api/users" 匹配 "/api/users"
            permission_api="/api/*" 匹配 "/api/users"、"/api/devices"
            permission_api="/api/users/*" 匹配 "/api/users/123"
            permission_api="*" 匹配所有路径
        """
        if permission_api == "*":
            return True

        # 将通配符转换为正则表达式
        pattern = permission_api.replace("*", ".*")
        # 确保是完整匹配
        pattern = f"^{pattern}$"

        return bool(re.match(pattern, request_path))

    @staticmethod
    def match_http_method(permission_method: str, request_method: str) -> bool:
        """匹配 HTTP 方法，不区分大小写

        示例:
            permission_method="GET" 匹配 "GET"
            permission_method="get" 匹配 "GET"
            permission_method="*" 匹配所有方法
        """
        if permission_method == "*":
            return True

        return permission_method.lower() == request_method.lower()

    @staticmethod
    def has_permission(
        user_permissions: List[Dict[str, str]],
        request_path: str,
        request_method: str
    ) -> bool:
        """检查用户是否有访问权限

        user_permissions 列表元素格式:
            {"api": "/login", "accessibility": "GET"}
        """
        for perm in user_permissions:
            api = perm.get("api", "")
            method = perm.get("accessibility", "")

            # 检查路径和方法是否都匹配
            if (
                PermissionChecker.match_api_path(api, request_path) and
                PermissionChecker.match_http_method(method, request_method)
            ):
                return True

        return False


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """请求日志中间件"""

    async def dispatch(self, request: Request, call_next: Callable):
        import time

        # 记录请求开始时间
        start_time = time.time()

        # 记录请求信息
        logger.info(
            f"[{request.method}] {request.url.path} - Started from {request.client.host if request.client else 'unknown'}"
        )

        # 处理请求
        response = await call_next(request)

        # 计算请求处理时间
        process_time = time.time() - start_time

        # 记录响应信息
        logger.info(
            f"[{request.method}] {request.url.path} - Status: {response.status_code} - Duration: {process_time:.3f}s"
        )

        # 添加处理时间到响应头
        response.headers["X-Process-Time"] = str(process_time)

        return response


class Permission:
    """权限装饰器和工具类"""

    @staticmethod
    def requires(api_path: str = None, http_method: str = None):
        """权限验证装饰器

        用法:
            @Permission.requires("/login", "GET")
            async def login_endpoint(request: Request):
                ...

            @Permission.requires("/api/users/*", "*")
            async def users_endpoint(request: Request):
                ...
        """
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                request: Request = kwargs.get('request') or args[0] if args else None
                if not request:
                    raise HTTPException(status_code=500, detail="Request object not found")

                # 获取当前用户权限
                user_permissions = getattr(request.state, 'permissions', [])

                # 使用请求的实际路径和方法，如果装饰器没有指定
                target_path = api_path or request.url.path
                target_method = http_method or request.method

                # 检查权限
                if not PermissionChecker.has_permission(user_permissions, target_path, target_method):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Permission denied: {target_method} {target_path}"
                    )

                return await func(*args, **kwargs)
            return wrapper
        return decorator


class RateLimitMiddleware(BaseHTTPMiddleware):
    """简单的基于内存的限流中间件

    注意：生产环境应使用 Redis 等分布式存储
    """

    def __init__(self, app, max_requests: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests = {}

    async def dispatch(self, request: Request, call_next: Callable):
        # 获取客户端标识（使用 IP）
        client_ip = request.client.host if request.client else "unknown"

        # 跳过限流的路径
        skip_paths = ["/health", "/docs", "/openapi.json", "/redoc"]
        if request.url.path in skip_paths or request.url.path.startswith("/api/v1/common"):
            return await call_next(request)

        import time
        current_time = time.time()

        # 清理过期的记录
        self._cleanup_expired(current_time)

        # 检查请求频率
        if self._is_rate_limited(client_ip, current_time):
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "code": 429,
                    "message": "Too many requests, please try again later",
                    "data": None
                }
            )

        # 记录请求
        self._record_request(client_ip, current_time)

        response = await call_next(request)
        return response

    def _cleanup_expired(self, current_time: float):
        """清理过期的请求记录"""
        expired_ips = [
            ip for ip, timestamps in self._requests.items()
            if all(current_time - ts > self.window_seconds for ts in timestamps)
        ]
        for ip in expired_ips:
            del self._requests[ip]

    def _is_rate_limited(self, client_ip: str, current_time: float) -> bool:
        """检查是否超过请求限制"""
        if client_ip not in self._requests:
            return False

        # 获取该 IP 在当前时间窗口内的请求
        recent_requests = [
            ts for ts in self._requests[client_ip]
            if current_time - ts <= self.window_seconds
        ]

        return len(recent_requests) >= self.max_requests

    def _record_request(self, client_ip: str, current_time: float):
        """记录请求"""
        if client_ip not in self._requests:
            self._requests[client_ip] = []
        self._requests[client_ip].append(current_time)


class AuthMiddleware(BaseHTTPMiddleware):
    """认证中间件 - 验证 JWT Token，权限从内存缓存获取"""

    # 不需要认证的路径
    EXEMPT_PATHS = [
        "/",
        "/health",
        "/docs",
        "/openapi.json",
        "/redoc",
        "/api/v1/common",
        "/api/v1/detection/stats",
        "/api/v1/detection/device-status",
        "/api/v1/detection/demo",
        "/api/v1/ws/detection/demo",
        "/api/detection/demo",
        "/api/ws/detection/demo",
        "/ws/detection/demo",
        "/api/ws/",
        "/ws/",
    ]

    def _get_cors_headers(self, request: Request) -> dict:
        """获取CORS响应头"""
        headers = {}
        
        # 检查请求来源
        origin = request.headers.get("origin")
        if origin:
            # 如果来源在允许列表中，设置Access-Control-Allow-Origin
            allowed_origins = server_config.settings.cors_origins
            if allowed_origins == ["*"] or origin in allowed_origins:
                headers["Access-Control-Allow-Origin"] = origin if allowed_origins != ["*"] else "*"
        
        # 设置其他CORS头
        if server_config.settings.cors_allow_credentials:
            headers["Access-Control-Allow-Credentials"] = "true"
        
        headers["Access-Control-Allow-Methods"] = ", ".join(server_config.settings.cors_allow_methods)
        headers["Access-Control-Allow-Headers"] = ", ".join(server_config.settings.cors_allow_headers)
        
        return headers

    async def dispatch(self, request: Request, call_next: Callable):
        # 检查是否是需要认证的路径
        if self._is_exempt(request.url.path):
            request.state.user_id = None
            request.state.role_id = None
            request.state.permissions = []
            return await call_next(request)

        # 获取 Authorization 头
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            # 没有认证信息
            request.state.user_id = None
            request.state.role_id = None
            request.state.permissions = []
            return await call_next(request)

        # 解析 Bearer Token
        try:
            scheme, token = auth_header.split(" ", 1)
            if scheme.lower() != "bearer":
                raise HTTPException(status_code=401, detail="Invalid authentication scheme")

            # 解码 Token
            payload = jwt.decode(
                token,
                server_config.settings.secret_key,
                algorithms=[server_config.settings.algorithm]
            )

            # 从 Token 中提取用户 ID
            user_id = payload.get("user_id")
            if not user_id:
                user_id = payload.get("sub")

            # 从缓存中获取用户权限
            permissions = role_cache.get_user_permissions(user_id)
            role_id = role_cache.get_user_role_id(user_id)

            request.state.user_id = user_id
            request.state.role_id = role_id
            request.state.permissions = permissions

        except JWTError as e:
            logger.error(f"JWTError: {e}")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "code": 401,
                    "message": "Invalid or expired token",
                    "data": None
                },
                headers=self._get_cors_headers(request)
            )
        except ValueError:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "code": 401,
                    "message": "Invalid authorization header format",
                    "data": None
                },
                headers=self._get_cors_headers(request)
            )

        return await call_next(request)

    def _is_exempt(self, path: str) -> bool:
        """检查路径是否免认证"""
        for exempt_path in self.EXEMPT_PATHS:
            if path == exempt_path or path.startswith(exempt_path + "/"):
                return True
        return False


async def get_current_user(request: Request) -> Optional[dict]:
    """获取当前用户信息

    用法:
        @router.get("/protected")
        async def protected_endpoint(user: dict = Depends(get_current_user)):
            if user is None:
                raise HTTPException(status_code=401, detail="Not authenticated")
            return user
    """
    user_id = getattr(request.state, 'user_id', None)
    if user_id is None:
        return None

    return {
        "user_id": user_id,
        "role_id": getattr(request.state, 'role_id', None),
        "permissions": getattr(request.state, 'permissions', [])
    }


async def require_auth(request: Request) -> dict:
    """需要认证的依赖

    用法:
        @router.get("/protected")
        async def protected_endpoint(user: dict = Depends(require_auth)):
            return user
    """
    user = await get_current_user(request)
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user


async def require_permission(request: Request) -> dict:
    """需要权限的依赖 - 验证当前请求的路径和方法

    用法:
        @router.get("/protected/path")
        async def protected_endpoint(user: dict = Depends(require_permission)):
            return user
    """
    user = await require_auth(request)
    permissions = user.get("permissions", [])

    # 检查权限
    if not PermissionChecker.has_permission(permissions, request.url.path, request.method):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission denied: {request.method} {request.url.path}"
        )

    return user

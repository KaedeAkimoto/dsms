from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from pydantic_settings import BaseSettings
from pathlib import Path
import tomllib
import socket
from typing import Optional

# 读取 TOML 配置
_config_path = Path(__file__).parent.parent.parent / "config.toml"
if _config_path.exists():
    with open(_config_path, "rb") as f:
        _config = tomllib.load(f)
else:
    _config = {}


class ServerSettings(BaseSettings):
    """服务器配置类"""
    
    # App Settings
    name: str = _config.get("app", {}).get("name", "DSMS")
    version: str = _config.get("app", {}).get("version", "1.0.0")
    debug: bool = _config.get("app", {}).get("debug", True)
    
    # Server Settings
    host: str = _config.get("server", {}).get("host", "0.0.0.0")
    port: int = _config.get("server", {}).get("port", 8000)
    request_timeout_seconds: int = _config.get("server", {}).get("request_timeout_seconds", 30)
    
    # CORS Settings
    cors_origins: list = _config.get("cors", {}).get("origins", ["http://localhost:5173", "http://127.0.0.1:5173"])
    cors_allow_credentials: bool = _config.get("cors", {}).get("allow_credentials", True)
    cors_allow_methods: list = _config.get("cors", {}).get("allow_methods", ["*"])
    cors_allow_headers: list = _config.get("cors", {}).get("allow_headers", ["*"])
    
    # Security Settings
    secret_key: str = _config.get("security", {}).get("secret_key", "your-secret-key-here-change-in-production")
    algorithm: str = _config.get("security", {}).get("algorithm", "HS256")
    access_token_expire_minutes: int = _config.get("security", {}).get("access_token_expire_minutes", 30)
    
    # Rate Limit Settings
    rate_limit_max_requests: int = _config.get("rate_limit", {}).get("max_requests", 100)
    rate_limit_window_seconds: int = _config.get("rate_limit", {}).get("window_seconds", 60)
    
    # File Upload Settings
    max_upload_size: int = _config.get("upload", {}).get("max_size", 10485760)
    allowed_image_types: list = _config.get("upload", {}).get("allowed_image_types", ["image/jpeg", "image/png", "image/jpg"])
    
    # User Settings
    default_title_id: int = _config.get("user", {}).get("default_title_id", 9)


class ServerConfig:
    """服务器配置管理类"""
    
    def __init__(self):
        self.settings = ServerSettings()
        self._app = None
        self._effective_port = None
    
    def is_port_available(self, host: str, port: int) -> bool:
        """
        检查端口是否可用
        
        Args:
            host: 主机地址
            port: 端口号
            
        Returns:
            如果端口可用返回True，否则返回False
        """
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.5)
                s.connect((host, port))
            return False
        except (ConnectionRefusedError, socket.timeout):
            return True
        except Exception:
            return True
    
    def find_available_port(self, host: str, start_port: int, max_tries: int = 100) -> Optional[int]:
        """
        从起始端口开始查找可用的端口
        
        Args:
            host: 主机地址
            start_port: 起始端口
            max_tries: 最大尝试次数
            
        Returns:
            找到的可用端口，如果找不到返回None
        """
        for port in range(start_port, start_port + max_tries):
            if self.is_port_available(host, port):
                return port
        return None
    
    def get_effective_port(self) -> int:
        """
        获取实际可用的端口
        
        如果配置的端口被占用，会自动查找下一个可用端口
        
        Returns:
            可用的端口号
        """
        if self._effective_port is not None:
            return self._effective_port
        
        host = self.settings.host
        port = self.settings.port
        
        if not self.is_port_available(host, port):
            print(f"⚠️  端口 {port} 已被占用，正在查找可用端口...")
            available_port = self.find_available_port(host, port + 1)
            
            if available_port is not None:
                self._effective_port = available_port
                print(f"✅ 找到可用端口: {available_port}")
            else:
                print(f"❌ 无法找到可用端口 (尝试了 {port+1} 到 {port+100})")
                print(f"   请手动指定其他端口或关闭占用端口的程序")
                import sys
                sys.exit(1)
        else:
            self._effective_port = port
        
        return self._effective_port
    
    @property
    def app(self) -> FastAPI:
        """获取 FastAPI 应用实例"""
        if self._app is None:
            self._app = self._create_app()
        return self._app
    
    def _create_app(self) -> FastAPI:
        """创建 FastAPI 应用实例"""
        app = FastAPI(
            title=self.settings.name,
            version=self.settings.version,
            debug=self.settings.debug,
            docs_url="/docs" if self.settings.debug else None,
            redoc_url="/redoc" if self.settings.debug else None,
            openapi_url="/openapi.json" if self.settings.debug else None,
        )
        
        self._add_middlewares(app)
        self._add_exception_handlers(app)
        
        return app
    
    def _add_middlewares(self, app: FastAPI):
        """添加中间件"""

        # Timeout Middleware (first, outermost) - 使用配置的请求超时时间
        from app.core.middlewares import TimeoutMiddleware
        app.add_middleware(TimeoutMiddleware, timeout_seconds=self.settings.request_timeout_seconds)

        # Request Logging Middleware (first, outermost)
        from app.core.middlewares import RequestLoggingMiddleware
        app.add_middleware(RequestLoggingMiddleware)

        # Rate Limit Middleware
        from app.core.middlewares import RateLimitMiddleware
        app.add_middleware(
            RateLimitMiddleware,
            max_requests=self.settings.rate_limit_max_requests,
            window_seconds=self.settings.rate_limit_window_seconds
        )

        # Auth Middleware
        from app.core.middlewares import AuthMiddleware
        app.add_middleware(AuthMiddleware)

        # CORS Middleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=self.settings.cors_origins,
            allow_credentials=self.settings.cors_allow_credentials,
            allow_methods=self.settings.cors_allow_methods,
            allow_headers=self.settings.cors_allow_headers,
        )

        # GZip Middleware
        app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    def _add_exception_handlers(self, app: FastAPI):
        """添加异常处理器"""
        from fastapi import Request, status
        from fastapi.responses import JSONResponse
        from fastapi.exceptions import RequestValidationError
        from starlette.exceptions import HTTPException as StarletteHTTPException
        
        # HTTP Exception Handler
        @app.exception_handler(StarletteHTTPException)
        async def http_exception_handler(request: Request, exc: StarletteHTTPException):
            return JSONResponse(
                status_code=exc.status_code,
                content={
                    "code": exc.status_code,
                    "message": exc.detail,
                    "data": None
                }
            )
        
        # Validation Exception Handler
        @app.exception_handler(RequestValidationError)
        async def validation_exception_handler(request: Request, exc: RequestValidationError):
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content={
                    "code": status.HTTP_422_UNPROCESSABLE_ENTITY,
                    "message": "Validation error",
                    "data": exc.errors()
                }
            )
        
        # Global Exception Handler
        @app.exception_handler(Exception)
        async def global_exception_handler(request: Request, exc: Exception):
            import traceback
            
            # 记录异常日志
            if self.settings.debug:
                error_detail = str(exc)
                traceback_str = traceback.format_exc()
            else:
                error_detail = "Internal server error"
                traceback_str = None
            
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "message": error_detail,
                    "data": {"traceback": traceback_str} if traceback_str else None
                }
            )
    
    def include_router(self, router, prefix: str = "", tags: list = None):
        """添加路由"""
        self.app.include_router(router, prefix=prefix, tags=tags or [])
    
    def startup(self):
        """应用启动事件"""
        from app.config.database import db_config
        
        @asynccontextmanager
        async def lifespan(app: FastAPI):
            """应用生命周期管理"""
            # 启动事件
            print(f"Starting {self.settings.name} v{self.settings.version}")
            print(f"Debug mode: {self.settings.debug}")
            print(f"Rate limit: {self.settings.rate_limit_max_requests} requests per {self.settings.rate_limit_window_seconds} seconds")
            
            # Initialize database
            try:
                await db_config.async_init_db()
                print("Database initialized successfully")
            except Exception as e:
                print(f"Database initialization failed: {e}")
            
            # Load role cache
            try:
                from app.core.role_cache import role_cache
                role_cache.load()
                print(f"Role cache loaded: {role_cache.roles_count} roles, {role_cache.user_roles_count} user-role mappings")
            except Exception as e:
                print(f"Role cache loading failed: {e}")

            # Start audit log writer
            try:
                from app.services.audit_log import audit_log_writer
                audit_log_writer.start()
                print("Audit log writer started")
            except Exception as e:
                print(f"Audit log writer start failed: {e}")

            yield

            # 关闭事件
            print("Shutting down application...")

            # Stop audit log writer
            try:
                from app.services.audit_log import audit_log_writer
                audit_log_writer.stop()
                print("Audit log writer stopped")
            except Exception as e:
                print(f"Audit log writer stop failed: {e}")

            db_config.close()
            print("Application shutdown complete")

        # 将 lifespan 传递给 FastAPI 应用
        self._app = self._create_app_with_lifespan(lifespan)
    
    def _create_app_with_lifespan(self, lifespan) -> FastAPI:
        """创建带有生命周期管理的 FastAPI 应用实例"""
        from contextlib import asynccontextmanager
        
        app = FastAPI(
            title=self.settings.name,
            version=self.settings.version,
            debug=self.settings.debug,
            docs_url="/docs" if self.settings.debug else None,
            redoc_url="/redoc" if self.settings.debug else None,
            openapi_url="/openapi.json" if self.settings.debug else None,
            lifespan=lifespan,
        )
        
        self._add_middlewares(app)
        self._add_exception_handlers(app)
        
        return app
    
    def startup(self):
        """应用启动事件（已弃用，使用 lifespan 替代）"""
        pass
    
    def shutdown(self):
        """应用关闭事件（已弃用，使用 lifespan 替代）"""
        pass
        async def startup_event():
            """启动事件"""
            print(f"Starting {self.settings.name} v{self.settings.version}")
            print(f"Debug mode: {self.settings.debug}")
            print(f"Rate limit: {self.settings.rate_limit_max_requests} requests per {self.settings.rate_limit_window_seconds} seconds")
            
            # Initialize database
            try:
                await db_config.async_init_db()
                print("Database initialized successfully")
            except Exception as e:
                print(f"Database initialization failed: {e}")
            
            # Load role cache
            try:
                from app.core.role_cache import role_cache
                role_cache.load()
                print(f"Role cache loaded: {role_cache.roles_count} roles, {role_cache.user_roles_count} user-role mappings")
            except Exception as e:
                print(f"Role cache loading failed: {e}")

            # Start audit log writer
            try:
                from app.services.audit_log import audit_log_writer
                audit_log_writer.start()
                print("Audit log writer started")
            except Exception as e:
                print(f"Audit log writer start failed: {e}")
    
    def shutdown(self):
        """应用关闭事件"""
        from app.config.database import db_config

        @self.app.on_event("shutdown")
        async def shutdown_event():
            """关闭事件"""
            print("Shutting down application...")

            # Stop audit log writer
            try:
                from app.services.audit_log import audit_log_writer
                audit_log_writer.stop()
                print("Audit log writer stopped")
            except Exception as e:
                print(f"Audit log writer stop failed: {e}")

            db_config.close()
            print("Application shutdown complete")


# 全局服务器配置实例
server_config = ServerConfig()


def get_app() -> FastAPI:
    """获取 FastAPI 应用实例"""
    return server_config.app

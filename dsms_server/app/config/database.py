from typing import AsyncGenerator
from contextlib import contextmanager
from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from pydantic_settings import BaseSettings
from pathlib import Path
import tomllib

# 读取 TOML 配置
_config_path = Path(__file__).parent.parent.parent / "config.toml"
if _config_path.exists():
    with open(_config_path, "rb") as f:
        _config = tomllib.load(f)
else:
    _config = {}


class DatabaseSettings(BaseSettings):
    """数据库配置类"""
    
    url: str = _config.get("database", {}).get("url", "postgresql://postgres:postgres@localhost:5432/dsms_db")
    pool_size: int = _config.get("database", {}).get("pool_size", 10)
    max_overflow: int = _config.get("database", {}).get("max_overflow", 20)


class DatabaseConfig:
    """数据库配置管理类"""
    
    def __init__(self):
        self.settings = DatabaseSettings()
        self._engine = None
        self._async_engine = None
        self._session_factory = None
        self._async_session_factory = None
    
    @property
    def engine(self):
        """获取同步数据库引擎"""
        if self._engine is None:
            self._engine = create_engine(
                self.settings.url,
                pool_size=self.settings.pool_size,
                max_overflow=self.settings.max_overflow,
                echo=False
            )
        return self._engine
    
    @property
    def async_engine(self):
        """获取异步数据库引擎"""
        if self._async_engine is None:
            async_url = self.settings.url.replace("postgresql://", "postgresql+asyncpg://")
            self._async_engine = create_async_engine(
                async_url,
                pool_size=self.settings.pool_size,
                max_overflow=self.settings.max_overflow,
                echo=False
            )
        return self._async_engine
    
    @property
    def session_factory(self):
        """获取同步会话工厂"""
        if self._session_factory is None:
            self._session_factory = sessionmaker(
                bind=self.engine,
                autocommit=False,
                autoflush=False,
                expire_on_commit=False
            )
        return self._session_factory
    
    @property
    def async_session_factory(self):
        """获取异步会话工厂"""
        if self._async_session_factory is None:
            self._async_session_factory = async_sessionmaker(
                bind=self.async_engine,
                class_=AsyncSession,
                autocommit=False,
                autoflush=False,
                expire_on_commit=False
            )
        return self._async_session_factory
    
    @contextmanager
    def get_session(self) -> Session:
        """获取同步数据库会话"""
        session = self.session_factory()
        try:
            yield session
        finally:
            session.close()
    
    async def get_async_session(self) -> AsyncGenerator[AsyncSession, None]:
        """获取异步数据库会话"""
        async with self.async_session_factory() as session:
            yield session
    
    def init_db(self):
        """初始化数据库表"""
        SQLModel.metadata.create_all(self.engine)
    
    async def async_init_db(self):
        """异步初始化数据库表"""
        async with self.async_engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)
    
    def close(self):
        """关闭数据库连接"""
        if self._engine:
            self._engine.dispose()
        if self._async_engine:
            try:
                import asyncio
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(self._async_engine.dispose())
                else:
                    loop.run_until_complete(self._async_engine.dispose())
            except Exception:
                pass


# 全局数据库配置实例
db_config = DatabaseConfig()


def get_db():
    """依赖注入: 获取数据库会话"""
    return db_config.get_session()


async def get_async_db():
    """依赖注入: 获取异步数据库会话"""
    async for session in db_config.get_async_session():
        yield session

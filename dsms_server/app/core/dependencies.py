from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlmodel import Session
from app.config.database import get_async_db
from app.config.server import server_config

security = HTTPBearer()


async def get_db() -> Generator:
    """获取数据库会话依赖"""
    async for session in get_async_db():
        yield session


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[dict]:
    """获取当前用户依赖
    
    Args:
        credentials: HTTP Bearer 认证凭证
        db: 数据库会话
    
    Returns:
        当前用户信息
    
    Raises:
        HTTPException: 认证失败时抛出异常
    """
    from jose import JWTError, jwt
    
    try:
        payload = jwt.decode(
            credentials.credentials,
            server_config.settings.secret_key,
            algorithms=[server_config.settings.algorithm]
        )
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
    
    return {"user_id": user_id}

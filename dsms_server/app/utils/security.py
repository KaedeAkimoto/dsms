from datetime import datetime, timedelta
from typing import Optional, Dict
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.config.server import server_config

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """加密密码
    
    Args:
        password: 原始密码
    
    Returns:
        加密后的密码
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码
    
    Args:
        plain_password: 原始密码
        hashed_password: 加密后的密码
    
    Returns:
        验证结果
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: Dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建访问令牌
    
    Args:
        data: 要编码的数据
        expires_delta: 过期时间增量
    
    Returns:
        JWT 令牌
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=server_config.settings.access_token_expire_minutes)
    
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(
        to_encode,
        server_config.settings.secret_key,
        algorithm=server_config.settings.algorithm
    )
    
    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict]:
    """解码访问令牌
    
    Args:
        token: JWT 令牌
    
    Returns:
        解码后的数据
    
    Raises:
        JWTError: 令牌无效时抛出异常
    """
    try:
        payload = jwt.decode(
            token,
            server_config.settings.secret_key,
            algorithms=[server_config.settings.algorithm]
        )
        return payload
    except JWTError:
        return None

from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from pydantic import BaseModel
from app.config.server import server_config

SECRET_KEY = server_config.settings.secret_key
ALGORITHM = server_config.settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = server_config.settings.access_token_expire_minutes


class TokenData(BaseModel):
    """Token数据"""
    user_id: str
    user_name: str
    role_id: int
    exp: Optional[datetime] = None


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建访问令牌"""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[TokenData]:
    """解码令牌"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("user_id")
        user_name: str = payload.get("user_name")
        role_id: int = payload.get("role_id")

        if user_id is None or user_name is None:
            return None

        return TokenData(user_id=user_id, user_name=user_name, role_id=role_id)
    except JWTError:
        return None

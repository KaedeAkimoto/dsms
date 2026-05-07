from typing import Dict, List, Optional
from sqlmodel import select
from app.config.database import db_config
from app.models import Role, User
from app.utils.logger import get_logger
import threading

logger = get_logger(__name__)


class RoleCache:
    """角色权限缓存类

    在应用启动时加载所有角色数据到内存，之后权限验证直接从内存获取。
    当角色数据被修改时，调用 reload() 方法重新加载。
    """
    
    _instance: Optional["RoleCache"] = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._roles: Dict[str, Dict] = {}
        self._user_roles: Dict[str, str] = {}
        self._initialized = True
        logger.info("RoleCache instance created")
        self.load()
    
    def load(self) -> None:
        """从数据库加载所有角色数据"""
        try:
            with db_config.get_session() as session:
                # 加载所有角色
                roles_result = session.execute(select(Role))
                roles = roles_result.scalars().all()
                
                self._roles.clear()
                for role in roles:
                    role_dict = {
                        "role_id": str(role.role_id),
                        "role_name": role.role_name,
                        "permissions": role.permissions or []
                    }
                    self._roles[str(role.role_id)] = role_dict
                
                # 加载所有用户的角色映射
                users_result = session.execute(select(User))
                users = users_result.scalars().all()
                
                self._user_roles.clear()
                for user in users:
                    if user.role_id:
                        self._user_roles[str(user.user_id)] = str(user.role_id)
                
                logger.info(f"RoleCache loaded: {len(self._roles)} roles, {len(self._user_roles)} user-role mappings")
                
        except Exception as e:
            logger.error(f"Failed to load RoleCache: {e}")
            raise
    
    def get_role_permissions(self, role_id: str) -> List[Dict[str, str]]:
        """获取角色的权限列表"""
        role = self._roles.get(str(role_id))
        if role:
            return role.get("permissions", [])
        return []
    
    def get_user_permissions(self, user_id: str) -> List[Dict[str, str]]:
        """获取用户的权限列表（通过角色）"""
        role_id = self._user_roles.get(str(user_id))
        if role_id:
            return self.get_role_permissions(role_id)
        return []
    
    def get_user_role_id(self, user_id: str) -> Optional[str]:
        """获取用户的角色ID"""
        return self._user_roles.get(str(user_id))
    
    def get_role_by_id(self, role_id: str) -> Optional[Dict]:
        """获取角色信息"""
        return self._roles.get(str(role_id))
    
    def get_role_id_by_name(self, role_name: str) -> Optional[str]:
        """根据角色名称获取角色ID"""
        for role_id, role_data in self._roles.items():
            if role_data.get("role_name") == role_name:
                return role_id
        return None
    
    def reload(self) -> None:
        """重新从数据库加载角色数据"""
        logger.info("Reloading RoleCache...")
        self.load()
    
    @property
    def roles_count(self) -> int:
        """获取缓存的角色数量"""
        return len(self._roles)
    
    @property
    def user_roles_count(self) -> int:
        """获取缓存的用户-角色映射数量"""
        return len(self._user_roles)


# 全局单例
role_cache = RoleCache()

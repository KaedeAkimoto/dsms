from typing import Optional, List
from uuid import UUID, uuid4
from datetime import datetime, timezone
import bcrypt
from sqlmodel import select
from app.config.database import db_config
from app.models import User, Role
from app.core.role_cache import role_cache
from app.core.system_roles import SystemRole
from app.utils.logger import get_logger

logger = get_logger(__name__)

# 从配置读取默认职称ID
from app.config.server import server_config
REGISTERED_EMPLOYEE_TITLE_ID = server_config.settings.default_title_id


class UserService:
    """用户服务类"""

    @staticmethod
    def hash_password(password: str) -> str:
        """密码哈希"""
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode('utf-8')

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        password_bytes = plain_password.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hashed_bytes)

    @staticmethod
    def generate_employee_id() -> str:
        """生成工号"""
        import random
        import string
        timestamp = datetime.now().strftime("%Y%m%d")
        random_str = ''.join(random.choices(string.digits, k=4))
        return f"EMP{timestamp}{random_str}"

    def get_user_by_username(self, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        with db_config.get_session() as session:
            result = session.execute(
                select(User).where(User.user_name == username)
            )
            return result.scalars().first()

    def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        """根据用户ID获取用户"""
        with db_config.get_session() as session:
            result = session.execute(
                select(User).where(User.user_id == user_id)
            )
            return result.scalars().first()

    def get_user_by_employee_id(self, employee_id: str) -> Optional[User]:
        """根据工号获取用户"""
        with db_config.get_session() as session:
            result = session.execute(
                select(User).where(User.employee_id == employee_id)
            )
            return result.scalars().first()

    def create_user(
        self,
        user_name: str,
        password: str,
        real_name: str,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        employee_id: Optional[str] = None,
        department_id: Optional[int] = None,
        title_id: int = REGISTERED_EMPLOYEE_TITLE_ID
    ) -> Optional[User]:
        """创建用户（默认分配注册员工职称和无权限角色）"""
        if self.get_user_by_username(user_name):
            logger.warning(f"User already exists: {user_name}")
            return None

        if employee_id and self.get_user_by_employee_id(employee_id):
            logger.warning(f"Employee ID already exists: {employee_id}")
            return None

        if not employee_id:
            employee_id = self.generate_employee_id()

        no_permission_role_id = self._get_no_permission_role_id()

        with db_config.get_session() as session:
            user = User(
                user_id=uuid4(),
                user_name=user_name,
                password_hash=self.hash_password(password),
                real_name=real_name,
                email=email,
                phone=phone,
                employee_id=employee_id,
                department_id=department_id,
                title_id=title_id,
                role_id=no_permission_role_id
            )
            session.add(user)
            session.commit()
            session.refresh(user)

            role_cache.reload()

            logger.info(f"User created successfully: {user_name}")
            return user

    def _get_no_permission_role_id(self) -> int:
        """获取无权限用户的角色ID"""
        with db_config.get_session() as session:
            result = session.execute(
                select(Role).where(Role.role_name == SystemRole.ROLE_NAMES[SystemRole.NO_PERMISSION_USER])
            )
            role = result.scalar_one_or_none()
            if role:
                return role.role_id
            logger.error(f"Role '{SystemRole.ROLE_NAMES[SystemRole.NO_PERMISSION_USER]}' not found in database")
            return 1

    def authenticate(self, username: str, password: str) -> Optional[User]:
        """用户认证"""
        user = self.get_user_by_username(username)
        if not user:
            return None

        if not self.verify_password(password, user.password_hash):
            return None

        with db_config.get_session() as session:
            result = session.execute(
                select(User).where(User.user_id == user.user_id)
            )
            user = result.scalars().first()
            user.last_login = datetime.now(timezone.utc)
            session.commit()

        return user

    def get_all_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """获取所有用户"""
        with db_config.get_session() as session:
            result = session.execute(
                select(User).offset(skip).limit(limit)
            )
            return list(result.scalars().all())

    def count_users(self) -> int:
        """统计用户数量"""
        with db_config.get_session() as session:
            result = session.execute(select(User))
            return len(result.scalars().all())

    def update_user(
        self,
        user_id: UUID,
        real_name: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        department_id: Optional[int] = None,
        title_id: Optional[int] = None,
        role_id: Optional[int] = None,
        avatar_url: Optional[str] = None
    ) -> Optional[User]:
        """更新用户信息"""
        with db_config.get_session() as session:
            result = session.execute(
                select(User).where(User.user_id == user_id)
            )
            user = result.scalars().first()
            
            if not user:
                return None

            if real_name:
                user.real_name = real_name
            if email:
                user.email = email
            if phone:
                user.phone = phone
            if department_id is not None:
                user.department_id = department_id
            if title_id is not None:
                user.title_id = title_id
            if role_id is not None:
                user.role_id = role_id
            if avatar_url is not None:
                user.avatar_url = avatar_url

            session.commit()
            session.refresh(user)

            role_cache.reload()

            logger.info(f"User updated successfully: {user.user_id}")
            return user

    def change_password(self, user_id: UUID, old_password: str, new_password: str) -> bool:
        """修改密码"""
        with db_config.get_session() as session:
            result = session.execute(
                select(User).where(User.user_id == user_id)
            )
            user = result.scalars().first()

            if not user:
                return False

            if not self.verify_password(old_password, user.password_hash):
                return False

            user.password_hash = self.hash_password(new_password)
            session.commit()

            logger.info(f"Password changed successfully for user: {user.user_id}")
            return True

    def delete_user(self, user_id: UUID) -> bool:
        """删除用户 - 将用户角色改为无权限用户（离职）"""
        with db_config.get_session() as session:
            result = session.execute(
                select(User).where(User.user_id == user_id)
            )
            user = result.scalars().first()

            if not user:
                return False

            no_permission_role_id = self._get_no_permission_role_id()
            user.role_id = no_permission_role_id
            session.add(user)
            session.commit()

            role_cache.reload()

            logger.info(f"User deactivated (set to no permission role): {user_id}")
            return True

    def batch_create_users(
        self,
        users_data: list,
        default_role_id: Optional[int] = None
    ) -> dict:
        """批量创建用户"""
        success_users = []
        failed_users = []

        # 如果没有提供默认角色ID，从角色缓存获取"无权限用户"角色
        if default_role_id is None:
            from app.core.role_cache import role_cache
            no_permission_role_id = role_cache.get_role_id_by_name("无权限用户")
            if no_permission_role_id:
                default_role_id = int(no_permission_role_id)
            else:
                raise ValueError('无法获取默认角色ID：角色缓存中未找到"无权限用户"角色')

        with db_config.get_session() as session:
            for i, user_data in enumerate(users_data):
                try:
                    username = user_data.get('user_name')
                    password = user_data.get('password')
                    real_name = user_data.get('real_name')
                    email = user_data.get('email')
                    phone = user_data.get('phone')
                    employee_id = user_data.get('employee_id')
                    department_id = user_data.get('department_id')
                    title_id = user_data.get('title_id', REGISTERED_EMPLOYEE_TITLE_ID)

                    # 检查用户名是否已存在
                    existing_user = session.execute(
                        select(User).where(User.user_name == username)
                    ).scalars().first()
                    if existing_user:
                        failed_users.append({
                            'index': i,
                            'user_name': username,
                            'reason': '用户名已存在'
                        })
                        continue

                    # 检查工号是否已存在（如果提供了）
                    if employee_id:
                        existing_emp = session.execute(
                            select(User).where(User.employee_id == employee_id)
                        ).scalars().first()
                        if existing_emp:
                            failed_users.append({
                                'index': i,
                                'user_name': username,
                                'reason': '工号已存在'
                            })
                            continue

                    if not employee_id:
                        employee_id = self.generate_employee_id()

                    user = User(
                        user_id=uuid4(),
                        user_name=username,
                        password_hash=self.hash_password(password),
                        real_name=real_name,
                        email=email,
                        phone=phone,
                        employee_id=employee_id,
                        department_id=department_id,
                        title_id=title_id,
                        role_id=default_role_id
                    )
                    session.add(user)

                    # 刷新以获取完整数据
                    session.flush()
                    session.refresh(user)
                    success_users.append(user)

                except Exception as e:
                    failed_users.append({
                        'index': i,
                        'user_name': user_data.get('user_name'),
                        'reason': str(e)
                    })
                    logger.error(f"Failed to create user {user_data.get('user_name')}: {e}")

            session.commit()
            role_cache.reload()

        logger.info(f"Batch create users completed: {len(success_users)} success, {len(failed_users)} failed")

        return {
            'success_count': len(success_users),
            'failed_count': len(failed_users),
            'success_users': success_users,
            'failed_users': failed_users
        }

    def get_users_by_department(self, department_id: int, skip: int = 0, limit: int = 100) -> List[User]:
        """根据部门ID获取用户列表"""
        with db_config.get_session() as session:
            result = session.execute(
                select(User).where(User.department_id == department_id).offset(skip).limit(limit)
            )
            return list(result.scalars().all())

    def count_users_by_department(self, department_id: int) -> int:
        """统计部门用户数量"""
        with db_config.get_session() as session:
            result = session.execute(
                select(User).where(User.department_id == department_id)
            )
            return len(result.scalars().all())

    def get_users_by_title(self, title_id: int, skip: int = 0, limit: int = 100) -> List[User]:
        """根据职称ID获取用户列表"""
        with db_config.get_session() as session:
            result = session.execute(
                select(User).where(User.title_id == title_id).offset(skip).limit(limit)
            )
            return list(result.scalars().all())

    def count_users_by_title(self, title_id: int) -> int:
        """统计职称用户数量"""
        with db_config.get_session() as session:
            result = session.execute(
                select(User).where(User.title_id == title_id)
            )
            return len(result.scalars().all())

    def get_users_by_role(self, role_id: int, skip: int = 0, limit: int = 100) -> List[User]:
        """根据角色ID获取用户列表"""
        with db_config.get_session() as session:
            result = session.execute(
                select(User).where(User.role_id == role_id).offset(skip).limit(limit)
            )
            return list(result.scalars().all())

    def count_users_by_role(self, role_id: int) -> int:
        """统计角色用户数量"""
        with db_config.get_session() as session:
            result = session.execute(
                select(User).where(User.role_id == role_id)
            )
            return len(result.scalars().all())

    def search_users(self, keyword: str, skip: int = 0, limit: int = 100) -> List[User]:
        """按用户名/姓名/工号模糊搜索用户"""
        with db_config.get_session() as session:
            result = session.execute(
                select(User).where(
                    (User.user_name.like(f"%{keyword}%")) |
                    (User.real_name.like(f"%{keyword}%")) |
                    (User.employee_id.like(f"%{keyword}%"))
                ).offset(skip).limit(limit)
            )
            return list(result.scalars().all())

    def count_search_users(self, keyword: str) -> int:
        """统计搜索结果数量"""
        with db_config.get_session() as session:
            result = session.execute(
                select(User).where(
                    (User.user_name.like(f"%{keyword}%")) |
                    (User.real_name.like(f"%{keyword}%")) |
                    (User.employee_id.like(f"%{keyword}%"))
                )
            )
            return len(result.scalars().all())


user_service = UserService()

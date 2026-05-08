#!/usr/bin/env python3
"""
数据库初始化脚本

功能说明:
    - clear: 清空数据库所有数据
    - init: 初始化所有基础数据（职称、部门、缺陷类型）
    - init-roles: 初始化系统角色
    - init-admin: 创建超级管理员
    - all: 执行完整初始化（清空+初始化+角色+管理员）

使用示例:
    python init_all.py clear      # 清空数据库
    python init_all.py init       # 初始化基础数据
    python init_all.py init-roles # 初始化角色
    python init_all.py init-admin # 创建管理员
    python init_all.py all        # 完整初始化（推荐）

注意:
    1. 确保已正确配置 config.toml 中的数据库连接信息
    2. 运行前确保 PostgreSQL 服务已启动
    3. 完整初始化会清空所有数据，请谨慎操作
"""

import sys
import bcrypt
import logging
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config.database import db_config
from app.models import Title, Department, DefectType, Role, User
from app.core.system_roles import get_all_system_roles, get_default_permissions, SystemRole
from sqlmodel import select
from sqlalchemy import text

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class DatabaseInitializer:
    """数据库初始化器"""

    DEFAULT_TITLES = [
        {"title_id": 1, "title_name": "高级工程师"},
        {"title_id": 2, "title_name": "工程师"},
        {"title_id": 3, "title_name": "助理工程师"},
        {"title_id": 4, "title_name": "技术员"},
        {"title_id": 5, "title_name": "管理员"},
        {"title_id": 6, "title_name": "主管"},
        {"title_id": 7, "title_name": "经理"},
        {"title_id": 8, "title_name": "总监"},
        {"title_id": 9, "title_name": "注册员工"},
        {"title_id": 10, "title_name": "离职员工"},
        {"title_id": 11, "title_name": "非正式员工"},
    ]

    DEFAULT_DEPARTMENTS = [
        {"department_id": 1, "department_code": "HQ", "department_name": "总部", "parent_id": None},
        {"department_id": 2, "department_code": "IT", "department_name": "信息技术部", "parent_id": 1},
        {"department_id": 3, "department_code": "HR", "department_name": "人力资源部", "parent_id": 1},
        {"department_id": 4, "department_code": "FIN", "department_name": "财务部", "parent_id": 1},
        {"department_id": 5, "department_code": "OP", "department_name": "运营部", "parent_id": 1},
        {"department_id": 6, "department_code": "QA", "department_name": "质量部", "parent_id": 1},
    ]

    DEFAULT_DEFECT_TYPES = [
        {"defect_type_id": 1, "defect_type_name": "锈蚀"},
        {"defect_type_id": 2, "defect_type_name": "毛刺"},
        {"defect_type_id": 3, "defect_type_name": "裂纹"},
        {"defect_type_id": 4, "defect_type_name": "划痕"},
        {"defect_type_id": 5, "defect_type_name": "凹痕"},
        {"defect_type_id": 6, "defect_type_name": "磨损"},
    ]

    ADMIN_USERNAME = "admin"
    ADMIN_PASSWORD = "admin123"
    ADMIN_REAL_NAME = "超级管理员"
    ADMIN_EMAIL = "admin@example.com"
    ADMIN_PHONE = "13800138000"

    def __init__(self):
        db_config.init_db()

    def get_all_table_names(self):
        """获取所有表名"""
        with db_config.engine.connect() as conn:
            result = conn.execute(text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'"))
            return [row[0] for row in result]

    def clear_database(self):
        """清空数据库所有数据"""
        logger.info("=" * 50)
        logger.info("开始清空数据库...")
        logger.info("=" * 50)

        for table_name in self.get_all_table_names():
            with db_config.engine.connect() as conn:
                conn.execute(text(f"TRUNCATE TABLE {table_name} CASCADE"))
            logger.info(f"  已清空表: {table_name}")

        logger.info("=" * 50)
        logger.info("数据库清空完成!")
        logger.info("=" * 50)

    def init_base_data(self):
        """初始化基础数据（职称、部门、缺陷类型）"""
        logger.info("=" * 50)
        logger.info("开始初始化基础数据...")
        logger.info("=" * 50)

        with db_config.get_session() as session:
            logger.info("初始化职称数据...")
            for title_data in self.DEFAULT_TITLES:
                result = session.execute(select(Title).where(Title.title_id == title_data["title_id"]))
                existing = result.scalar_one_or_none()
                if existing:
                    existing.title_name = title_data["title_name"]
                    logger.info(f"  更新职称: {title_data['title_name']}")
                else:
                    title = Title(title_id=title_data["title_id"], title_name=title_data["title_name"])
                    session.add(title)
                    logger.info(f"  创建职称: {title_data['title_name']}")

            logger.info("初始化部门数据...")
            for dept_data in self.DEFAULT_DEPARTMENTS:
                result = session.execute(select(Department).where(Department.department_id == dept_data["department_id"]))
                existing = result.scalar_one_or_none()
                if existing:
                    existing.department_code = dept_data["department_code"]
                    existing.department_name = dept_data["department_name"]
                    existing.parent_id = dept_data["parent_id"]
                    logger.info(f"  更新部门: {dept_data['department_name']}")
                else:
                    dept = Department(
                        department_id=dept_data["department_id"],
                        department_code=dept_data["department_code"],
                        department_name=dept_data["department_name"],
                        parent_id=dept_data["parent_id"]
                    )
                    session.add(dept)
                    logger.info(f"  创建部门: {dept_data['department_name']}")

            logger.info("初始化缺陷类型数据...")
            for defect_data in self.DEFAULT_DEFECT_TYPES:
                result = session.execute(select(DefectType).where(DefectType.defect_type_id == defect_data["defect_type_id"]))
                existing = result.scalar_one_or_none()
                if existing:
                    existing.defect_type_name = defect_data["defect_type_name"]
                    logger.info(f"  更新缺陷类型: {defect_data['defect_type_name']}")
                else:
                    defect = DefectType(
                        defect_type_id=defect_data["defect_type_id"],
                        defect_type_name=defect_data["defect_type_name"]
                    )
                    session.add(defect)
                    logger.info(f"  创建缺陷类型: {defect_data['defect_type_name']}")

            session.commit()

        logger.info("=" * 50)
        logger.info("基础数据初始化完成!")
        logger.info("=" * 50)

    def init_system_roles(self):
        """初始化系统角色"""
        logger.info("=" * 50)
        logger.info("开始初始化系统角色...")
        logger.info("=" * 50)

        with db_config.get_session() as session:
            existing_roles = session.execute(select(Role).where(Role.is_system_role == True)).scalars().all()

            if existing_roles:
                logger.info(f"发现 {len(existing_roles)} 个现有系统角色，正在清空...")
                old_role_ids = [r.role_id for r in existing_roles]

                temp_role_name = f"_temp_role_{uuid4().hex[:8]}"
                temp_role = Role(
                    role_name=temp_role_name,
                    desc="Temporary role for migration",
                    is_system_role=False,
                    permissions=[]
                )
                session.add(temp_role)
                session.flush()
                temp_role_id = temp_role.role_id

                for old_id in old_role_ids:
                    session.execute(
                        text("UPDATE users SET role_id = :new_id WHERE role_id = :old_id"),
                        {"new_id": temp_role_id, "old_id": old_id}
                    )

                for old_role in existing_roles:
                    session.delete(old_role)

                session.commit()
                logger.info(f"已清空 {len(existing_roles)} 个系统角色")

            logger.info("插入系统角色...")
            for role_info in get_all_system_roles():
                role_name = role_info["role_name"]
                role = Role(
                    role_name=role_name,
                    desc=role_info["description"],
                    is_system_role=True,
                    permissions=get_default_permissions(role_info["role_key"])
                )
                session.add(role)
                logger.info(f"  创建角色: {role_name}")

            session.commit()

        logger.info("=" * 50)
        logger.info("系统角色初始化完成!")
        logger.info("=" * 50)

    def create_super_admin(self):
        """创建超级管理员"""
        logger.info("=" * 50)
        logger.info("开始创建超级管理员...")
        logger.info("=" * 50)

        with db_config.get_session() as session:
            super_role = session.execute(
                select(Role).where(Role.role_name == SystemRole.ROLE_NAMES[SystemRole.SUPER_SYS_ADMIN])
            ).scalar_one_or_none()

            if not super_role:
                logger.error("超级管理员角色不存在，请先运行 init-roles")
                return False

            first_title = session.execute(select(Title)).scalars().first()
            if not first_title:
                logger.error("职称数据不存在，请先运行 init")
                return False

            existing_user = session.execute(select(User).where(User.user_name == self.ADMIN_USERNAME)).scalar_one_or_none()

            if existing_user:
                logger.warning(f"用户 '{self.ADMIN_USERNAME}' 已存在，正在更新...")
                existing_user.password_hash = bcrypt.hashpw(
                    self.ADMIN_PASSWORD.encode('utf-8'), bcrypt.gensalt()
                ).decode('utf-8')
                existing_user.real_name = self.ADMIN_REAL_NAME
                existing_user.email = self.ADMIN_EMAIL
                existing_user.phone = self.ADMIN_PHONE
                existing_user.role_id = super_role.role_id
                existing_user.title_id = 9
                session.commit()
                logger.info(f"已更新用户: {self.ADMIN_USERNAME}")
            else:
                user = User(
                    user_id=uuid4(),
                    user_name=self.ADMIN_USERNAME,
                    password_hash=bcrypt.hashpw(
                        self.ADMIN_PASSWORD.encode('utf-8'), bcrypt.gensalt()
                    ).decode('utf-8'),
                    real_name=self.ADMIN_REAL_NAME,
                    email=self.ADMIN_EMAIL,
                    phone=self.ADMIN_PHONE,
                    role_id=super_role.role_id,
                    title_id=9
                )
                session.add(user)
                session.commit()
                logger.info(f"超级管理员创建成功!")
                logger.info(f"  用户名: {self.ADMIN_USERNAME}")
                logger.info(f"  密码: {self.ADMIN_PASSWORD}")

        logger.info("=" * 50)
        logger.info("超级管理员创建完成!")
        logger.info("=" * 50)
        return True


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print(__doc__)
        print("\n可用命令:")
        print("  clear      - 清空数据库所有数据")
        print("  init       - 初始化基础数据（职称、部门、缺陷类型）")
        print("  init-roles - 初始化系统角色")
        print("  init-admin - 创建超级管理员")
        print("  all        - 完整初始化（清空+初始化+角色+管理员）")
        return

    initializer = DatabaseInitializer()
    command = sys.argv[1].lower()

    if command == "clear":
        initializer.clear_database()
    elif command == "init":
        initializer.init_base_data()
    elif command == "init-roles":
        initializer.init_system_roles()
    elif command == "init-admin":
        initializer.create_super_admin()
    elif command == "all":
        initializer.clear_database()
        initializer.init_base_data()
        initializer.init_system_roles()
        initializer.create_super_admin()
        print("\n" + "=" * 50)
        print("数据库完整初始化完成!")
        print("默认管理员账号: admin / admin123")
        print("=" * 50)
    else:
        print(f"未知命令: {command}")
        print(__doc__)


if __name__ == "__main__":
    main()

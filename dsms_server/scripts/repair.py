#!/usr/bin/env python3
"""
系统修复脚本

功能说明:
    - reset-admin: 重置超级管理员密码为默认值
    - reset-titles: 重置系统职称数据（保留原数据，补充缺失）
    - reset-roles: 重置系统角色（先清空再重建）
    - all: 执行所有修复操作

使用示例:
    python repair.py reset-admin   # 重置管理员密码
    python repair.py reset-titles  # 重置职称数据
    python repair.py reset-roles   # 重置系统角色
    python repair.py all           # 执行所有修复

注意:
    1. 确保已正确配置 config.toml 中的数据库连接信息
    2. 运行前确保 PostgreSQL 服务已启动
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config.database import db_config
from app.models import Title, Role, User
from sqlmodel import select
from sqlalchemy import text
import bcrypt
from uuid import uuid4
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def reset_admin(username: str = "admin", password: str = "admin123"):
    """重置超级管理员密码"""
    logger.info("=" * 50)
    logger.info("开始重置超级管理员...")
    logger.info("=" * 50)

    from app.core.system_roles import SystemRole

    db_config.init_db()

    with db_config.get_session() as session:
        # 检查管理员用户是否存在
        result = session.execute(select(User).where(User.user_name == username))
        user = result.scalar_one_or_none()

        if user:
            user.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            session.commit()
            logger.info(f"  已重置用户: {username}")
            logger.info(f"  新密码: {password}")
        else:
            # 如果管理员不存在，尝试创建
            logger.warning(f"  用户 '{username}' 不存在，尝试创建...")

            # 检查角色
            super_role = session.execute(
                select(Role).where(Role.role_name == SystemRole.ROLE_NAMES[SystemRole.SUPER_SYS_ADMIN])
            ).scalar_one_or_none()

            if not super_role:
                logger.error("  超级管理员角色不存在，请先运行 reset-roles")
                return

            # 检查职称
            first_title = session.execute(select(Title)).scalars().first()
            if not first_title:
                logger.error("  职称数据不存在，请先运行 reset-titles")
                return

            user = User(
                user_id=uuid4(),
                user_name=username,
                password_hash=bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
                real_name="超级管理员",
                email="admin@example.com",
                phone="13800138000",
                role_id=super_role.role_id,
                title_id=first_title.title_id
            )
            session.add(user)
            session.commit()
            logger.info(f"  已创建用户: {username}")
            logger.info(f"  密码: {password}")

    logger.info("=" * 50)
    logger.info("超级管理员重置完成!")
    logger.info("=" * 50)


def reset_titles():
    """重置系统职称数据"""
    logger.info("=" * 50)
    logger.info("开始重置系统职称...")
    logger.info("=" * 50)

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

    db_config.init_db()

    with db_config.get_session() as session:
        for title_data in DEFAULT_TITLES:
            result = session.execute(select(Title).where(Title.title_id == title_data["title_id"]))
            existing = result.scalar_one_or_none()

            if existing:
                if existing.title_name != title_data["title_name"]:
                    existing.title_name = title_data["title_name"]
                    logger.info(f"  更新职称: {title_data['title_name']}")
                else:
                    logger.info(f"  职称已存在: {title_data['title_name']}")
            else:
                title = Title(
                    title_id=title_data["title_id"],
                    title_name=title_data["title_name"]
                )
                session.add(title)
                logger.info(f"  创建职称: {title_data['title_name']}")

        session.commit()

    logger.info("=" * 50)
    logger.info("系统职称重置完成!")
    logger.info("=" * 50)


def reset_roles():
    """重置系统角色"""
    logger.info("=" * 50)
    logger.info("开始重置系统角色...")
    logger.info("=" * 50)

    from app.core.system_roles import get_all_system_roles, get_default_permissions

    db_config.init_db()

    with db_config.get_session() as session:
        # 获取现有系统角色
        existing_roles = session.execute(
            select(Role).where(Role.is_system_role == True)
        ).scalars().all()

        if existing_roles:
            logger.info(f"发现 {len(existing_roles)} 个现有系统角色，正在清空...")
            old_role_ids = [r.role_id for r in existing_roles]

            # 创建临时角色用于迁移用户
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

            # 将使用旧角色的用户迁移到临时角色
            for old_id in old_role_ids:
                session.execute(
                    text("UPDATE users SET role_id = :new_id WHERE role_id = :old_id"),
                    {"new_id": temp_role_id, "old_id": old_id}
                )

            # 删除旧角色
            for old_role in existing_roles:
                session.delete(old_role)

            session.commit()
            logger.info(f"已清空 {len(existing_roles)} 个系统角色")

        # 插入新角色
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
    logger.info("系统角色重置完成!")
    logger.info("=" * 50)


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print(__doc__)
        print("\n可用命令:")
        print("  reset-admin  - 重置超级管理员密码")
        print("  reset-titles - 重置系统职称数据")
        print("  reset-roles  - 重置系统角色")
        print("  all          - 执行所有修复操作")
        return

    command = sys.argv[1].lower()

    if command == "reset-admin":
        reset_admin()
    elif command == "reset-titles":
        reset_titles()
    elif command == "reset-roles":
        reset_roles()
    elif command == "all":
        reset_titles()
        reset_roles()
        reset_admin()
        print("\n" + "=" * 50)
        print("系统修复完成!")
        print("默认管理员账号: admin / admin123")
        print("=" * 50)
    else:
        print(f"未知命令: {command}")
        print(__doc__)


if __name__ == "__main__":
    main()

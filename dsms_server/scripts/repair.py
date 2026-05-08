#!/usr/bin/env python3
"""
系统修复脚本

功能说明:
    - reset-admin: 重置超级管理员密码为默认值
    - reset-titles: 重置系统职称数据（保留原数据，补充缺失）
    - reset-departments: 重置部门数据（保留原数据，补充缺失）
    - reset-defect-types: 重置缺陷类型数据（保留原数据，补充缺失）
    - reset-roles: 重置系统角色（先清空再重建，处理外键关系）
    - clean-detection: 清空检测相关数据（生产线、设备、检测记录、缺陷详情、审查任务）
    - clean-logs: 清空审计日志、用户消息、系统消息、公告（广告）
    - clean-all: 清空所有数据（考虑外键依赖关系）
    - all: 执行所有修复操作

使用示例:
    python repair.py reset-admin       # 重置管理员密码
    python repair.py reset-titles      # 重置职称数据
    python repair.py reset-departments # 重置部门数据
    python repair.py reset-roles       # 重置系统角色
    python repair.py clean-detection   # 清空检测数据
    python repair.py clean-logs        # 清空日志和消息数据
    python repair.py clean-all         # 清空所有数据
    python repair.py all               # 执行所有修复

注意:
    1. 确保已正确配置 config.toml 中的数据库连接信息
    2. 运行前确保 PostgreSQL 服务已启动
"""

import sys
import bcrypt
import logging
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config.database import db_config
from app.models import Title, Department, DefectType, Role, User
from sqlmodel import select, delete
from sqlalchemy import text

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class RepairManager:
    """系统修复管理器"""

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

    def reset_admin(self):
        """重置超级管理员密码"""
        logger.info("=" * 50)
        logger.info("开始重置超级管理员...")
        logger.info("=" * 50)

        from app.core.system_roles import SystemRole

        with db_config.get_session() as session:
            result = session.execute(select(User).where(User.user_name == self.ADMIN_USERNAME))
            user = result.scalar_one_or_none()

            if user:
                user.password_hash = bcrypt.hashpw(
                    self.ADMIN_PASSWORD.encode('utf-8'), bcrypt.gensalt()
                ).decode('utf-8')
                session.commit()
                logger.info(f"  已重置用户: {self.ADMIN_USERNAME}")
                logger.info(f"  新密码: {self.ADMIN_PASSWORD}")
            else:
                logger.warning(f"  用户 '{self.ADMIN_USERNAME}' 不存在，尝试创建...")

                super_role = session.execute(
                    select(Role).where(Role.role_name == SystemRole.ROLE_NAMES[SystemRole.SUPER_SYS_ADMIN])
                ).scalar_one_or_none()

                if not super_role:
                    logger.error("  超级管理员角色不存在，请先运行 reset-roles")
                    return

                first_title = session.execute(select(Title)).scalars().first()
                if not first_title:
                    logger.error("  职称数据不存在，请先运行 reset-titles")
                    return

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
                    title_id=first_title.title_id
                )
                session.add(user)
                session.commit()
                logger.info(f"  已创建用户: {self.ADMIN_USERNAME}")
                logger.info(f"  密码: {self.ADMIN_PASSWORD}")

        logger.info("=" * 50)
        logger.info("超级管理员重置完成!")
        logger.info("=" * 50)

    def reset_titles(self):
        """重置系统职称数据"""
        logger.info("=" * 50)
        logger.info("开始重置系统职称...")
        logger.info("=" * 50)

        with db_config.get_session() as session:
            for title_data in self.DEFAULT_TITLES:
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

    def reset_departments(self):
        """重置部门数据"""
        logger.info("=" * 50)
        logger.info("开始重置部门数据...")
        logger.info("=" * 50)

        with db_config.get_session() as session:
            for dept_data in self.DEFAULT_DEPARTMENTS:
                result = session.execute(select(Department).where(Department.department_id == dept_data["department_id"]))
                existing = result.scalar_one_or_none()

                if existing:
                    needs_update = False
                    if existing.department_code != dept_data["department_code"]:
                        existing.department_code = dept_data["department_code"]
                        needs_update = True
                    if existing.department_name != dept_data["department_name"]:
                        existing.department_name = dept_data["department_name"]
                        needs_update = True
                    if existing.parent_id != dept_data["parent_id"]:
                        existing.parent_id = dept_data["parent_id"]
                        needs_update = True

                    if needs_update:
                        logger.info(f"  更新部门: {dept_data['department_name']}")
                    else:
                        logger.info(f"  部门已存在: {dept_data['department_name']}")
                else:
                    dept = Department(
                        department_id=dept_data["department_id"],
                        department_code=dept_data["department_code"],
                        department_name=dept_data["department_name"],
                        parent_id=dept_data["parent_id"]
                    )
                    session.add(dept)
                    logger.info(f"  创建部门: {dept_data['department_name']}")

            session.commit()

        logger.info("=" * 50)
        logger.info("部门数据重置完成!")
        logger.info("=" * 50)

    def reset_defect_types(self):
        """重置缺陷类型数据"""
        logger.info("=" * 50)
        logger.info("开始重置缺陷类型数据...")
        logger.info("=" * 50)

        with db_config.get_session() as session:
            for defect_data in self.DEFAULT_DEFECT_TYPES:
                result = session.execute(select(DefectType).where(DefectType.defect_type_id == defect_data["defect_type_id"]))
                existing = result.scalar_one_or_none()

                if existing:
                    if existing.defect_type_name != defect_data["defect_type_name"]:
                        existing.defect_type_name = defect_data["defect_type_name"]
                        logger.info(f"  更新缺陷类型: {defect_data['defect_type_name']}")
                    else:
                        logger.info(f"  缺陷类型已存在: {defect_data['defect_type_name']}")
                else:
                    defect = DefectType(
                        defect_type_id=defect_data["defect_type_id"],
                        defect_type_name=defect_data["defect_type_name"]
                    )
                    session.add(defect)
                    logger.info(f"  创建缺陷类型: {defect_data['defect_type_name']}")

            session.commit()

        logger.info("=" * 50)
        logger.info("缺陷类型数据重置完成!")
        logger.info("=" * 50)

    def reset_roles(self):
        """重置系统角色（处理外键关系）"""
        logger.info("=" * 50)
        logger.info("开始重置系统角色...")
        logger.info("=" * 50)

        from app.core.system_roles import get_all_system_roles, get_default_permissions

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
        logger.info("系统角色重置完成!")
        logger.info("=" * 50)

    def clean_detection_data(self):
        """清空检测相关数据（考虑外键关系）"""
        logger.info("=" * 50)
        logger.info("开始清空检测相关数据...")
        logger.info("=" * 50)

        # 使用 SQL 直接操作，避免模型字段不匹配问题
        # 按外键依赖顺序排列，确保子表先于父表删除
        tables_to_clear = [
            ("announcement_readers", "公告已读记录"),
            ("announcements", "公告"),
            ("user_messages", "用户消息"),
            ("system_messages", "系统消息"),
            ("user_operation_logs", "审计日志"),
            ("review_tasks", "审查任务"),
            ("defect_details", "缺陷详情"),
            ("detection_records", "检测记录"),
            ("device_status_history", "设备状态历史"),
            ("devices", "设备"),
            ("device_approvals", "设备审批"),
            ("production_lines", "生产线"),
        ]

        with db_config.engine.connect() as conn:
            for table_name, display_name in tables_to_clear:
                try:
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                    count = result.scalar_one()
                    if count > 0:
                        conn.execute(text(f"DELETE FROM {table_name}"))
                        logger.info(f"  已清空 {display_name}: {count} 条记录")
                    else:
                        logger.info(f"  {display_name} 为空，跳过")
                except Exception as e:
                    logger.warning(f"  跳过 {display_name}: {str(e)}")
            conn.commit()

        logger.info("=" * 50)
        logger.info("检测数据清空完成!")
        logger.info("=" * 50)

    def clean_logs(self):
        """单独清空日志和消息数据"""
        logger.info("=" * 50)
        logger.info("开始清空日志和消息数据...")
        logger.info("=" * 50)

        # 按外键依赖顺序排列
        tables_to_clear = [
            ("announcement_readers", "公告已读记录"),
            ("announcements", "公告"),
            ("user_messages", "用户消息"),
            ("system_messages", "系统消息"),
            ("user_operation_logs", "审计日志"),
        ]

        with db_config.engine.connect() as conn:
            for table_name, display_name in tables_to_clear:
                try:
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                    count = result.scalar_one()
                    if count > 0:
                        conn.execute(text(f"DELETE FROM {table_name}"))
                        logger.info(f"  已清空 {display_name}: {count} 条记录")
                    else:
                        logger.info(f"  {display_name} 为空，跳过")
                except Exception as e:
                    logger.warning(f"  跳过 {display_name}: {str(e)}")
            conn.commit()

        logger.info("=" * 50)
        logger.info("日志和消息数据清空完成!")
        logger.info("=" * 50)

    def clean_all_data(self):
        """清空所有数据（考虑外键依赖关系）"""
        logger.info("=" * 50)
        logger.info("开始清空所有数据...")
        logger.info("=" * 50)

        # 按外键依赖顺序清空表
        tables_ordered = [
            "review_tasks",
            "defect_details",
            "detection_records",
            "device_status_history",
            "devices",
            "device_approvals",
            "production_lines",
            "announcement_readers",
            "user_messages",
            "system_messages",
            "announcements",
            "user_operation_logs",
            "users",
            "roles",
            "defect_types",
            "departments",
            "titles",
        ]

        with db_config.engine.connect() as conn:
            for table_name in tables_ordered:
                result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                count = result.scalar_one()
                if count > 0:
                    conn.execute(text(f"TRUNCATE TABLE {table_name} CASCADE"))
                    logger.info(f"  已清空表: {table_name} ({count} 条记录)")
                else:
                    logger.info(f"  表 {table_name} 为空，跳过")
            conn.commit()

        logger.info("=" * 50)
        logger.info("所有数据清空完成!")
        logger.info("=" * 50)


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print(__doc__)
        return

    manager = RepairManager()
    command = sys.argv[1].lower()

    commands = {
        "reset-admin": manager.reset_admin,
        "reset-titles": manager.reset_titles,
        "reset-departments": manager.reset_departments,
        "reset-defect-types": manager.reset_defect_types,
        "reset-roles": manager.reset_roles,
        "clean-detection": manager.clean_detection_data,
        "clean-logs": manager.clean_logs,
        "clean-all": manager.clean_all_data,
    }

    if command == "all":
        manager.reset_titles()
        manager.reset_departments()
        manager.reset_defect_types()
        manager.reset_roles()
        manager.reset_admin()
        print("\n" + "=" * 50)
        print("系统修复完成!")
        print("默认管理员账号: admin / admin123")
        print("=" * 50)
    elif command in commands:
        commands[command]()
    else:
        print(f"未知命令: {command}")
        print(__doc__)


if __name__ == "__main__":
    main()
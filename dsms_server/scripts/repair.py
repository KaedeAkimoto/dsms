#!/usr/bin/env python3
"""
系统修复脚本

功能说明:
    - fix-db: 修复数据库结构（删除所有表并根据模型重建）
    - reseed: 重新填充系统基础数据（职称、部门、缺陷类型、角色、管理员）
    - reset-admin: 重置超级管理员密码
    - clean-detection: 清空检测相关数据（生产线、设备、检测记录、缺陷详情、审查任务）
    - clean-logs: 清空审计日志、用户消息、系统消息、公告
    - clean-all: 清空所有数据
    - all: 执行完整修复（修复数据库+填充数据）

使用示例:
    python repair.py fix-db        # 修复数据库结构
    python repair.py reseed      # 重新填充系统数据
    python repair.py reset-admin # 重置管理员密码
    python repair.py clean-detection  # 清空检测数据
    python repair.py clean-logs   # 清空日志数据
    python repair.py clean-all    # 清空所有数据
    python repair.py all         # 完整修复（推荐）

注意:
    1. 确保已正确配置 config.toml 中的数据库连接信息
    2. 运行前确保 PostgreSQL 服务已启动
    3. fix-db 和 all 命令会删除所有现有数据，请谨慎操作
"""

import sys
import bcrypt
import logging
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config.database import db_config
from app.models import (
    Title, Department, DefectType, Role, User,
    ProductionLine, Device, DeviceApproval, DeviceStatusHistory,
    DetectionRecord, DefectDetail, ReviewTask,
    UserOperationLog, UserMessage, SystemMessage, Announcement, AnnouncementReader
)
from app.core.system_roles import get_all_system_roles, get_default_permissions, SystemRole
from sqlmodel import SQLModel, select
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

    TABLE_ORDER_BY_DEPENDENCY = [
        "titles",
        "departments",
        "roles",
        "users",
        "defect_types",
        "production_lines",
        "device_approvals",
        "devices",
        "device_status_history",
        "detection_records",
        "defect_details",
        "review_tasks",
        "user_operation_logs",
        "user_messages",
        "system_messages",
        "announcements",
        "announcement_readers",
    ]

    def __init__(self):
        db_config.init_db()
        self.debug_images_path = Path(__file__).parent.parent / "debug" / "images"

    def fix_database(self):
        """修复数据库结构 - 删除所有表并重建"""
        logger.info("=" * 50)
        logger.info("开始修复数据库结构...")
        logger.info("=" * 50)

        with db_config.engine.connect() as conn:
            for table_name in reversed(self.TABLE_ORDER_BY_DEPENDENCY):
                try:
                    conn.execute(text(f"DROP TABLE IF EXISTS {table_name} CASCADE"))
                    logger.info(f"  已删除表: {table_name}")
                except Exception as e:
                    logger.warning(f"  删除表 {table_name} 失败: {e}")
            conn.commit()

        logger.info("\n根据模型重建所有表...")
        SQLModel.metadata.create_all(db_config.engine)
        logger.info("所有表创建完成!")

        logger.info("=" * 50)
        logger.info("数据库结构修复完成!")
        logger.info("=" * 50)

    def reseed_system_data(self):
        """重新填充系统基础数据"""
        logger.info("=" * 50)
        logger.info("开始重新填充系统数据...")
        logger.info("=" * 50)

        with db_config.get_session() as session:
            logger.info("[1/5] 填充职称数据...")
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
            session.commit()

            logger.info("[2/5] 填充部门数据...")
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
            session.commit()

            logger.info("[3/5] 填充缺陷类型数据...")
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

            logger.info("[4/5] 填充系统角色...")
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

            logger.info("[5/5] 创建超级管理员...")
            super_role = session.execute(
                select(Role).where(Role.role_name == SystemRole.ROLE_NAMES[SystemRole.SUPER_SYS_ADMIN])
            ).scalar_one_or_none()

            if not super_role:
                logger.error("超级管理员角色不存在，请先运行 reseed")
                return

            first_title = session.execute(select(Title)).scalars().first()
            if not first_title:
                logger.error("职称数据不存在，请先运行 reseed")
                return

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
        logger.info("系统数据填充完成!")
        logger.info("=" * 50)

    def reset_admin(self):
        """重置超级管理员密码"""
        logger.info("=" * 50)
        logger.info("开始重置超级管理员...")
        logger.info("=" * 50)

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
                logger.warning(f"  用户 '{self.ADMIN_USERNAME}' 不存在，请先运行 reseed 创建")

        logger.info("=" * 50)
        logger.info("超级管理员重置完成!")
        logger.info("=" * 50)

    def clean_detection_data(self):
        """清空检测相关数据（考虑外键关系）"""
        logger.info("=" * 50)
        logger.info("开始清空检测相关数据...")
        logger.info("=" * 50)

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

        with db_config.engine.connect() as conn:
            for table_name in reversed(self.TABLE_ORDER_BY_DEPENDENCY):
                try:
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                    count = result.scalar_one()
                    if count > 0:
                        conn.execute(text(f"TRUNCATE TABLE {table_name} CASCADE"))
                        logger.info(f"  已清空表: {table_name} ({count} 条记录)")
                    else:
                        logger.info(f"  表 {table_name} 为空，跳过")
                except Exception as e:
                    logger.warning(f"  清空表 {table_name} 失败: {e}")
            conn.commit()

        logger.info("=" * 50)
        logger.info("所有数据清空完成!")
        logger.info("=" * 50)


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print(__doc__)
        print("\n可用命令:")
        print("  fix-db        - 修复数据库结构（删除所有表并重建）")
        print("  reseed        - 重新填充系统基础数据")
        print("  reset-admin   - 重置超级管理员密码")
        print("  clean-detection - 清空检测相关数据")
        print("  clean-logs    - 清空日志和消息数据")
        print("  clean-all     - 清空所有数据")
        print("  all           - 完整修复（修复数据库+填充数据）")
        return

    manager = RepairManager()
    command = sys.argv[1].lower()

    if command == "fix-db":
        manager.fix_database()
    elif command == "reseed":
        manager.reseed_system_data()
    elif command == "reset-admin":
        manager.reset_admin()
    elif command == "clean-detection":
        manager.clean_detection_data()
    elif command == "clean-logs":
        manager.clean_logs()
    elif command == "clean-all":
        manager.clean_all_data()
    elif command == "all":
        manager.fix_database()
        manager.reseed_system_data()
        print("\n" + "=" * 50)
        print("系统修复完成!")
        print("默认管理员账号: admin / admin123")
        print("缺陷图片路径: debug/images/")
        print("=" * 50)
    else:
        print(f"未知命令: {command}")
        print(__doc__)


if __name__ == "__main__":
    main()

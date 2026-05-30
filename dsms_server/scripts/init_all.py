#!/usr/bin/env python3
"""
数据库初始化脚本

功能说明:
    - build: 从模型创建所有数据库表
    - clear: 清空数据库所有数据（保留表结构）
    - seed: 填充所有数据（基础数据+用户+设备+检测记录等）
    - all: 执行完整初始化（建表+填充数据）

使用示例:
    python init_all.py build    # 创建所有表
    python init_all.py clear    # 清空数据
    python init_all.py seed     # 填充所有数据
    python init_all.py all      # 完整初始化（建表+数据）

注意:
    1. 确保已正确配置 config.toml 中的数据库连接信息
    2. 运行前确保 PostgreSQL 服务已启动
"""

import sys
import bcrypt
import logging
import random
import base64
from datetime import datetime, timedelta, timezone, date
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
from app.core.role_cache import role_cache
from sqlmodel import SQLModel, select
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
        self._user_cache = {}
        self._device_cache = {}
        self._line_cache = {}

    def _hash_password(self, password: str) -> str:
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def _load_image_base64(self, filename: str) -> bytes:
        img_path = self.debug_images_path / filename
        if img_path.exists():
            with open(img_path, 'rb') as f:
                return f.read()
        return b''

    def _generate_batch_id(self, base_time: datetime) -> str:
        gap = 10
        minute_slot = (base_time.minute // gap) + 1
        return f"BTH{base_time.year}{base_time.month:02d}{base_time.day:02d}{base_time.hour:02d}{minute_slot}"

    def get_all_table_names(self):
        """获取所有表名"""
        with db_config.engine.connect() as conn:
            result = conn.execute(text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'"))
            return [row[0] for row in result]

    def build_tables(self):
        """从模型创建所有数据库表"""
        logger.info("=" * 50)
        logger.info("开始创建数据库表...")
        logger.info("=" * 50)

        SQLModel.metadata.create_all(db_config.engine)
        logger.info("所有表创建完成!")

        logger.info("=" * 50)
        logger.info("数据库表创建完成!")
        logger.info("=" * 50)

    def drop_all_tables(self):
        """删除所有表"""
        logger.info("=" * 50)
        logger.info("开始删除所有表...")
        logger.info("=" * 50)

        with db_config.engine.connect() as conn:
            for table_name in reversed(self.TABLE_ORDER_BY_DEPENDENCY):
                try:
                    conn.execute(text(f"DROP TABLE IF EXISTS {table_name} CASCADE"))
                    logger.info(f"  已删除表: {table_name}")
                except Exception as e:
                    logger.warning(f"  删除表 {table_name} 失败: {e}")
            conn.commit()

        logger.info("=" * 50)
        logger.info("所有表删除完成!")
        logger.info("=" * 50)

    def clear_database(self):
        """清空数据库所有数据（保留表结构）"""
        logger.info("=" * 50)
        logger.info("开始清空数据库...")
        logger.info("=" * 50)

        with db_config.engine.connect() as conn:
            for table_name in reversed(self.TABLE_ORDER_BY_DEPENDENCY):
                try:
                    conn.execute(text(f"TRUNCATE TABLE {table_name} CASCADE"))
                    logger.info(f"  已清空表: {table_name}")
                except Exception as e:
                    logger.warning(f"  清空表 {table_name} 失败: {e}")
            conn.commit()

        logger.info("=" * 50)
        logger.info("数据库清空完成!")
        logger.info("=" * 50)

    def seed_base_data(self):
        """填充基础数据（职称、部门、缺陷类型）"""
        logger.info("=" * 50)
        logger.info("开始填充基础数据...")
        logger.info("=" * 50)

        with db_config.get_session() as session:
            logger.info("[1/3] 填充职称数据...")
            for title_data in self.DEFAULT_TITLES:
                result = session.execute(select(Title).where(Title.title_id == title_data["title_id"]))
                existing = result.scalar_one_or_none()
                if existing:
                    existing.title_name = title_data["title_name"]
                else:
                    title = Title(title_id=title_data["title_id"], title_name=title_data["title_name"])
                    session.add(title)
                logger.info(f"  职称: {title_data['title_name']}")
            session.commit()

            logger.info("[2/3] 填充部门数据...")
            for dept_data in self.DEFAULT_DEPARTMENTS:
                result = session.execute(select(Department).where(Department.department_id == dept_data["department_id"]))
                existing = result.scalar_one_or_none()
                if existing:
                    existing.department_code = dept_data["department_code"]
                    existing.department_name = dept_data["department_name"]
                    existing.parent_id = dept_data["parent_id"]
                else:
                    dept = Department(
                        department_id=dept_data["department_id"],
                        department_code=dept_data["department_code"],
                        department_name=dept_data["department_name"],
                        parent_id=dept_data["parent_id"]
                    )
                    session.add(dept)
                logger.info(f"  部门: {dept_data['department_name']}")
            session.commit()

            logger.info("[3/3] 填充缺陷类型数据...")
            for defect_data in self.DEFAULT_DEFECT_TYPES:
                result = session.execute(select(DefectType).where(DefectType.defect_type_id == defect_data["defect_type_id"]))
                existing = result.scalar_one_or_none()
                if existing:
                    existing.defect_type_name = defect_data["defect_type_name"]
                else:
                    defect = DefectType(
                        defect_type_id=defect_data["defect_type_id"],
                        defect_type_name=defect_data["defect_type_name"]
                    )
                    session.add(defect)
                logger.info(f"  缺陷类型: {defect_data['defect_type_name']}")
            session.commit()

        logger.info("基础数据填充完成!")

    def seed_system_roles(self):
        """填充系统角色"""
        logger.info("=" * 50)
        logger.info("开始填充系统角色...")
        logger.info("=" * 50)

        with db_config.get_session() as session:
            existing_roles = session.execute(select(Role).where(Role.is_system_role == True)).scalars().all()

            if existing_roles:
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
                    session.execute(text("UPDATE users SET role_id = :new_id WHERE role_id = :old_id"),
                                   {"new_id": temp_role_id, "old_id": old_id})

                for old_role in existing_roles:
                    session.delete(old_role)
                session.commit()

            for role_info in get_all_system_roles():
                role = Role(
                    role_name=role_info["role_name"],
                    desc=role_info["description"],
                    is_system_role=True,
                    permissions=get_default_permissions(role_info["role_key"])
                )
                session.add(role)
                logger.info(f"  角色: {role_info['role_name']}")
            session.commit()

        logger.info("系统角色填充完成!")

    def seed_users(self):
        """填充普通用户"""
        logger.info("=" * 50)
        logger.info("开始填充用户数据...")
        logger.info("=" * 50)

        with db_config.get_session() as session:
            super_role = session.execute(select(Role).where(
                Role.role_name == SystemRole.ROLE_NAMES[SystemRole.SUPER_SYS_ADMIN]
            )).scalar_one_or_none()

            sys_admin_role = session.execute(select(Role).where(
                Role.role_name == SystemRole.ROLE_NAMES[SystemRole.SENIOR_SYS_ADMIN]
            )).scalar_one_or_none()

            hr_role = session.execute(select(Role).where(
                Role.role_name == SystemRole.ROLE_NAMES[SystemRole.HR_ADMIN]
            )).scalar_one_or_none()

            device_role = session.execute(select(Role).where(
                Role.role_name == SystemRole.ROLE_NAMES[SystemRole.DEVICE_ADMIN]
            )).scalar_one_or_none()

            qa_role = session.execute(select(Role).where(
                Role.role_name == SystemRole.ROLE_NAMES[SystemRole.DETECTION_MONITOR]
            )).scalar_one_or_none()

            operator_role = session.execute(select(Role).where(
                Role.role_name == SystemRole.ROLE_NAMES[SystemRole.NORMAL_EMPLOYEE]
            )).scalar_one_or_none()

            users_data = [
                {"user_name": "admin", "real_name": "超级管理员", "email": "admin@example.com",
                 "phone": "13800138000", "role_id": super_role.role_id, "title_id": 9, "department_id": 1},
                {"user_name": "sysadmin", "real_name": "系统管理员", "email": "sysadmin@example.com",
                 "phone": "13800138005", "role_id": sys_admin_role.role_id if sys_admin_role else super_role.role_id,
                 "title_id": 5, "department_id": 2},
                {"user_name": "hradmin", "real_name": "人事管理员", "email": "hradmin@example.com",
                 "phone": "13800138006", "role_id": hr_role.role_id if hr_role else super_role.role_id,
                 "title_id": 6, "department_id": 3},
                {"user_name": "deviceadmin", "real_name": "设备管理员", "email": "deviceadmin@example.com",
                 "phone": "13800138007", "role_id": device_role.role_id if device_role else super_role.role_id,
                 "title_id": 2, "department_id": 5},
                {"user_name": "zhangsan", "real_name": "张三", "email": "zhangsan@example.com",
                 "phone": "13800138001", "role_id": qa_role.role_id if qa_role else super_role.role_id,
                 "title_id": 2, "department_id": 6},
                {"user_name": "lisi", "real_name": "李四", "email": "lisi@example.com",
                 "phone": "13800138002", "role_id": operator_role.role_id if operator_role else super_role.role_id,
                 "title_id": 3, "department_id": 5},
                {"user_name": "wangwu", "real_name": "王五", "email": "wangwu@example.com",
                 "phone": "13800138003", "role_id": qa_role.role_id if qa_role else super_role.role_id,
                 "title_id": 2, "department_id": 6},
                {"user_name": "zhaoliu", "real_name": "赵六", "email": "zhaoliu@example.com",
                 "phone": "13800138004", "role_id": operator_role.role_id if operator_role else super_role.role_id,
                 "title_id": 4, "department_id": 5},
            ]

            for user_data in users_data:
                existing = session.execute(select(User).where(User.user_name == user_data["user_name"])).scalar_one_or_none()
                if existing:
                    self._user_cache[user_data["user_name"]] = existing.user_id
                    logger.info(f"  用户已存在: {user_data['real_name']}")
                else:
                    user = User(
                        user_id=uuid4(),
                        user_name=user_data["user_name"],
                        password_hash=self._hash_password("password123"),
                        real_name=user_data["real_name"],
                        email=user_data["email"],
                        phone=user_data["phone"],
                        role_id=user_data["role_id"],
                        title_id=user_data["title_id"],
                        department_id=user_data["department_id"]
                    )
                    session.add(user)
                    session.flush()
                    self._user_cache[user_data["user_name"]] = user.user_id
                    logger.info(f"  创建用户: {user_data['real_name']} ({user_data['user_name']})")
            session.commit()

        logger.info("用户数据填充完成!")

    def seed_production_lines(self):
        """填充生产线"""
        logger.info("=" * 50)
        logger.info("开始填充生产线数据...")
        logger.info("=" * 50)

        with db_config.get_session() as session:
            lines_data = [
                {"production_line_name": "A线-主机装配", "production_line_loc": "工厂A区1楼"},
                {"production_line_name": "B线-辅机装配", "production_line_loc": "工厂A区2楼"},
                {"production_line_name": "C线-测试", "production_line_loc": "工厂B区1楼"},
                {"production_line_name": "D线-包装", "production_line_loc": "工厂B区2楼"},
            ]

            for i, line_data in enumerate(lines_data):
                line = ProductionLine(
                    production_line_id=uuid4(),
                    production_line_name=line_data["production_line_name"],
                    production_line_loc=line_data["production_line_loc"],
                    production_line_manager=self._user_cache.get("zhangsan")
                )
                session.add(line)
                session.flush()
                self._line_cache[line_data["production_line_name"]] = line.production_line_id
                logger.info(f"  创建生产线: {line_data['production_line_name']}")
            session.commit()

        logger.info("生产线数据填充完成!")

    def seed_devices(self):
        """填充设备"""
        logger.info("=" * 50)
        logger.info("开始填充设备数据...")
        logger.info("=" * 50)

        with db_config.get_session() as session:
            devices_data = [
                {"device_name": "视觉检测相机-A1", "device_type": "工业相机", "line_name": "A线-主机装配"},
                {"device_name": "视觉检测相机-A2", "device_type": "工业相机", "line_name": "A线-主机装配"},
                {"device_name": "视觉检测相机-B1", "device_type": "工业相机", "line_name": "B线-辅机装配"},
                {"device_name": "视觉检测相机-C1", "device_type": "工业相机", "line_name": "C线-测试"},
                {"device_name": "视觉检测相机-C2", "device_type": "工业相机", "line_name": "C线-测试"},
            ]

            for dev_data in devices_data:
                device = Device(
                    device_id=uuid4(),
                    device_name=dev_data["device_name"],
                    device_type=dev_data["device_type"],
                    production_line_id=self._line_cache[dev_data["line_name"]],
                    device_manager=self._user_cache.get("zhangsan"),
                    status="active",
                    ip_addr=f"192.168.1.{random.randint(10, 250)}",
                    mac_addr=f"00:1B:44:11:{random.randint(10, 99)}:{random.randint(10, 99)}",
                    installation_date=date(2024, random.randint(1, 12), random.randint(1, 28))
                )
                session.add(device)
                session.flush()
                self._device_cache[dev_data["device_name"]] = device.device_id
                logger.info(f"  创建设备: {dev_data['device_name']}")
            session.commit()

        logger.info("设备数据填充完成!")

    def seed_device_history(self):
        """填充设备历史状态"""
        logger.info("=" * 50)
        logger.info("开始填充设备历史数据...")
        logger.info("=" * 50)

        with db_config.get_session() as session:
            device_names = list(self._device_cache.keys())
            now = datetime.now(timezone.utc)

            for device_name in device_names[:3]:
                device_id = self._device_cache[device_name]
                for hours_ago in range(24, 0, -1):
                    record_time = now - timedelta(hours=hours_ago)
                    history = DeviceStatusHistory(
                        history_id=uuid4(),
                        device_id=device_id,
                        status="active" if random.random() > 0.05 else "maintenance",
                        cpu_usage=round(random.uniform(20, 80), 2),
                        memory_usage=round(random.uniform(30, 70), 2),
                        network_latency=random.randint(1, 50),
                        created_at=record_time
                    )
                    session.add(history)
            session.commit()
            logger.info(f"  创建了 24*3=72 条设备历史记录")

        logger.info("设备历史数据填充完成!")

    def seed_detection_records(self):
        """填充检测记录和缺陷详情"""
        logger.info("=" * 50)
        logger.info("开始填充检测记录和缺陷详情...")
        logger.info("=" * 50)

        defect_images = [
            "sample_000_original.jpg", "sample_001_original.jpg", "sample_002_original.jpg",
            "sample_003_original.jpg", "sample_004_original.jpg", "sample_005_original.jpg",
            "sample_006_original.jpg", "sample_007_original.jpg", "sample_008_original.jpg",
            "sample_009_original.jpg", "sample_010_original.jpg", "sample_011_original.jpg",
            "sample_012_original.jpg", "sample_013_original.jpg", "sample_014_original.jpg",
            "sample_015_original.jpg", "sample_016_original.jpg", "sample_017_original.jpg",
            "sample_018_original.jpg", "sample_019_original.jpg",
        ]

        device_names = list(self._device_cache.keys())
        now = datetime.now(timezone.utc)
        batch_count = 0
        defect_count = 0

        with db_config.get_session() as session:
            for day_offset in range(7, 0, -1):
                for hour in range(8, 18):
                    for minute_slot in range(6):
                        base_time = now - timedelta(days=day_offset, hours=18-hour, minutes=minute_slot*10)
                        batch_id = self._generate_batch_id(base_time)

                        device_name = random.choice(device_names)
                        device_id = self._device_cache[device_name]

                        total_count = random.randint(50, 200)
                        pass_count = int(total_count * random.uniform(0.85, 0.98))

                        has_defect = random.random() > 0.6
                        detect_info = []
                        if has_defect:
                            defect_type_id = random.randint(1, 6)
                            defect_type_count = random.randint(1, 5)
                            detect_info.append({
                                "defect_type_id": defect_type_id,
                                "defect_count": defect_type_count
                            })

                        record = DetectionRecord(
                            record_batch_id=batch_id,
                            device_id=device_id,
                            detect_count=total_count,
                            pass_count=pass_count,
                            detect_info=detect_info,
                            latest_upload_at=base_time
                        )
                        session.add(record)
                        session.flush()
                        batch_count += 1

                        if has_defect and detect_info:
                            img_filename = random.choice(defect_images)
                            img_data = self._load_image_base64(img_filename)

                            if img_data:
                                for _ in range(random.randint(1, 3)):
                                    defect_record = DefectDetail(
                                        defect_details_id=uuid4(),
                                        record_batch_id=batch_id,
                                        image=img_data,
                                        image_format="jpeg",
                                        defect_count=random.randint(1, 5),
                                        details=[{
                                            "defect_type_id": detect_info[0]["defect_type_id"],
                                            "xyhw": (random.randint(100, 500), random.randint(100, 500),
                                                    random.randint(50, 200), random.randint(50, 200)),
                                            "conf": round(random.uniform(0.5, 0.99), 3)
                                        }]
                                    )
                                    session.add(defect_record)
                                    defect_count += 1
                        session.commit()

        logger.info(f"  创建了 {batch_count} 条检测记录")
        logger.info(f"  创建了 {defect_count} 条缺陷详情记录")
        logger.info("检测记录和缺陷详情填充完成!")

    def seed_messages(self):
        """填充用户消息和系统消息"""
        logger.info("=" * 50)
        logger.info("开始填充消息数据...")
        logger.info("=" * 50)

        usernames = [k for k in self._user_cache.keys() if k != "admin"]
        now = datetime.now(timezone.utc)

        with db_config.get_session() as session:
            msg_count = 0
            for i in range(20):
                send_user = self._user_cache.get(random.choice(usernames))
                receive_user = self._user_cache.get(random.choice(usernames))
                if send_user and receive_user and send_user != receive_user:
                    msg = UserMessage(
                        msg_id=uuid4(),
                        send_user=send_user,
                        receive_user=receive_user,
                        content=f"这是一条测试消息 #{i+1}",
                        created_at=now - timedelta(hours=random.randint(1, 168)),
                        status="read" if random.random() > 0.3 else "unread",
                        readed_at=now - timedelta(hours=random.randint(0, 24)) if random.random() > 0.3 else None
                    )
                    session.add(msg)
                    msg_count += 1
            session.commit()

            sys_msg_count = 0
            for username in usernames:
                user_id = self._user_cache.get(username)
                if user_id:
                    for i in range(3):
                        sys_msg = SystemMessage(
                            msg_id=uuid4(),
                            receive_user=user_id,
                            content=f"系统通知 #{i+1}: 您的设备检测任务已分配",
                            created_at=now - timedelta(days=random.randint(1, 7)),
                            status="read" if random.random() > 0.5 else "unread"
                        )
                        session.add(sys_msg)
                        sys_msg_count += 1
            session.commit()

        logger.info(f"  创建了 {msg_count} 条用户消息")
        logger.info(f"  创建了 {sys_msg_count} 条系统消息")
        logger.info("消息数据填充完成!")

    def seed_announcements(self):
        """填充公告"""
        logger.info("=" * 50)
        logger.info("开始填充公告数据...")
        logger.info("=" * 50)

        admin_id = self._user_cache.get("admin")
        now = datetime.now(timezone.utc)

        with db_config.get_session() as session:
            announcements_data = [
                {"content": "【系统通知】本周六将进行系统维护，请提前做好数据备份。", "receiver_type": "all"},
                {"content": "【质量部通知】关于2024年度质量管理体系内审的通知", "receiver_type": "department", "receive_target": 6},
                {"content": "【IT部通知】新版本检测系统已上线，请各部门知悉。", "receiver_type": "department", "receive_target": 2},
            ]

            for ann_data in announcements_data:
                announcement = Announcement(
                    announcement_id=uuid4(),
                    receiver_type=ann_data["receiver_type"],
                    receive_target=ann_data.get("receive_target"),
                    content=ann_data["content"],
                    created_at=now - timedelta(days=random.randint(1, 30)),
                    send_user=admin_id,
                    expired=now + timedelta(days=random.randint(30, 90))
                )
                session.add(announcement)
                session.flush()

                for user_id in list(self._user_cache.values()):
                    if random.random() > 0.3:
                        reader = AnnouncementReader(
                            announcement_id=announcement.announcement_id,
                            user_id=user_id,
                            readed_at=now - timedelta(days=random.randint(0, 15))
                        )
                        session.add(reader)
            session.commit()

        logger.info(f"  创建了 {len(announcements_data)} 条公告")
        logger.info("公告数据填充完成!")

    def seed_all(self):
        """填充所有数据"""
        logger.info("=" * 60)
        logger.info("开始填充所有数据...")
        logger.info("=" * 60)

        self.seed_base_data()
        self.seed_system_roles()
        self.seed_users()
        self.seed_production_lines()
        self.seed_devices()
        self.seed_device_history()
        self.seed_detection_records()
        self.seed_messages()
        self.seed_announcements()

        logger.info("=" * 60)
        logger.info("加载角色缓存...")
        role_cache.load()
        logger.info(f"角色缓存已加载: {role_cache.roles_count} 个角色, {role_cache.user_roles_count} 个用户-角色映射")
        logger.info("=" * 60)
        logger.info("所有数据填充完成!")
        logger.info("=" * 60)


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print(__doc__)
        print("\n可用命令:")
        print("  build   - 从模型创建所有数据库表")
        print("  clear   - 清空数据库所有数据（保留表结构）")
        print("  seed    - 填充所有数据（基础数据+用户+设备+检测记录等）")
        print("  all     - 完整初始化（删除所有表+建表+填充数据）")
        return

    initializer = DatabaseInitializer()
    command = sys.argv[1].lower()

    if command == "build":
        initializer.build_tables()
    elif command == "clear":
        initializer.clear_database()
    elif command == "seed":
        initializer.seed_all()
    elif command == "all":
        initializer.drop_all_tables()
        initializer.build_tables()
        initializer.seed_all()
        print("\n" + "=" * 50)
        print("数据库完整初始化完成!")
        print("默认管理员账号: admin / admin123")
        print("普通用户密码: password123")
        print("缺陷图片路径: debug/images/")
        print("=" * 50)
    else:
        print(f"未知命令: {command}")
        print(__doc__)


if __name__ == "__main__":
    main()

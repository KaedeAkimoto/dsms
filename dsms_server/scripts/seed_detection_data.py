#!/usr/bin/env python3
"""
检测数据生成脚本

为系统生成测试用检测数据，包括：
1. 生产线
2. 设备
3. 检测记录
4. 缺陷详情（包含二进制图片数据）
5. 审查任务

使用示例:
    python seed_detection_data.py          # 生成检测数据
    python seed_detection_data.py clean    # 清空检测相关数据

注意：确保基础数据（部门、职称、角色、用户）已初始化
"""

import sys
import base64
import random
import logging
from pathlib import Path
from datetime import datetime, timedelta, timezone
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config.database import db_config
from app.models import (
    ProductionLine, Device, DetectionRecord, DefectDetail, ReviewTask, User, DefectType
)
from sqlmodel import select, delete

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def load_sample_image():
    """加载示例缺陷图片"""
    sample_path = Path(__file__).parent / "sample_017_original.jpg"
    if sample_path.exists():
        with open(sample_path, "rb") as f:
            return f.read(), "jpeg"
    return base64.b64decode(
        "R0lGODlhAQABAIAAAP///wAAACH5BAEAAAAALAAAAAABAAEAAAICRAEAOw=="
    ), "gif"


DEFAULT_DEFECT_IMAGE_DATA, DEFAULT_IMAGE_FORMAT = load_sample_image()


class DetectionDataSeeder:
    """检测数据填充器"""

    DEVICE_TEMPLATES = [
        {"device_name": "冲压机-A1", "device_type": "冲压机"},
        {"device_name": "冲压机-A2", "device_type": "冲压机"},
        {"device_name": "焊接机器人-B1", "device_type": "焊接机器人"},
        {"device_name": "焊接机器人-B2", "device_type": "焊接机器人"},
        {"device_name": "喷涂机器人-C1", "device_type": "喷涂机器人"},
        {"device_name": "喷涂机器人-C2", "device_type": "喷涂机器人"},
        {"device_name": "装配机械手-D1", "device_type": "装配机械手"},
        {"device_name": "装配机械手-D2", "device_type": "装配机械手"},
        {"device_name": "质量检测仪-Q1", "device_type": "质量检测仪"},
        {"device_name": "质量检测仪-Q2", "device_type": "质量检测仪"},
    ]

    def __init__(self):
        db_config.init_db()
        self.users = []
        self.defect_types = []
        self.line_ids = []
        self.device_ids = []
        self.records = []
        self.defects = []

    def clean(self):
        """清空检测相关数据"""
        logger.info("=" * 50)
        logger.info("开始清空检测相关数据...")
        logger.info("=" * 50)

        with db_config.get_session() as session:
            session.execute(delete(ReviewTask))
            logger.info("  已清空审查任务")
            session.execute(delete(DefectDetail))
            logger.info("  已清空缺陷详情")
            session.execute(delete(DetectionRecord))
            logger.info("  已清空检测记录")
            session.execute(delete(Device))
            logger.info("  已清空设备")
            session.execute(delete(ProductionLine))
            logger.info("  已清空生产线")
            session.commit()

        logger.info("=" * 50)
        logger.info("检测数据清空完成!")
        logger.info("=" * 50)

    def load_reference_data(self):
        """加载参考数据（用户、缺陷类型）"""
        logger.info("=" * 50)
        logger.info("加载参考数据...")
        logger.info("=" * 50)

        with db_config.get_session() as session:
            self.users = list(session.execute(select(User)).scalars().all())
            logger.info(f"  找到 {len(self.users)} 个用户")

            self.defect_types = list(session.execute(select(DefectType)).scalars().all())
            logger.info(f"  找到 {len(self.defect_types)} 个缺陷类型")

        if not self.users:
            raise ValueError("系统中没有用户数据，请先运行 init_all.py 初始化基础数据")

        logger.info("=" * 50)
        logger.info("参考数据加载完成!")
        logger.info("=" * 50)

    def seed_production_lines(self):
        """生成生产线数据"""
        logger.info("=" * 50)
        logger.info("生成生产线数据...")
        logger.info("=" * 50)

        production_lines_data = [
            {"production_line_name": "A线 - 冲压车间", "production_line_loc": "冲压车间A区"},
            {"production_line_name": "B线 - 焊接车间", "production_line_loc": "焊接车间B区"},
            {"production_line_name": "C线 - 涂装车间", "production_line_loc": "涂装车间C区"},
            {"production_line_name": "D线 - 总装车间", "production_line_loc": "总装车间D区"},
        ]

        with db_config.get_session() as session:
            for i, line_data in enumerate(production_lines_data):
                line = ProductionLine(
                    production_line_id=uuid4(),
                    production_line_name=line_data["production_line_name"],
                    production_line_loc=line_data["production_line_loc"],
                    production_line_manager=self.users[i % len(self.users)].user_id
                )
                session.add(line)
                self.line_ids.append(line.production_line_id)
                logger.info(f"  创建生产线: {line_data['production_line_name']}")

            session.commit()

        logger.info("=" * 50)
        logger.info(f"生产线数据生成完成! 共 {len(self.line_ids)} 条")
        logger.info("=" * 50)

    def seed_devices(self):
        """生成设备数据"""
        logger.info("=" * 50)
        logger.info("生成设备数据...")
        logger.info("=" * 50)

        if not self.line_ids:
            raise ValueError("没有生产线，无法创建设备")

        with db_config.get_session() as session:
            for i, template in enumerate(self.DEVICE_TEMPLATES):
                device = Device(
                    device_id=uuid4(),
                    device_name=template["device_name"],
                    device_type=template["device_type"],
                    device_upload_token=f"token_{uuid4().hex[:16]}",
                    production_line_id=self.line_ids[i % len(self.line_ids)],
                    device_manager=self.users[i % len(self.users)].user_id,
                    ip_addr=f"192.168.1.{100 + i}",
                    mac_addr=f"00:1B:44:11:3A:{i:02d}",
                    status="active",
                    installation_date=datetime.now().date() - timedelta(days=random.randint(30, 365))
                )
                session.add(device)
                self.device_ids.append(device.device_id)
                logger.info(f"  创建设备: {template['device_name']}")

            session.commit()

        logger.info("=" * 50)
        logger.info(f"设备数据生成完成! 共 {len(self.device_ids)} 条")
        logger.info("=" * 50)

    def seed_detection_records(self):
        """生成检测记录数据"""
        logger.info("=" * 50)
        logger.info("生成检测记录数据...")
        logger.info("=" * 50)

        if not self.device_ids:
            raise ValueError("没有设备，无法创建检测记录")

        now = datetime.now(timezone.utc)
        self.records = []

        with db_config.get_session() as session:
            for device_id in self.device_ids:
                for day_offset in range(7):
                    for hour_offset in range(24):
                        record_time = now - timedelta(days=day_offset, hours=23 - hour_offset)
                        record_batch_id = f"BTH{record_time.strftime('%Y%m%d%H')}{uuid4().hex[:4].upper()}"

                        has_defect = random.random() < 0.3

                        if has_defect and self.defect_types:
                            detect_count = random.randint(5, 20)
                            pass_count = detect_count - random.randint(1, 5)
                            defect_type = random.choice(self.defect_types)
                            detect_info = [
                                {
                                    "defect_type_id": defect_type.defect_type_id,
                                    "defect_count": random.randint(1, 3)
                                }
                            ]
                        else:
                            detect_count = random.randint(10, 50)
                            pass_count = detect_count
                            detect_info = []

                        record = DetectionRecord(
                            record_batch_id=record_batch_id,
                            device_id=device_id,
                            detect_count=detect_count,
                            pass_count=pass_count,
                            detect_info=detect_info,
                            latest_upload_at=record_time
                        )
                        session.add(record)
                        self.records.append({
                            "record_batch_id": record_batch_id,
                            "device_id": device_id,
                            "detect_info": detect_info
                        })

                        if len(self.records) % 500 == 0:
                            logger.info(f"  已创建 {len(self.records)} 条检测记录...")
                            session.commit()

            session.commit()

        logger.info("=" * 50)
        logger.info(f"检测记录数据生成完成! 共 {len(self.records)} 条")
        logger.info("=" * 50)

    def seed_defect_details(self):
        """生成缺陷详情数据（包含二进制图片）"""
        logger.info("=" * 50)
        logger.info("生成缺陷详情数据...")
        logger.info("=" * 50)

        if not self.records:
            raise ValueError("没有检测记录，无法创建缺陷详情")

        self.defects = []

        with db_config.get_session() as session:
            count = 0
            for record in self.records:
                if not record["detect_info"]:
                    continue

                details_list = []
                for info in record["detect_info"]:
                    for _ in range(info.get("defect_count", 1)):
                        details_list.append({
                            "defect_type_id": info["defect_type_id"],
                            "xyhw": (
                                random.randint(100, 800),
                                random.randint(100, 600),
                                random.randint(50, 200),
                                random.randint(50, 200)
                            ),
                            "conf": round(random.uniform(0.5, 0.99), 3)
                        })

                defect_detail = DefectDetail(
                    defect_details_id=uuid4(),
                    record_batch_id=record["record_batch_id"],
                    image=DEFAULT_DEFECT_IMAGE_DATA,
                    image_format=DEFAULT_IMAGE_FORMAT,
                    defect_count=len(details_list),
                    details=details_list
                )
                session.add(defect_detail)
                self.defects.append({
                    "defect_details_id": defect_detail.defect_details_id,
                    "record_batch_id": record["record_batch_id"]
                })
                count += 1

                if count % 50 == 0:
                    logger.info(f"  已创建 {count} 条缺陷详情...")
                    session.commit()

            session.commit()

        logger.info("=" * 50)
        logger.info(f"缺陷详情数据生成完成! 共 {len(self.defects)} 条")
        logger.info("=" * 50)

    def seed_review_tasks(self):
        """生成审查任务数据"""
        logger.info("=" * 50)
        logger.info("生成审查任务数据...")
        logger.info("=" * 50)

        if not self.defects:
            logger.warning("没有缺陷详情，跳过审查任务生成")
            return

        if not self.users:
            logger.warning("没有用户，跳过审查任务生成")
            return

        statuses = ["pending", "completed", "completed", "completed", "cancel"]
        review_results = ["confirmed", "false_positive", "uncertain", "confusion"]

        with db_config.get_session() as session:
            count = 0
            for defect in self.defects:
                assignee = self.users[random.randint(0, len(self.users) - 1)]
                status = random.choice(statuses)
                assignee_at = datetime.now(timezone.utc) - timedelta(hours=random.randint(1, 48))

                review_task = ReviewTask(
                    review_task_id=uuid4(),
                    defect_details_id=defect["defect_details_id"],
                    assignee_id=assignee.user_id,
                    reviewer_id=assignee.user_id if status == "completed" else None,
                    review_status=status,
                    review_result=random.choice(review_results) if status == "completed" else None,
                    review_defect_count=random.randint(1, 3) if status == "completed" else None,
                    has_details=status == "completed" and random.random() < 0.5,
                    review_comment=f"审查备注-{uuid4().hex[:8]}" if status == "completed" and random.random() < 0.5 else None,
                    assignee_at=assignee_at,
                    completed_at=assignee_at + timedelta(hours=random.randint(1, 8)) if status == "completed" else None
                )
                session.add(review_task)
                count += 1

                if count % 50 == 0:
                    logger.info(f"  已创建 {count} 条审查任务...")
                    session.commit()

            session.commit()

        logger.info("=" * 50)
        logger.info(f"审查任务数据生成完成! 共 {len(self.defects)} 条")
        logger.info("=" * 50)

    def seed_all(self):
        """生成所有检测数据"""
        self.load_reference_data()
        self.seed_production_lines()
        self.seed_devices()
        self.seed_detection_records()
        self.seed_defect_details()
        self.seed_review_tasks()

        logger.info("=" * 50)
        logger.info("数据生成完成!")
        logger.info(f"  生产线: {len(self.line_ids)} 条")
        logger.info(f"  设备: {len(self.device_ids)} 条")
        logger.info(f"  检测记录: {len(self.records)} 条")
        logger.info(f"  缺陷详情: {len(self.defects)} 条")
        logger.info("=" * 50)


def main():
    """主函数"""
    if len(sys.argv) > 1 and sys.argv[1] == "clean":
        seeder = DetectionDataSeeder()
        seeder.clean()
        return

    seeder = DetectionDataSeeder()
    seeder.seed_all()


if __name__ == "__main__":
    main()
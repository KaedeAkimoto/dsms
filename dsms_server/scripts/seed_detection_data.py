#!/usr/bin/env python3
"""
检测数据生成脚本

为系统生成测试用检测数据，包括：
1. 生产线
2. 设备
3. 检测记录
4. 缺陷详情
5. 审查任务

使用示例:
    python seed_detection_data.py          # 生成检测数据
    python seed_detection_data.py clean   # 清空检测相关数据

注意：确保基础数据（部门、职称、角色、用户）已初始化
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone
from uuid import uuid4
import random
import json

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config.database import db_config
from app.models import (
    ProductionLine, Device, DeviceApproval,
    DetectionRecord, DefectDetail, ReviewTask,
    User, DefectType
)
from sqlmodel import select, delete


# 统一的缺陷图片路径
DEFAULT_DEFECT_IMAGE = "/images/defect/sample_017_original.jpg"


def clean_detection_data():
    """清空检测相关数据"""
    print("=" * 60)
    print("开始清空检测相关数据...")
    print("=" * 60)

    db_config.init_db()

    with db_config.get_session() as session:
        print("  清空审查任务...")
        session.execute(delete(ReviewTask))

        print("  清空缺陷详情...")
        session.execute(delete(DefectDetail))

        print("  清空检测记录...")
        session.execute(delete(DetectionRecord))

        print("  清空设备...")
        session.execute(delete(Device))

        print("  清空生产线...")
        session.execute(delete(ProductionLine))

        session.commit()

    print("检测数据清空完成!")


def get_existing_users():
    """获取现有用户"""
    with db_config.get_session() as session:
        result = session.execute(select(User))
        return list(result.scalars().all())


def get_existing_defect_types():
    """获取现有缺陷类型"""
    with db_config.get_session() as session:
        result = session.execute(select(DefectType))
        return list(result.scalars().all())


def seed_production_lines(users):
    """生成生产线数据"""
    print("\n生成生产线数据...")

    production_lines = [
        {
            "production_line_id": uuid4(),
            "production_line_name": "A线 - 冲压车间",
            "production_line_loc": "冲压车间A区",
            "production_line_manager": users[0].user_id if users else None
        },
        {
            "production_line_id": uuid4(),
            "production_line_name": "B线 - 焊接车间",
            "production_line_loc": "焊接车间B区",
            "production_line_manager": users[1].user_id if len(users) > 1 else None
        },
        {
            "production_line_id": uuid4(),
            "production_line_name": "C线 - 涂装车间",
            "production_line_loc": "涂装车间C区",
            "production_line_manager": users[2].user_id if len(users) > 2 else None
        },
        {
            "production_line_id": uuid4(),
            "production_line_name": "D线 - 总装车间",
            "production_line_loc": "总装车间D区",
            "production_line_manager": users[0].user_id if users else None
        },
    ]

    created_lines = []
    with db_config.get_session() as session:
        for line_data in production_lines:
            line = ProductionLine(**line_data)
            session.add(line)
            created_lines.append(line_data)
            print(f"  创建生产线: {line_data['production_line_name']}")

        session.commit()

    return [line["production_line_id"] for line in created_lines]


def seed_devices(line_ids, users):
    """生成设备数据"""
    print("\n生成设备数据...")

    if not line_ids:
        print("  错误: 没有生产线，无法创建设备")
        return []

    device_templates = [
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

    created_devices = []
    with db_config.get_session() as session:
        for i, template in enumerate(device_templates):
            device_id = uuid4()
            device = Device(
                device_id=device_id,
                device_name=template["device_name"],
                device_type=template["device_type"],
                device_upload_token=f"token_{uuid4().hex[:16]}",
                production_line_id=line_ids[i % len(line_ids)],
                device_manager=users[i % len(users)].user_id if users else None,
                ip_addr=f"192.168.1.{100 + i}",
                mac_addr=f"00:1B:44:11:3A:{i:02d}",
                status="active",
                installation_date=datetime.now().date() - timedelta(days=random.randint(30, 365))
            )
            session.add(device)
            created_devices.append({"device_id": device_id, **template})
            print(f"  创建设备: {template['device_name']}")

        session.commit()

    return [d["device_id"] for d in created_devices]


def seed_detection_records(device_ids, defect_types):
    """生成检测记录数据"""
    print("\n生成检测记录数据...")

    if not device_ids:
        print("  错误: 没有设备，无法创建检测记录")
        return []

    created_records = []
    now = datetime.now(timezone.utc)

    for device_id in device_ids:
        for day_offset in range(7):
            for hour_offset in range(24):
                record_time = now - timedelta(days=day_offset, hours=23 - hour_offset)
                record_batch_id = f"BTH{record_time.strftime('%Y%m%d%H')}{uuid4().hex[:4].upper()}"

                has_defect = random.random() < 0.3

                if has_defect and defect_types:
                    detect_count = random.randint(5, 20)
                    pass_count = detect_count - random.randint(1, 5)
                    defect_type = random.choice(defect_types)
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

                with db_config.get_session() as session:
                    record = DetectionRecord(
                        record_batch_id=record_batch_id,
                        device_id=device_id,
                        detect_count=detect_count,
                        pass_count=pass_count,
                        detect_info=detect_info,
                        latest_upload_at=record_time
                    )
                    session.add(record)
                    session.commit()

                created_records.append({
                    "record_batch_id": record_batch_id,
                    "device_id": device_id,
                    "detect_info": detect_info
                })

                if len(created_records) % 500 == 0:
                    print(f"  已创建 {len(created_records)} 条检测记录...")

    print(f"  共创建 {len(created_records)} 条检测记录")
    return created_records


def seed_defect_details(records, defect_types):
    """生成缺陷详情数据"""
    print("\n生成缺陷详情数据...")

    if not records:
        print("  错误: 没有检测记录，无法创建缺陷详情")
        return []

    created_defects = []

    with db_config.get_session() as session:
        count = 0
        for record in records:
            if not record["detect_info"]:
                continue

            defect_details_id = uuid4()
            # 使用统一的缺陷图片
            original_img = DEFAULT_DEFECT_IMAGE

            details_list = []
            for info in record["detect_info"]:
                for _ in range(info["defect_count"] if "defect_count" in info else 1):
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
                defect_details_id=defect_details_id,
                record_batch_id=record["record_batch_id"],
                original_img=original_img,
                defect_count=len(details_list),
                details=details_list
            )
            session.add(defect_detail)
            created_defects.append({
                "defect_details_id": defect_details_id,
                "record_batch_id": record["record_batch_id"]
            })
            count += 1

            if count % 50 == 0:
                print(f"  已创建 {count} 条缺陷详情...")
                session.commit()

        session.commit()

    print(f"  共创建 {len(created_defects)} 条缺陷详情")
    return created_defects


def seed_review_tasks(defects, users):
    """生成审查任务数据"""
    print("\n生成审查任务数据...")

    if not defects:
        print("  错误: 没有缺陷详情，无法创建审查任务")
        return

    if not users:
        print("  错误: 没有用户，无法创建审查任务")
        return

    statuses = ["pending", "completed", "completed", "completed", "cancel"]
    review_results = ["confirmed", "false_positive", "uncertain", "confusion"]

    with db_config.get_session() as session:
        count = 0
        for defect in defects:
            assignee = users[random.randint(0, len(users) - 1)]
            status = random.choice(statuses)

            review_task_id = uuid4()
            assignee_at = datetime.now(timezone.utc) - timedelta(hours=random.randint(1, 48))

            review_task = ReviewTask(
                review_task_id=review_task_id,
                defect_details_id=defect["defect_details_id"],
                assignee_id=assignee.user_id,
                reviewer_id=assignee.user_id if status == "completed" else None,
                review_status=status,
                review_result=random.choice(review_results) if status == "completed" else None,
                review_defect_count=random.randint(1, 3) if status == "completed" else None,
                has_details=True if status == "completed" and random.random() < 0.5 else False,
                review_comment=f"审查备注-{uuid4().hex[:8]}" if status == "completed" and random.random() < 0.5 else None,
                assignee_at=assignee_at,
                completed_at=assignee_at + timedelta(hours=random.randint(1, 8)) if status == "completed" else None
            )
            session.add(review_task)
            count += 1

            if count % 50 == 0:
                print(f"  已创建 {count} 条审查任务...")
                session.commit()

        session.commit()

    print(f"  共创建 {len(defects)} 条审查任务")


def main():
    print("=" * 60)
    print("检测数据生成脚本")
    print("=" * 60)

    if len(sys.argv) > 1 and sys.argv[1] == "clean":
        clean_detection_data()
        return

    db_config.init_db()

    print("\n获取现有数据...")
    users = get_existing_users()
    print(f"  找到 {len(users)} 个用户")
    defect_types = get_existing_defect_types()
    print(f"  找到 {len(defect_types)} 个缺陷类型")

    if not users:
        print("\n错误: 系统中没有用户数据，请先运行 init_all.py 初始化基础数据")
        return

    line_ids = seed_production_lines(users)
    device_ids = seed_devices(line_ids, users)
    records = seed_detection_records(device_ids, defect_types)
    defects = seed_defect_details(records, defect_types)
    seed_review_tasks(defects, users)

    print("\n" + "=" * 60)
    print("数据生成完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
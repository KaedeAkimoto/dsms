"""
设备检测WebSocket接口

设备通过WebSocket连接服务器，上传图片进行实时缺陷检测。
"""

import asyncio
import json
import base64
import time
from datetime import datetime, timezone
from typing import Dict, Optional
from uuid import UUID, uuid4
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from sqlalchemy import select

from app.config.database import db_config
from app.config.server import server_config
from app.models import Device, User, DetectionRecord, DefectDetail, ReviewTask, DefectType
from app.core.system_roles import SystemRole
from app.services.yolo import yolo_detector
from app.services.message import SystemMessageService
from app.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)

TIME_GAP_MINUTES = 5


class DeviceStatusManager:
    """设备状态管理器"""

    def __init__(self):
        self.device_statuses: Dict[str, dict] = {}

    def update_status(self, device_id: str, status_data: dict):
        """更新设备状态"""
        self.device_statuses[device_id] = {
            "status": status_data.get("status", "unknown"),
            "cpu_usage": status_data.get("cpu_usage"),
            "memory_usage": status_data.get("memory_usage"),
            "disk_usage": status_data.get("disk_usage"),
            "temperature": status_data.get("temperature"),
            "ip_address": status_data.get("ip_address"),
            "firmware_version": status_data.get("firmware_version"),
            "last_update": datetime.now(timezone.utc).isoformat()
        }
        logger.info(f"Device {device_id} status updated: {status_data}")

    def get_status(self, device_id: str) -> Optional[dict]:
        """获取设备状态"""
        return self.device_statuses.get(device_id)


status_manager = DeviceStatusManager()


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.device_sessions: Dict[str, dict] = {}

    async def connect(self, device_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[device_id] = websocket
        self.device_sessions[device_id] = {
            "connected_at": datetime.now(timezone.utc),
            "last_batch_id": None,
            "last_batch_time": None,
            "last_status_request": datetime.now(timezone.utc)
        }
        logger.info(f"Device {device_id} connected via WebSocket")

    def disconnect(self, device_id: str):
        if device_id in self.active_connections:
            del self.active_connections[device_id]
        if device_id in self.device_sessions:
            del self.device_sessions[device_id]
        logger.info(f"Device {device_id} disconnected")

    def get_connection(self, device_id: str) -> WebSocket:
        return self.active_connections.get(device_id)

    def update_session(self, device_id: str, batch_id: str):
        if device_id in self.device_sessions:
            self.device_sessions[device_id]["last_batch_id"] = batch_id
            self.device_sessions[device_id]["last_batch_time"] = datetime.now(timezone.utc)

    def should_request_status(self, device_id: str) -> bool:
        """检查是否应该请求设备状态（每time_gap一次）"""
        if device_id not in self.device_sessions:
            return True

        last_request = self.device_sessions[device_id].get("last_status_request")
        if not last_request:
            return True

        now = datetime.now(timezone.utc)
        elapsed = (now - last_request).total_seconds()

        return elapsed >= TIME_GAP_MINUTES * 60

    def mark_status_requested(self, device_id: str):
        """标记已请求设备状态"""
        if device_id in self.device_sessions:
            self.device_sessions[device_id]["last_status_request"] = datetime.now(timezone.utc)


manager = ConnectionManager()


def verify_device_token(device_id: str, upload_token: str) -> bool:
    """验证设备上传Token"""
    with db_config.get_session() as session:
        result = session.execute(
            select(Device).where(
                Device.device_id == UUID(device_id),
                Device.device_upload_token == upload_token
            )
        )
        device = result.scalar_one_or_none()
        return device is not None


def get_device_manager_id(device_id: str) -> Optional[UUID]:
    """获取设备负责人ID"""
    with db_config.get_session() as session:
        result = session.execute(
            select(Device).where(Device.device_id == UUID(device_id))
        )
        device = result.scalar_one_or_none()
        if device:
            return device.device_manager
        return None


def get_device_info(device_id: str) -> tuple:
    """获取设备信息 (device_name, manager_id)"""
    with db_config.get_session() as session:
        result = session.execute(
            select(Device).where(Device.device_id == UUID(device_id))
        )
        device = result.scalar_one_or_none()
        if device:
            return device.device_name, device.device_manager
        return None, None


def generate_batch_id() -> str:
    """生成检测批次ID: BTH[year][month][day][hour][min//time_gap+1]"""
    now = datetime.now(timezone.utc)
    batch_num = now.minute // TIME_GAP_MINUTES + 1
    return f"BTH{now.year:04d}{now.month:02d}{now.day:02d}{now.hour:02d}{batch_num:02d}"


def get_or_create_detection_record(device_id: str, batch_id: str) -> tuple[DetectionRecord, bool]:
    """获取或创建检测记录，返回(记录, 是否新建)"""
    with db_config.get_session() as session:
        result = session.execute(
            select(DetectionRecord).where(
                DetectionRecord.record_batch_id == batch_id,
                DetectionRecord.device_id == UUID(device_id)
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            return existing, False

        record = DetectionRecord(
            record_batch_id=batch_id,
            device_id=UUID(device_id),
            detect_count=0,
            pass_count=0,
            detect_info=[]
        )
        session.add(record)
        session.commit()
        session.refresh(record)
        return record, True


def update_detection_record_stats(batch_id: str, device_id: str, has_defect: bool, defect_type_counts: dict):
    """更新检测记录的统计数据"""
    with db_config.get_session() as session:
        result = session.execute(
            select(DetectionRecord).where(
                DetectionRecord.record_batch_id == batch_id,
                DetectionRecord.device_id == UUID(device_id)
            )
        )
        record = result.scalar_one_or_none()

        if record:
            record.detect_count = (record.detect_count or 0) + 1
            if not has_defect:
                record.pass_count = (record.pass_count or 0) + 1

            current_info = record.detect_info or []
            for defect_type_id, count in defect_type_counts.items():
                found = False
                for item in current_info:
                    if item.get("defect_type_id") == defect_type_id:
                        item["defect_count"] = item.get("defect_type_id", 0) + count
                        found = True
                        break
                if not found:
                    current_info.append({
                        "defect_type_id": defect_type_id,
                        "defect_count": count
                    })

            record.detect_info = current_info
            record.latest_upload_at = datetime.now(timezone.utc)
            session.commit()


def create_defect_and_review_task(record_batch_id: str, device_id: str, device_name: str,
                                   original_img: str, defect_count: int, details: list,
                                   assignee_id: UUID) -> DefectDetail:
    """创建缺陷详情和审查任务"""
    with db_config.get_session() as session:
        defect_detail = DefectDetail(
            defect_details_id=uuid4(),
            record_batch_id=record_batch_id,
            original_img=original_img,
            defect_count=defect_count,
            details=details
        )
        session.add(defect_detail)
        session.flush()

        review_task = ReviewTask(
            review_task_id=uuid4(),
            defect_details_id=defect_detail.defect_details_id,
            assignee_id=assignee_id,
            assignee_at=datetime.now(timezone.utc)
        )
        session.add(review_task)
        session.commit()
        session.refresh(defect_detail)

        logger.info(f"Created defect detail {defect_detail.defect_details_id} and review task {review_task.review_task_id}")

        defect_types_info = []
        for detail in details:
            defect_types_info.append(f"缺陷类型{detail.get('class_id')}")

        message_content = (
            f"🚨 设备异常告警\n\n"
            f"设备名称: {device_name}\n"
            f"设备ID: {device_id}\n"
            f"检测批次: {record_batch_id}\n"
            f"缺陷数量: {defect_count}\n"
            f"缺陷类型: {', '.join(defect_types_info) if defect_types_info else '未知'}\n"
            f"请及时处理！"
        )
        SystemMessageService.create_message(assignee_id, message_content)
        logger.info(f"Sent defect alert message to device manager {assignee_id} for device {device_name}")

        return defect_detail


async def status_request_loop(device_id: str, websocket: WebSocket):
    """定期请求设备状态的协程"""
    while True:
        try:
            await asyncio.sleep(TIME_GAP_MINUTES * 60)

            if device_id not in manager.active_connections:
                break

            await websocket.send_json({
                "type": "status_request",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "message": "请上报设备状态"
            })
            logger.debug(f"Sent status request to device {device_id}")

        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Error in status request loop for device {device_id}: {e}")
            break


@router.websocket("/ws/detection")
async def detection_websocket(
    websocket: WebSocket,
    device_id: str = Query(...),
    upload_token: str = Query(...)
):
    if not verify_device_token(device_id, upload_token):
        await websocket.close(code=4001, reason="Invalid device credentials")
        return

    await manager.connect(device_id, websocket)

    status_task = asyncio.create_task(status_request_loop(device_id, websocket))

    try:
        while True:
            data = await websocket.receive_text()

            try:
                message = json.loads(data)

                if message.get("type") == "image":
                    image_data = message.get("data")
                    if not image_data:
                        continue

                    image_bytes = base64.b64decode(image_data)
                    detection_results = yolo_detector.detect(image_bytes)

                    has_defect = len(detection_results) > 0
                    defect_type_counts = {}

                    for result in detection_results:
                        defect_type_id = result.get("class_id")
                        defect_type_counts[defect_type_id] = defect_type_counts.get(defect_type_id, 0) + 1

                    batch_id = generate_batch_id()
                    record, is_new = get_or_create_detection_record(device_id, batch_id)

                    if has_defect:
                        device_name, manager_device_id = get_device_info(device_id)
                        if manager_device_id:
                            defect_details = [{
                                "xyhw": (r["x"], r["y"], r["width"], r["height"]),
                                "conf": r["confidence"],
                                "class_id": r["class_id"]
                            } for r in detection_results]

                            create_defect_and_review_task(
                                record_batch_id=batch_id,
                                device_id=device_id,
                                device_name=device_name or "未知设备",
                                original_img=f"data:image/jpeg;base64,{image_data[:100]}...",
                                defect_count=len(detection_results),
                                details=defect_details,
                                assignee_id=manager_device_id
                            )

                    update_detection_record_stats(batch_id, device_id, has_defect, defect_type_counts)
                    manager.update_session(device_id, batch_id)

                    await websocket.send_json({
                        "type": "detection_result",
                        "batch_id": batch_id,
                        "has_defect": has_defect,
                        "detect_count": len(detection_results),
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })

                elif message.get("type") == "status":
                    status_data = message.get("data", {})
                    status_manager.update_status(device_id, status_data)
                    await websocket.send_json({
                        "type": "status_ack",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })

                elif message.get("type") == "ping":
                    await websocket.send_json({"type": "pong", "timestamp": datetime.now(timezone.utc).isoformat()})

            except json.JSONDecodeError:
                logger.error(f"Invalid JSON received from device {device_id}")
            except Exception as e:
                logger.error(f"Error processing message from device {device_id}: {e}")

    except WebSocketDisconnect:
        manager.disconnect(device_id)
        status_task.cancel()
        logger.info(f"Device {device_id} WebSocket disconnected")


@router.get("/detection/stats")
async def get_detection_stats(device_id: str):
    """获取设备检测统计（供设备查询）"""
    with db_config.get_session() as session:
        result = session.execute(
            select(DetectionRecord)
            .where(DetectionRecord.device_id == UUID(device_id))
            .order_by(DetectionRecord.latest_upload_at.desc())
            .limit(10)
        )
        records = result.scalars().all()

        total_detect = sum(r.detect_count or 0 for r in records)
        total_pass = sum(r.pass_count or 0 for r in records)

        return {
            "device_id": device_id,
            "total_detect": total_detect,
            "total_pass": total_pass,
            "total_defect": total_detect - total_pass,
            "recent_records": [
                {
                    "batch_id": r.record_batch_id,
                    "detect_count": r.detect_count,
                    "pass_count": r.pass_count,
                    "detect_info": r.detect_info,
                    "latest_upload_at": r.latest_upload_at.isoformat() if r.latest_upload_at else None
                }
                for r in records
            ]
        }


@router.get("/detection/device-status/{device_id}")
async def get_device_status(device_id: str):
    """获取设备状态"""
    status = status_manager.get_status(device_id)
    if not status:
        return {
            "device_id": device_id,
            "status": "offline",
            "message": "设备未连接或未上报状态"
        }
    return {
        "device_id": device_id,
        **status
    }


@router.post("/detection/demo")
async def demo_detection(image_data: str = Query(..., description="Base64编码的图片数据")):
    """演示接口 - 直接检测图片，无需设备认证

    用于快速测试YOLO检测功能。

    参数:
        image_data: Base64编码的图片数据

    返回:
        检测结果列表
    """
    try:
        image_bytes = base64.b64decode(image_data)
        detection_results = yolo_detector.detect(image_bytes)

        return {
            "success": True,
            "has_defect": len(detection_results) > 0,
            "detect_count": len(detection_results),
            "detections": detection_results,
            "message": "检测完成" if detection_results else "未检测到缺陷"
        }
    except Exception as e:
        logger.error(f"Demo detection error: {e}")
        return {
            "success": False,
            "error": str(e),
            "has_defect": False,
            "detect_count": 0,
            "detections": []
        }


@router.websocket("/ws/detection/demo")
async def websocket_demo(websocket: WebSocket):
    """演示用WebSocket接口 - 无需设备认证，用于视频流处理

    适用于处理视频数据，可以每秒处理多张图片。

    客户端消息格式:
    {
      "type": "image",
      "data": "<base64编码的图片数据>",
      "frame_id": 123  // 可选，用于标识帧
    }

    服务器响应格式:
    {
      "type": "detection_result",
      "frame_id": 123,  // 如果客户端提供了frame_id
      "has_defect": true,
      "detect_count": 3,
      "detections": [...],
      "timestamp": "2026-05-02T10:30:45.123456Z"
    }
    """
    await websocket.accept()
    logger.info("Demo WebSocket connection established")

    frame_count = 0
    start_time = time.time()

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            if message.get("type") == "image":
                frame_id = message.get("frame_id")
                image_data = message.get("data")

                if not image_data:
                    await websocket.send_json({
                        "type": "error",
                        "message": "No image data provided"
                    })
                    continue

                try:
                    image_bytes = base64.b64decode(image_data)
                    detection_results = yolo_detector.detect(image_bytes)

                    frame_count += 1

                    response = {
                        "type": "detection_result",
                        "has_defect": len(detection_results) > 0,
                        "detect_count": len(detection_results),
                        "detections": detection_results,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }

                    if frame_id is not None:
                        response["frame_id"] = frame_id

                    await websocket.send_json(response)

                    # 每处理100帧记录一次FPS
                    if frame_count % 100 == 0:
                        elapsed = time.time() - start_time
                        fps = frame_count / elapsed if elapsed > 0 else 0
                        logger.info(f"Demo WebSocket: Processed {frame_count} frames, {fps:.2f} FPS")

                except Exception as e:
                    logger.error(f"Demo detection error: {e}")
                    await websocket.send_json({
                        "type": "error",
                        "message": str(e)
                    })

            elif message.get("type") == "ping":
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })

            elif message.get("type") == "reset_stats":
                frame_count = 0
                start_time = time.time()
                await websocket.send_json({
                    "type": "stats_reset",
                    "message": "Statistics reset"
                })

            elif message.get("type") == "get_stats":
                elapsed = time.time() - start_time
                fps = frame_count / elapsed if elapsed > 0 else 0
                await websocket.send_json({
                    "type": "stats",
                    "frame_count": frame_count,
                    "elapsed_seconds": elapsed,
                    "fps": fps
                })

    except WebSocketDisconnect:
        logger.info("Demo WebSocket disconnected")
    except Exception as e:
        logger.error(f"Demo WebSocket error: {e}")

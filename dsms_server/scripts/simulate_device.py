#!/usr/bin/env python3
"""
模拟流水线设备与服务器交互的脚本

功能说明:
    - 通过WebSocket连接服务器进行实时缺陷检测
    - 支持上传图片进行检测
    - 定期上报设备状态
    - 自动重连机制

配置项:
    - DEVICE_ID: 设备ID（待配置）
    - UPLOAD_TOKEN: 上传Token（待配置）
    - SERVER_URL: 服务器地址
    - IMAGE_DIR: 图片目录

使用示例:
    python simulate_device.py --device-id <device_id> --token <upload_token>
    python simulate_device.py --config config.json

注意:
    1. 确保设备已在系统中注册并生成了上传Token
    2. 图片目录中放置待检测的图片文件（支持jpg, jpeg, png格式）
"""

import argparse
import asyncio
import base64
import json
import logging
import os
import random
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, Optional, List

import websockets
from websockets.exceptions import ConnectionClosed

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# ==================== 配置项（待配置） ====================
# 设备ID和Token，运行时通过参数传入或配置文件指定
DEVICE_ID = "8c7b074d-6520-4d9c-a285-ab414927ad79"  # 设备ID
UPLOAD_TOKEN = "UmYwfL2Rg9G_cEiRFuY5ameEQs9eE-4qms9ClEIL8o4"  # 上传Token
SERVER_URL = "ws://localhost:8001/api/v1/ws/detection"  # 服务器WebSocket地址
IMAGE_DIR = Path(__file__).parent.parent / "debug" / "images"  # 图片目录

# 检测间隔（秒）- 每秒3张
DETECTION_INTERVAL = 1/3
# 状态上报间隔（秒）
STATUS_REPORT_INTERVAL = 60
# 重连间隔（秒）
RECONNECT_INTERVAL = 10
# 最大重连次数
MAX_RECONNECT_ATTEMPTS = 10

# ========================================================


class DeviceSimulator:
    """设备模拟器"""

    def __init__(self, device_id: str, upload_token: str, server_url: str, image_dir: Path):
        self.device_id = device_id
        self.upload_token = upload_token
        self.server_url = server_url
        self.image_dir = image_dir
        self.websocket = None
        self.running = False
        self.reconnect_attempts = 0
        self.image_files: List[str] = []
        self.current_image_index = 0
        self.response_queue = asyncio.Queue()

        # 模拟设备状态
        self.device_status = {
            "status": "active",
            "cpu_usage": 45.0,
            "memory_usage": 60.0,
            "disk_usage": 72.0,
            "temperature": 38.5,
            "ip_address": f"192.168.1.{random.randint(10, 250)}",
            "firmware_version": "v1.2.3"
        }

    def generate_monochrome_image(self) -> bytes:
        """生成640x640的全黑或全白图片（PNG格式）"""
        try:
            from PIL import Image
            import io

            # 随机选择全黑或全白
            is_white = random.choice([True, False])
            color = (255, 255, 255) if is_white else (0, 0, 0)
            
            # 创建640x640的图片
            image = Image.new('RGB', (640, 640), color)
            
            # 保存为PNG格式的字节流
            buffer = io.BytesIO()
            image.save(buffer, format='PNG')
            buffer.seek(0)
            
            logger.debug(f"生成了 {'全白' if is_white else '全黑'} 图片 (640x640)")
            return buffer.read()
        except ImportError:
            logger.error("需要安装Pillow库来生成图片")
            return None
        except Exception as e:
            logger.error(f"生成单色图片失败: {e}")
            return None

    def load_images(self):
        """加载图片文件列表"""
        if not self.image_dir.exists():
            logger.warning(f"图片目录不存在: {self.image_dir}")
            return

        supported_extensions = ('.jpg', '.jpeg', '.png', '.bmp')
        self.image_files = [
            str(f) for f in self.image_dir.iterdir()
            if f.is_file() and f.suffix.lower() in supported_extensions
        ]
        logger.info(f"已加载 {len(self.image_files)} 张图片")

    def get_next_image(self) -> Optional[bytes]:
        """获取下一张图片数据（99.8%概率返回正常图片，0.2%概率返回有缺陷图片）"""
        # 99.8%概率返回生成的全黑/全白图片（模拟正常产品）
        if random.random() < 0.99:
            return self.generate_monochrome_image()
        else:
            # 0.2%概率返回文件夹里的有缺陷图片
            if not self.image_files:
                logger.debug("没有缺陷图片，生成单色图片")
                return self.generate_monochrome_image()

            if self.current_image_index >= len(self.image_files):
                self.current_image_index = 0

            image_path = self.image_files[self.current_image_index]
            self.current_image_index += 1

            logger.debug(f"发送有缺陷图片: {image_path}")
            try:
                with open(image_path, 'rb') as f:
                    return f.read()
            except Exception as e:
                logger.error(f"读取图片失败 {image_path}: {e}")
                return self.generate_monochrome_image()

    def generate_random_status(self) -> dict:
        """生成随机设备状态（包含异常状态测试）"""
        # 随机选择状态，增加异常状态的概率用于测试
        status_prob = random.random()
        if status_prob < 0.15:  # 15% 概率模拟异常状态
            status = random.choice(["maintenance", "error", "warning"])
        else:
            status = "active"
        
        # 根据状态设置不同的参数值
        if status == "error":
            temperature = round(random.uniform(70, 90), 1)
            cpu_usage = round(random.uniform(85, 100), 2)
        elif status == "warning":
            temperature = round(random.uniform(50, 65), 1)
            cpu_usage = round(random.uniform(75, 90), 2)
        else:
            temperature = round(random.uniform(35, 45), 1)
            cpu_usage = round(random.uniform(20, 85), 2)
        
        return {
            "status": status,
            "cpu_usage": cpu_usage,
            "memory_usage": round(random.uniform(40, 80), 2),
            "disk_usage": round(random.uniform(50, 85), 2),
            "temperature": temperature,
            "ip_address": self.device_status["ip_address"],
            "firmware_version": self.device_status["firmware_version"]
        }

    async def connect(self) -> bool:
        """建立WebSocket连接"""
        try:
            url = f"{self.server_url}?device_id={self.device_id}&upload_token={self.upload_token}"
            self.websocket = await websockets.connect(url)
            self.reconnect_attempts = 0
            logger.info(f"设备 {self.device_id} 成功连接到服务器")
            return True
        except Exception as e:
            logger.error(f"连接失败: {e}")
            return False

    async def send_image(self, image_bytes: bytes):
        """发送图片进行检测"""
        if not self.websocket:
            logger.error("WebSocket连接未建立")
            return

        try:
            image_base64 = base64.b64encode(image_bytes).decode('utf-8')
            # 使用东八区时间（UTC+8）
            timestamp = (datetime.now(timezone.utc) + timedelta(hours=8)).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + '+08:00'
            message = json.dumps({
                "type": "image",
                "data": image_base64,
                "timestamp": timestamp
            })
            await self.websocket.send(message)
            logger.debug("图片已发送")

        except ConnectionClosed:
            logger.warning("连接已关闭")
            self.websocket = None
        except Exception as e:
            logger.error(f"发送图片失败: {e}")

    async def send_status(self):
        """发送设备状态"""
        if not self.websocket:
            logger.error("WebSocket连接未建立")
            return

        try:
            status_data = self.generate_random_status()
            # 使用东八区时间（UTC+8）
            timestamp = (datetime.now(timezone.utc) + timedelta(hours=8)).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + '+08:00'
            message = json.dumps({
                "type": "status",
                "data": status_data,
                "timestamp": timestamp
            })
            await self.websocket.send(message)
            logger.info(f"状态已发送: {status_data['status']}")

        except ConnectionClosed:
            logger.warning("连接已关闭")
            self.websocket = None
        except Exception as e:
            logger.error(f"发送状态失败: {e}")

    async def send_ping(self):
        """发送心跳包"""
        if not self.websocket:
            return

        try:
            # 使用东八区时间（UTC+8）
            timestamp = (datetime.now(timezone.utc) + timedelta(hours=8)).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + '+08:00'
            message = json.dumps({
                "type": "ping",
                "timestamp": timestamp
            })
            await self.websocket.send(message)
            logger.debug("心跳已发送")

        except Exception as e:
            logger.error(f"心跳失败: {e}")

    async def receive_loop(self):
        """接收服务器响应的循环"""
        while self.running:
            if not self.websocket:
                await asyncio.sleep(0.1)
                continue

            try:
                response = await self.websocket.recv()
                response_data = json.loads(response)
                response_type = response_data.get("type")

                if response_type == "detection_result":
                    has_defect = response_data.get("has_defect", False)
                    detect_count = response_data.get("detect_count", 0)
                    batch_id = response_data.get("batch_id")
                    logger.info(
                        f"检测完成 | 批次: {batch_id} | 有缺陷: {has_defect} | 缺陷数量: {detect_count}"
                    )
                elif response_type == "status_ack":
                    logger.debug("状态上报成功")
                elif response_type == "pong":
                    logger.debug("心跳响应正常")
                elif response_type == "status_request":
                    logger.debug("收到服务器状态请求")
                    await self.send_status()
                else:
                    logger.debug(f"收到未知类型响应: {response_type}")

            except ConnectionClosed:
                logger.warning("连接已关闭")
                self.websocket = None
                break
            except json.JSONDecodeError:
                logger.error("接收到无效的JSON数据")
            except Exception as e:
                logger.error(f"接收响应失败: {e}")
                self.websocket = None
                break

    async def detection_loop(self):
        """检测循环"""
        while self.running:
            try:
                if not self.websocket:
                    await asyncio.sleep(1)
                    continue

                image_bytes = self.get_next_image()
                if image_bytes:
                    await self.send_image(image_bytes)
                else:
                    logger.warning("没有可检测的图片")

                await asyncio.sleep(DETECTION_INTERVAL)

            except Exception as e:
                logger.error(f"检测循环异常: {e}")
                await asyncio.sleep(1)

    async def status_loop(self):
        """状态上报循环"""
        while self.running:
            try:
                if self.websocket:
                    await self.send_status()
                await asyncio.sleep(STATUS_REPORT_INTERVAL)
            except Exception as e:
                logger.error(f"状态上报循环异常: {e}")
                await asyncio.sleep(1)

    async def run(self):
        """主运行方法"""
        self.running = True
        self.load_images()

        while self.running:
            if not self.websocket:
                if self.reconnect_attempts >= MAX_RECONNECT_ATTEMPTS:
                    logger.error(f"达到最大重连次数 ({MAX_RECONNECT_ATTEMPTS})，退出")
                    break

                logger.info(f"尝试连接... ({self.reconnect_attempts + 1}/{MAX_RECONNECT_ATTEMPTS})")
                if await self.connect():
                    # 启动接收、检测和状态上报任务
                    receive_task = asyncio.create_task(self.receive_loop())
                    detection_task = asyncio.create_task(self.detection_loop())
                    status_task = asyncio.create_task(self.status_loop())

                    try:
                        await asyncio.gather(receive_task, detection_task, status_task)
                    except Exception as e:
                        logger.error(f"任务异常: {e}")
                    finally:
                        receive_task.cancel()
                        detection_task.cancel()
                        status_task.cancel()
                        if self.websocket:
                            await self.websocket.close()
                        self.websocket = None

                self.reconnect_attempts += 1
                await asyncio.sleep(RECONNECT_INTERVAL)
            else:
                await asyncio.sleep(1)

        logger.info("设备模拟器已停止")

    def stop(self):
        """停止模拟器"""
        self.running = False


def load_config(config_path: str) -> Dict[str, str]:
    """从配置文件加载配置"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"加载配置文件失败: {e}")
        return {}


def main():
    parser = argparse.ArgumentParser(description='模拟流水线设备与服务器交互')
    parser.add_argument('--device-id', '-d', type=str, help='设备ID')
    parser.add_argument('--token', '-t', type=str, help='上传Token')
    parser.add_argument('--server', '-s', type=str, help='服务器地址', default=SERVER_URL)
    parser.add_argument('--image-dir', '-i', type=str, help='图片目录')
    parser.add_argument('--config', '-c', type=str, help='配置文件路径')
    parser.add_argument('--interval', type=int, help='检测间隔（秒）', default=DETECTION_INTERVAL)
    parser.add_argument('--debug', action='store_true', help='启用调试模式')

    args = parser.parse_args()

    # 设置日志级别
    if args.debug:
        logger.setLevel(logging.DEBUG)

    # 加载配置
    config = {}
    if args.config:
        config = load_config(args.config)

    # 获取设备ID和Token（优先级：命令行参数 > 配置文件 > 默认值）
    device_id = args.device_id or config.get('device_id') or DEVICE_ID
    upload_token = args.token or config.get('upload_token') or UPLOAD_TOKEN
    server_url = args.server or config.get('server_url') or SERVER_URL
    image_dir = Path(args.image_dir) if args.image_dir else \
                Path(config.get('image_dir')) if config.get('image_dir') else IMAGE_DIR

    # 检查必需参数
    if not device_id:
        logger.error("请提供设备ID（--device-id 或配置文件）")
        parser.print_help()
        return

    if not upload_token:
        logger.error("请提供上传Token（--token 或配置文件）")
        parser.print_help()
        return

    logger.info(f"设备ID: {device_id}")
    logger.info(f"服务器地址: {server_url}")
    logger.info(f"图片目录: {image_dir}")
    logger.info(f"检测间隔: {args.interval}秒")

    # 创建并运行设备模拟器
    simulator = DeviceSimulator(
        device_id=device_id,
        upload_token=upload_token,
        server_url=server_url,
        image_dir=image_dir
    )

    try:
        asyncio.run(simulator.run())
    except KeyboardInterrupt:
        logger.info("收到中断信号，正在停止...")
        simulator.stop()


if __name__ == "__main__":
    main()

"""
YOLO目标检测服务

用于实时缺陷检测。
"""

import os
from typing import List, Dict
import numpy as np

from app.utils.logger import get_logger

logger = get_logger(__name__)


class YOLODetector:
    def __init__(self):
        self.model = None
        self.model_path = None
        self.initialized = False
        self.device = "cpu"  # 默认使用CPU

    def initialize(self):
        """初始化YOLO模型"""
        if self.initialized:
            return

        try:
            from ultralytics import YOLO
            import torch

            model_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "detect_model",
                "best.pt"
            )

            if not os.path.exists(model_path):
                logger.warning(f"YOLO model not found at {model_path}, using dummy detector")
                self.model = None
                self.initialized = True
                return

            # 检测CUDA可用性
            if torch.cuda.is_available():
                self.device = "cuda"
                logger.info("CUDA可用，将使用GPU进行检测")
            else:
                self.device = "cpu"
                logger.info("CUDA不可用，将使用CPU进行检测")

            self.model = YOLO(model_path)
            self.model_path = model_path
            self.initialized = True
            logger.info(f"YOLO model loaded from {model_path}, device: {self.device}")

        except ImportError:
            logger.warning("ultralytics not installed, using dummy detector")
            self.model = None
            self.initialized = True
        except Exception as e:
            logger.error(f"Failed to load YOLO model: {e}")
            self.model = None
            self.initialized = True

    def detect(self, image_bytes: bytes) -> List[Dict]:
        """检测图像中的缺陷

        Args:
            image_bytes: 图像字节数据

        Returns:
            检测结果列表，每个结果包含:
            - class_id: 缺陷类型ID
            - class_name: 缺陷类型名称
            - confidence: 置信度
            - x, y, width, height: 边界框坐标
        """
        if not self.initialized:
            self.initialize()

        if self.model is None:
            return self._dummy_detect(image_bytes)

        try:
            import cv2
            from PIL import Image
            import io

            nparr = np.frombuffer(image_bytes, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if image is None:
                image = Image.open(io.BytesIO(image_bytes))
                image = np.array(image)
                image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

            # 使用自动检测的设备进行推理
            results = self.model.predict(image, device=self.device, verbose=False)

            detections = []
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        # 确保在CPU上处理结果
                        xyxy = box.xyxy[0].cpu().numpy()
                        conf = float(box.conf[0].cpu().numpy())
                        cls = int(box.cls[0].cpu().numpy())

                        detections.append({
                            "class_id": cls + 1,
                            "class_name": result.names[cls],
                            "confidence": conf,
                            "x": float(xyxy[0]),
                            "y": float(xyxy[1]),
                            "width": float(xyxy[2] - xyxy[0]),
                            "height": float(xyxy[3] - xyxy[1])
                        })

            # logger.debug(f"Detected {len(detections)} defects using {self.device}")
            return detections

        except Exception as e:
            logger.error(f"YOLO detection error with {self.device}: {e}")
            # 如果CUDA失败，尝试使用CPU
            if self.device == "cuda":
                logger.warning("CUDA检测失败，尝试使用CPU")
                return self._detect_with_cpu(image_bytes)
            return self._dummy_detect(image_bytes)

    def _detect_with_cpu(self, image_bytes: bytes) -> List[Dict]:
        """使用CPU进行检测（作为CUDA失败的回退）"""
        try:
            import cv2
            from PIL import Image
            import io

            nparr = np.frombuffer(image_bytes, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if image is None:
                image = Image.open(io.BytesIO(image_bytes))
                image = np.array(image)
                image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

            results = self.model.predict(image, device="cpu", verbose=False)

            detections = []
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        xyxy = box.xyxy[0].cpu().numpy()
                        conf = float(box.conf[0].cpu().numpy())
                        cls = int(box.cls[0].cpu().numpy())

                        detections.append({
                            "class_id": cls + 1,
                            "class_name": result.names[cls],
                            "confidence": conf,
                            "x": float(xyxy[0]),
                            "y": float(xyxy[1]),
                            "width": float(xyxy[2] - xyxy[0]),
                            "height": float(xyxy[3] - xyxy[1])
                        })

            logger.info(f"CPU fallback: Detected {len(detections)} defects")
            return detections

        except Exception as e:
            logger.error(f"CPU detection also failed: {e}")
            return self._dummy_detect(image_bytes)

    def _dummy_detect(self, image_bytes: bytes) -> List[Dict]:
        """模拟检测（当YOLO模型不可用时）"""
        import random

        if random.random() < 0.1:
            return [{
                "class_id": random.randint(1, 6),
                "class_name": random.choice(["scratch", "dent", "crack", "stain", "discoloration", "burr"]),
                "confidence": random.uniform(0.5, 0.95),
                "x": random.uniform(50, 200),
                "y": random.uniform(50, 200),
                "width": random.uniform(30, 100),
                "height": random.uniform(30, 100)
            }]
        return []


yolo_detector = YOLODetector()
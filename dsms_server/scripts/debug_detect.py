#!/usr/bin/env python3
"""
YOLO缺陷检测调试脚本

用于测试YOLO模型对缺陷图片的检测效果。

使用示例:
    python debug_detect.py                           # 检测默认图片
    python debug_detect.py --image path/to/image.jpg  # 检测指定图片
"""

import argparse
import os
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def test_ultralytics_import():
    """测试ultralytics导入"""
    print("\n[DEBUG] 测试ultralytics导入...")
    try:
        from ultralytics import YOLO
        print(f"  ✓ ultralytics导入成功")
        import ultralytics
        print(f"  ✓ ultralytics版本: {ultralytics.__version__}")
        return True
    except ImportError as e:
        print(f"  ✗ ultralytics导入失败: {e}")
        return False
    except Exception as e:
        print(f"  ✗ 未知错误: {e}")
        return False


def test_model_path():
    """测试模型路径"""
    print("\n[DEBUG] 测试模型路径...")
    model_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "detect_model",
        "best.pt"
    )
    print(f"  模型路径: {model_path}")
    if os.path.exists(model_path):
        file_size = os.path.getsize(model_path) / (1024 * 1024)
        print(f"  ✓ 模型文件存在，大小: {file_size:.2f} MB")
        return model_path
    else:
        print(f"  ✗ 模型文件不存在")
        return None


def test_cuda():
    """测试CUDA可用性"""
    print("\n[DEBUG] 测试CUDA可用性...")
    try:
        import torch
        print(f"  PyTorch版本: {torch.__version__}")
        if torch.cuda.is_available():
            print(f"  ✓ CUDA可用")
            print(f"  GPU数量: {torch.cuda.device_count()}")
            print(f"  当前GPU: {torch.cuda.get_device_name(0)}")
            return True
        else:
            print(f"  ✗ CUDA不可用，将使用CPU")
            return False
    except ImportError as e:
        print(f"  ✗ PyTorch未安装: {e}")
        return False


def test_image(image_path):
    """测试图片加载"""
    print(f"\n[DEBUG] 测试图片加载: {image_path}")
    if not os.path.exists(image_path):
        print(f"  ✗ 图片不存在")
        return None
    
    try:
        with open(image_path, 'rb') as f:
            image_bytes = f.read()
        print(f"  ✓ 图片加载成功，大小: {len(image_bytes)} bytes")
        
        # 测试OpenCV加载
        import cv2
        import numpy as np
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if image is not None:
            print(f"  ✓ OpenCV解码成功，尺寸: {image.shape}")
        else:
            print(f"  ✗ OpenCV解码失败")
        
        return image_bytes
    except Exception as e:
        print(f"  ✗ 图片加载失败: {e}")
        traceback.print_exc()
        return None


def run_detection(image_bytes, model_path, use_cuda):
    """运行实际检测"""
    print("\n[DEBUG] 运行YOLO检测...")
    try:
        from ultralytics import YOLO
        import cv2
        import numpy as np
        
        print(f"  加载模型: {model_path}")
        device = "cuda" if use_cuda else "cpu"
        print(f"  使用设备: {device}")
        
        model = YOLO(model_path)
        print(f"  ✓ 模型加载成功")
        
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        print(f"  开始检测...")
        if image is None:
            print(f"  ✗ 图片解码失败，无法进行检测")
            return None
        results = model.predict(image, device=device, verbose=False)
        print(f"  ✓ 检测完成")
        
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
        
        print(f"  检测到 {len(detections)} 个缺陷")
        return detections
        
    except Exception as e:
        print(f"  ✗ 检测失败: {e}")
        traceback.print_exc()
        return None


def main():
    parser = argparse.ArgumentParser(description='YOLO缺陷检测调试脚本')
    parser.add_argument('--image', '-i', 
                        default=os.path.join(os.path.dirname(__file__), 'sample_017_original.jpg'),
                        help='待检测的图片路径')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("YOLO缺陷检测调试脚本 - 详细模式")
    print("=" * 60)
    print(f"\n待检测图片: {args.image}")
    
    # 1. 测试ultralytics导入
    has_ultralytics = test_ultralytics_import()
    
    # 2. 测试模型路径
    model_path = test_model_path()
    
    # 3. 测试CUDA
    has_cuda = test_cuda()
    
    # 4. 测试图片
    image_bytes = test_image(args.image)
    
    # 5. 运行检测（如果所有依赖都满足）
    if has_ultralytics and model_path and image_bytes:
        detections = run_detection(image_bytes, model_path, has_cuda)
        
        print("\n" + "=" * 60)
        print("检测结果")
        print("=" * 60)
        
        if detections is None:
            print("检测过程出错")
        elif not detections:
            print("未检测到缺陷")
        else:
            print(f"共检测到 {len(detections)} 个缺陷:")
            print()
            
            for i, detection in enumerate(detections, 1):
                print(f"缺陷 #{i}:")
                print(f"  类型ID: {detection['class_id']}")
                print(f"  类型名称: {detection['class_name']}")
                print(f"  置信度: {detection['confidence']:.4f}")
                print(f"  位置: x={detection['x']:.2f}, y={detection['y']:.2f}")
                print(f"  尺寸: width={detection['width']:.2f}, height={detection['height']:.2f}")
                print()
    else:
        print("\n" + "=" * 60)
        print("无法执行检测，缺少必要依赖")
        print("=" * 60)
        print(f"  ultralytics: {'✓ 已安装' if has_ultralytics else '✗ 未安装'}")
        print(f"  模型文件: {'✓ 存在' if model_path else '✗ 不存在'}")
        print(f"  图片文件: {'✓ 存在' if image_bytes else '✗ 不存在'}")


if __name__ == '__main__':
    main()
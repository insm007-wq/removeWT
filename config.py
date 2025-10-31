"""
Configuration settings for Watermark Removal System
"""

import os
from pathlib import Path

# .env 파일 로드
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass  # python-dotenv 설치 안됨 - 환경변수만 사용

# API 설정
REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN", "")  # Replicate API token

# 디렉토리 설정
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
TEMP_DIR = os.path.join(os.path.dirname(__file__), "temp")
LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")

# 처리 설정
MAX_VIDEO_DURATION = 300  # 최대 비디오 길이 (초)

# 지원 형식
SUPPORTED_FORMATS = ('mp4', 'mov', 'avi', 'mkv', 'webm', 'flv', 'wmv')

# GPU 설정
USE_GPU = True
GPU_ID = 0

# Local GPU Processing 설정
LOCAL_GPU_ENABLED = True  # Local GPU 모드 사용 가능 여부
LOCAL_GPU_DEVICE = 0      # GPU ID (0, 1, 2...)
MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")  # 모델 저장 디렉토리
YOLO_MODEL_PATH = os.path.join(MODELS_DIR, "best.pt")  # YOLOv11s 모델
YOLO_MODEL_URL = "https://github.com/linkedlist771/SoraWatermarkCleaner/releases/download/v1.0/best.pt"
LAMA_MODEL_NAME = "lama"  # IOPaint LAMA 모델 이름 (자동 다운로드)

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

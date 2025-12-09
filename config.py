"""
Configuration settings for Watermark Removal System
"""

import os
from pathlib import Path

# .env 파일 로드
try:
    from dotenv import load_dotenv

    # .env 파일 찾기 (여러 위치 시도)
    env_path = None

    # 1. 현재 작업 디렉토리에서 찾기 (배포 폴더 방식)
    if Path('.env').exists():
        env_path = Path('.env')
    # 2. 스크립트 디렉토리에서 찾기 (개발 환경)
    elif (Path(__file__).parent / '.env').exists():
        env_path = Path(__file__).parent / '.env'
    # 3. 상위 디렉토리에서 찾기
    elif (Path(__file__).parent.parent / '.env').exists():
        env_path = Path(__file__).parent.parent / '.env'

    if env_path and env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass  # python-dotenv 설치 안됨 - 환경변수만 사용

# API 설정
REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN", "")  # Replicate API token

# 디렉토리 설정 (보안: 절대 경로 사용)
PROJECT_ROOT = Path(__file__).parent.resolve()
OUTPUT_DIR = str(PROJECT_ROOT / "output")
TEMP_DIR = str(PROJECT_ROOT / "temp")
LOG_DIR = str(PROJECT_ROOT / "logs")

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
GPU_TYPE = "auto"         # GPU 타입: "auto" (자동 감지), "cuda" (NVIDIA), "rocm" (AMD)
MODELS_DIR = str(PROJECT_ROOT / "models")  # 모델 저장 디렉토리
YOLO_MODEL_PATH = str(Path(MODELS_DIR) / "best.pt")  # YOLOv11s 모델
YOLO_MODEL_URL = "https://github.com/linkedlist771/SoraWatermarkCleaner/releases/download/V0.0.1/best.pt"
LAMA_MODEL_NAME = "lama"  # IOPaint LAMA 모델 이름 (자동 다운로드)

# 성능 최적화 설정
YOLO_CONF_THRESHOLD = 0.3      # YOLO 신뢰도 임계값 (낮을수록 더 많이 탐지, 0.3 = 최고 감지)
YOLO_IOU_THRESHOLD = 0.45      # YOLO IoU 임계값 (낮을수록 더 많이 탐지)
YOLO_HALF_PRECISION = False    # FP16 반정밀도 (CPU는 지원 안함, GPU만 가능)
TORCH_NUM_THREADS = 8          # PyTorch 스레드 수 (CPU 코어 수에 맞춰 설정)
LAMA_GUIDANCE_SCALE = 7.5      # LAMA 가이던스 스케일 (높을수록 정확, 1-20)

# ==================== Video Enhancement Pipeline ====================

# Real-ESRGAN (Stage 1: 공간 해상도 4배 증가)
ESRGAN_MODEL_NAME = "RealESRGAN_x4plus"
ESRGAN_MODEL_PATH = str(Path(MODELS_DIR) / "RealESRGAN_x4plus.pth")
ESRGAN_MODEL_URL = "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth"
ESRGAN_SCALE = 4
ESRGAN_TILE_SIZE = 256
ESRGAN_TILE_PAD = 10
ESRGAN_HALF_PRECISION = True
ESRGAN_PRE_PAD = 0

# CodeFormer (Stage 2: 얼굴 품질 향상)
CODEFORMER_MODEL_PATH = str(Path(MODELS_DIR) / "codeformer.pth")
CODEFORMER_FIDELITY = 0.5  # 0-1 (0.5 = 균형)
CODEFORMER_UPSCALE = 1
CODEFORMER_FACE_UPSAMPLE = False
CODEFORMER_BG_UPSAMPLER = None
CODEFORMER_DETECTION_MODEL = "retinaface_resnet50"

# Pipeline 전체 설정
ENHANCEMENT_PIPELINE_ENABLED = True

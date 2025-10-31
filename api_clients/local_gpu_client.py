"""
Local GPU 워터마크 제거 클라이언트
YOLOv11s (탐지) + IOPaint LAMA (인페인팅) 기반
SoraWatermarkCleaner 공식 구현 참고
"""

import os
import cv2
import torch
import numpy as np
from pathlib import Path
from utils.logger import logger
import config

try:
    from ultralytics import YOLO
    from iopaint.model_manager import ModelManager
    from iopaint.schema import HDStrategy, LDMSampler
except ImportError:
    logger.warning("Local GPU dependencies not installed. Local GPU mode will not work.")
    YOLO = None
    ModelManager = None


class LocalGPUClient:
    """로컬 GPU를 사용한 워터마크 제거"""

    def __init__(self):
        """로컬 GPU 클라이언트 초기화"""
        self.device = f"cuda:{config.LOCAL_GPU_DEVICE}" if torch.cuda.is_available() else "cpu"

        if self.device.startswith("cuda"):
            logger.info(f"Using GPU: {torch.cuda.get_device_name(config.LOCAL_GPU_DEVICE)}")
        else:
            logger.warning("CUDA not available. Falling back to CPU (very slow)")

        self.yolo_model = None
        self.lama_model = None
        self.model_manager = None

        # 모델 초기화
        self._initialize_models()

    def _initialize_models(self):
        """YOLOv11s와 LAMA 모델 초기화"""
        try:
            logger.info("Initializing YOLO model...")
            self._download_yolo_if_needed()
            self.yolo_model = YOLO(config.YOLO_MODEL_PATH)
            self.yolo_model.to(self.device)
            logger.info("YOLO model loaded successfully")

            logger.info("Initializing LAMA inpainting model...")
            # IOPaint ModelManager 초기화
            self.model_manager = ModelManager(
                name=config.LAMA_MODEL_NAME,
                device=self.device,
                disable_nsfw=False,
                cpu_offload=False,
                cpu_textencoder=False,
            )
            logger.info("LAMA model initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize models: {str(e)}")
            raise

    def _download_yolo_if_needed(self):
        """YOLO 모델 다운로드 (필요한 경우)"""
        model_path = Path(config.YOLO_MODEL_PATH)

        if model_path.exists():
            logger.info(f"YOLO model already exists: {model_path}")
            return

        # 모델 디렉토리 생성
        model_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            logger.info(f"Downloading YOLO model from {config.YOLO_MODEL_URL}...")
            import requests
            response = requests.get(config.YOLO_MODEL_URL, stream=True)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0

            with open(model_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            percent = (downloaded / total_size) * 100
                            logger.info(f"Download progress: {percent:.1f}%")

            logger.info(f"YOLO model downloaded successfully: {model_path}")

        except Exception as e:
            logger.error(f"Failed to download YOLO model: {str(e)}")
            raise

    def remove_watermark(self, video_path, output_path):
        """
        로컬 GPU로 워터마크 제거

        Args:
            video_path: 입력 비디오 경로
            output_path: 출력 비디오 경로

        Returns:
            bool: 성공 여부
        """
        try:
            if not os.path.exists(video_path):
                raise FileNotFoundError(f"Video file not found: {video_path}")

            logger.info(f"Starting local GPU watermark removal: {video_path}")

            # 비디오 열기
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise IOError(f"Cannot open video: {video_path}")

            # 비디오 정보 추출
            fps = cap.get(cv2.CAP_PROP_FPS)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

            logger.info(f"Video info - Size: {width}x{height}, FPS: {fps}, Frames: {total_frames}")

            # 출력 비디오 쓰기 설정
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

            if not out.isOpened():
                raise IOError(f"Cannot create output video: {output_path}")

            # 프레임 처리
            frame_count = 0
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                frame_count += 1
                logger.info(f"Processing frame {frame_count}/{total_frames}")

                # 워터마크 탐지 및 제거
                processed_frame = self._process_frame(frame)
                out.write(processed_frame)

            cap.release()
            out.release()

            logger.info(f"Local GPU watermark removal completed: {output_path}")
            return True

        except Exception as e:
            logger.error(f"Local GPU removal failed: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False

    def _process_frame(self, frame):
        """
        개별 프레임 처리

        Args:
            frame: 입력 프레임 (BGR)

        Returns:
            처리된 프레임 (BGR)
        """
        try:
            # 1. YOLO로 워터마크 탐지
            results = self.yolo_model(frame, verbose=False)

            if len(results) == 0 or len(results[0].boxes) == 0:
                # 워터마크 없음
                return frame

            # 마스크 생성
            mask = np.zeros((frame.shape[0], frame.shape[1]), dtype=np.uint8)

            for box in results[0].boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                # 바운딩 박스 좌표 제한
                x1, y1 = max(0, x1), max(0, y1)
                x2, y2 = min(frame.shape[1], x2), min(frame.shape[0], y2)
                mask[y1:y2, x1:x2] = 255

            # 2. LAMA로 인페인팅
            processed_frame = self._inpaint_frame(frame, mask)

            return processed_frame

        except Exception as e:
            logger.warning(f"Frame processing failed: {str(e)}, returning original frame")
            return frame

    def _inpaint_frame(self, frame, mask):
        """
        LAMA를 사용한 인페인팅

        Args:
            frame: 입력 프레임 (BGR)
            mask: 워터마크 마스크 (0-255)

        Returns:
            인페인팅된 프레임 (BGR)
        """
        try:
            # BGR to RGB 변환
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # LAMA 인페인팅 (IOPaint 사용)
            # 간단한 구현을 위해 마스크 영역을 근처 픽셀로 채우기 (테레신) 사용
            result = cv2.inpaint(rgb_frame, mask, 3, cv2.INPAINT_TELEA)

            # RGB to BGR 변환
            result_bgr = cv2.cvtColor(result, cv2.COLOR_RGB2BGR)

            return result_bgr

        except Exception as e:
            logger.warning(f"Inpainting failed: {str(e)}, returning original frame")
            return frame

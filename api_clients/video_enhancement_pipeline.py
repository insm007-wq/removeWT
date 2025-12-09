"""
비디오 업스케일링 파이프라인 - 2-Stage (ESRGAN + CodeFormer)
Stage 1: Real-ESRGAN (4x 업스케일)
Stage 2: CodeFormer (얼굴 복원)
"""

# Monkey patch for basicsr compatibility MUST be first
import sys
try:
    import torchvision.transforms.functional_tensor as functional_tensor
except (ModuleNotFoundError, ImportError):
    # Create missing module before any other imports
    import types
    import torchvision.transforms.functional as F
    functional_tensor = types.ModuleType('functional_tensor')

    def rgb_to_grayscale(img, num_output_channels=1):
        """Convert RGB to grayscale"""
        if img.ndim < 3 or img.shape[-3] != 3:
            raise ValueError(f'Input size should be (*, 3, H, W). Got {img.shape}')
        r, g, b = img.unbind(dim=-3)
        l_img = (0.2989 * r + 0.587 * g + 0.114 * b).unsqueeze(dim=-3)
        l_img = l_img.expand(img.shape[:-3] + (num_output_channels,) + img.shape[-2:])
        return l_img

    functional_tensor.rgb_to_grayscale = rgb_to_grayscale
    sys.modules['torchvision.transforms.functional_tensor'] = functional_tensor

# Now safe to import other modules
import os
import cv2
import torch
import numpy as np
import tempfile
from pathlib import Path
from PIL import Image

from utils.logger import logger
from utils.video_utils import extract_audio, merge_audio
import config

try:
    from realesrgan import RealESRGANer
    from basicsr.archs.rrdbnet_arch import RRDBNet
    HAS_ESRGAN = True
except ImportError:
    HAS_ESRGAN = False
    logger.warning("Real-ESRGAN not installed")


class VideoEnhancementPipeline:
    """Real-ESRGAN 비디오 업스케일링 (4x 해상도 증가)"""

    def __init__(self, stop_event=None, progress_callback=None):
        """
        VideoEnhancementPipeline 초기화

        Args:
            stop_event: threading.Event 객체로 처리 중단을 신호하는 데 사용
            progress_callback: 진행률 업데이트 콜백 함수 (message, progress) -> None
        """
        # PyTorch 성능 최적화 설정
        torch.set_num_threads(config.TORCH_NUM_THREADS)
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        # 디바이스 결정 (CUDA/ROCm/CPU)
        self.device = self._select_device()
        self.stop_event = stop_event
        self.progress_callback = progress_callback

        # ESRGAN 모델 초기화
        self.esrgan_upsampler = None

        logger.info(f"Using device for enhancement: {self.device}")
        self._initialize_models()

    def _select_device(self) -> str:
        """
        최적의 디바이스 선택 (CUDA > ROCm > CPU)
        """
        if config.GPU_TYPE == "cuda":
            if torch.cuda.is_available():
                return f"cuda:{config.LOCAL_GPU_DEVICE}"
            else:
                logger.warning("CUDA requested but not available, falling back to CPU")
                return "cpu"
        elif config.GPU_TYPE == "rocm":
            if torch.cuda.is_available():
                return f"cuda:{config.LOCAL_GPU_DEVICE}"
            else:
                logger.warning("ROCm requested but not available, falling back to CPU")
                return "cpu"
        else:  # "auto"
            if torch.cuda.is_available():
                try:
                    if "HIP" in torch.version.cuda:
                        logger.info("Auto-detected AMD ROCm GPU")
                        return f"cuda:{config.LOCAL_GPU_DEVICE}"
                except Exception:
                    pass
                logger.info("Auto-detected NVIDIA CUDA GPU")
                return f"cuda:{config.LOCAL_GPU_DEVICE}"
            else:
                logger.info("No GPU detected, using CPU")
                return "cpu"

    def _initialize_models(self):
        """ESRGAN 모델만 초기화"""
        try:
            self._init_esrgan()
            logger.info("Real-ESRGAN model initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Real-ESRGAN: {e}")
            self.esrgan_upsampler = None

    def _init_esrgan(self):
        """Real-ESRGAN 모델 초기화"""
        if not HAS_ESRGAN:
            raise ImportError("Real-ESRGAN not installed")

        logger.info("Initializing Real-ESRGAN model...")

        # 모델 디렉토리 생성
        os.makedirs(config.MODELS_DIR, exist_ok=True)

        # 모델 파일 경로 체크
        model_path = config.ESRGAN_MODEL_PATH
        if not os.path.exists(model_path):
            logger.warning(f"ESRGAN model not found at {model_path}")
            logger.info(f"Downloading ESRGAN model from {config.ESRGAN_MODEL_URL}...")
            self._download_esrgan_model(config.ESRGAN_MODEL_URL, model_path)

        try:
            # RealESRGANer 초기화
            self.esrgan_upsampler = RealESRGANer(
                scale=config.ESRGAN_SCALE,
                model_path=model_path
            )
            logger.info("Real-ESRGAN model loaded successfully")
        except Exception as e:
            logger.error(f"RealESRGANer failed: {e}")
            raise

    def _download_esrgan_model(self, url, save_path):
        """ESRGAN 모델 다운로드"""
        import urllib.request
        import shutil

        try:
            logger.info(f"Downloading from: {url}")
            # 임시 파일로 다운로드
            temp_path = save_path + ".tmp"

            def download_progress(block_num, block_size, total_size):
                downloaded = block_num * block_size
                percent = min(downloaded * 100 // total_size, 100)
                if percent % 10 == 0:
                    logger.info(f"Download progress: {percent}%")

            urllib.request.urlretrieve(url, temp_path, download_progress)

            # 다운로드 완료 후 최종 위치로 이동
            shutil.move(temp_path, save_path)
            logger.info(f"✓ ESRGAN model downloaded successfully to {save_path}")

        except Exception as e:
            logger.error(f"Failed to download ESRGAN model: {e}")
            raise

    def enhance_video(self, video_path, output_path):
        """
        메인 진입점: ESRGAN 업스케일링만 실행 (4x 해상도 증가)

        Args:
            video_path: 입력 비디오 경로
            output_path: 출력 비디오 경로

        Returns:
            bool: 성공 여부
        """
        try:
            if not os.path.exists(video_path):
                raise FileNotFoundError(f"Video file not found: {video_path}")

            logger.info(f"Starting ESRGAN Video Enhancement...")
            logger.info(f"Input: {video_path}")

            with tempfile.TemporaryDirectory() as temp_dir:
                # 오디오 추출
                audio_path = os.path.join(temp_dir, 'audio.aac')
                logger.info("Extracting audio from original video...")
                extract_audio(video_path, audio_path)

                # ESRGAN: 1080p → 4K 업스케일
                esrgan_out = os.path.join(temp_dir, 'esrgan_4k.mp4')
                logger.info("Starting Real-ESRGAN 4x upscaling...")
                if not self._run_esrgan(video_path, esrgan_out):
                    return False

                # 오디오 병합
                logger.info("Merging upscaled video with audio...")
                if os.path.exists(audio_path) and os.path.getsize(audio_path) > 0:
                    merge_audio(esrgan_out, audio_path, output_path)
                else:
                    logger.warning("No audio found, saving video without audio")
                    import shutil
                    shutil.copy2(esrgan_out, output_path)

                logger.info(f"✓ Video enhancement completed successfully!")
                logger.info(f"Output: {output_path}")
                return True

        except Exception as e:
            logger.error(f"Video enhancement failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False

    def _run_esrgan(self, input_path, output_path):
        """
        Stage 1: 1080p → 4K 업스케일
        """
        try:
            cap = cv2.VideoCapture(input_path)
            if not cap.isOpened():
                raise IOError(f"Cannot open video: {input_path}")

            fps = cap.get(cv2.CAP_PROP_FPS)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

            # 출력: 4배 크기
            out_width, out_height = width * 4, height * 4
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, fps, (out_width, out_height))

            if not out.isOpened():
                raise IOError(f"Cannot create output video: {output_path}")

            logger.info(f"ESRGAN: {width}x{height} → {out_width}x{out_height}, FPS: {fps}, Frames: {total_frames}")

            frame_count = 0
            while True:
                if self.stop_event and self.stop_event.is_set():
                    logger.warning(f"Stage 1 stopped by user at frame {frame_count}/{total_frames}")
                    cap.release()
                    out.release()
                    return False

                ret, frame = cap.read()
                if not ret:
                    break

                frame_count += 1

                # 업스케일 (ESRGAN 또는 OpenCV fallback)
                try:
                    if self.esrgan_upsampler == "opencv":
                        # OpenCV 업스케일
                        upscaled = cv2.resize(frame, (out_width, out_height), interpolation=cv2.INTER_CUBIC)
                    else:
                        # Real-ESRGAN 업스케일
                        upscaled, _ = self.esrgan_upsampler.enhance(frame, outscale=config.ESRGAN_SCALE)
                except Exception as e:
                    logger.warning(f"Upscale failed on frame {frame_count}: {e}, using OpenCV resize")
                    upscaled = cv2.resize(frame, (out_width, out_height), interpolation=cv2.INTER_CUBIC)

                out.write(upscaled)

                # 진행률 업데이트 (매 프레임마다)
                progress = (frame_count / total_frames) * 100
                if self.progress_callback:
                    self.progress_callback(
                        f"[ESRGAN Upscaling] {frame_count}/{total_frames} frames",
                        progress
                    )

            cap.release()
            out.release()

            if self.progress_callback:
                self.progress_callback(
                    f"[ESRGAN Upscaling] Complete",
                    100.0
                )

            logger.info(f"Stage 1 (ESRGAN) completed")
            return True

        except Exception as e:
            logger.error(f"ESRGAN processing failed: {e}")
            return False

    def _run_codeformer(self, input_path, output_path):
        """
        Stage 2: 얼굴 복원 (프레임별 처리)
        CodeFormer은 이미지 파일 경로를 받으므로 임시 파일로 처리
        """
        try:
            cap = cv2.VideoCapture(input_path)
            if not cap.isOpened():
                raise IOError(f"Cannot open video: {input_path}")

            fps = cap.get(cv2.CAP_PROP_FPS)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

            if not out.isOpened():
                raise IOError(f"Cannot create output video: {output_path}")

            logger.info(f"CodeFormer: {width}x{height}, FPS: {fps}, Frames: {total_frames}")

            import tempfile
            temp_dir = tempfile.mkdtemp()

            frame_count = 0
            while True:
                if self.stop_event and self.stop_event.is_set():
                    logger.warning(f"Stage 2 stopped by user at frame {frame_count}/{total_frames}")
                    cap.release()
                    out.release()
                    return False

                ret, frame = cap.read()
                if not ret:
                    break

                frame_count += 1

                # 프레임을 임시 파일로 저장
                temp_frame_path = os.path.join(temp_dir, f"frame_{frame_count}.jpg")
                cv2.imwrite(temp_frame_path, frame)

                # CodeFormer 얼굴 복원 (파일 경로 사용)
                restored_path = self._restore_faces_file(temp_frame_path)

                if restored_path and os.path.exists(restored_path):
                    restored_frame = cv2.imread(restored_path)
                    out.write(restored_frame)
                    os.remove(restored_path)
                else:
                    # 복원 실패 시 원본 사용
                    out.write(frame)

                # 임시 파일 삭제
                if os.path.exists(temp_frame_path):
                    os.remove(temp_frame_path)

                # 진행률 업데이트 (매 프레임마다)
                progress = 50.0 + (frame_count / total_frames) * 50
                if self.progress_callback:
                    self.progress_callback(
                        f"[Stage 2/2 - Face Restoration] {frame_count}/{total_frames} frames",
                        progress
                    )

            cap.release()
            out.release()

            # 임시 디렉토리 정리
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)

            if self.progress_callback:
                self.progress_callback(
                    f"[Stage 2/2 - Face Restoration] Complete",
                    100.0
                )

            logger.info(f"Stage 2 (CodeFormer) completed")
            return True

        except Exception as e:
            logger.error(f"CodeFormer processing failed: {e}")
            return False

    def _restore_faces(self, frame):
        """CodeFormer로 얼굴 복원"""
        try:
            # BGR → RGB 변환
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # CodeFormer inference_app 호출 (NumPy array 사용)
            # inference_app(image, background_enhance, face_upsample, upscale, codeformer_fidelity)
            restored = self.codeformer_restorer(
                rgb_frame,                              # image (NumPy array)
                False,                                  # background_enhance
                False,                                  # face_upsample
                1,                                      # upscale (이미 4배 업스케일됨)
                config.CODEFORMER_FIDELITY             # fidelity (0.5)
            )

            # RGB → BGR로 변환하여 반환
            return cv2.cvtColor(np.array(restored, dtype=np.uint8), cv2.COLOR_RGB2BGR)

        except Exception as e:
            logger.warning(f"Face restoration failed: {e}")
            return frame  # Fallback: 원본 반환

    def _restore_faces_file(self, image_path):
        """CodeFormer로 얼굴 복원 (파일 경로 사용)

        Args:
            image_path: 입력 이미지 파일 경로

        Returns:
            str: 복원된 이미지 파일 경로 (실패 시 None)
        """
        try:
            if not os.path.exists(image_path):
                logger.warning(f"Image file not found: {image_path}")
                return None

            # CodeFormer inference_app 호출 (파일 경로 사용)
            # inference_app(image, background_enhance, face_upsample, upscale, codeformer_fidelity)
            restored_path = self.codeformer_restorer(
                image_path,                             # image (파일 경로)
                False,                                  # background_enhance
                False,                                  # face_upsample
                1,                                      # upscale (이미 4배 업스케일됨)
                config.CODEFORMER_FIDELITY             # fidelity (0.5)
            )

            return restored_path

        except Exception as e:
            logger.warning(f"Face restoration failed for {image_path}: {e}")
            return None

"""
메인 워터마크 제거 파이프라인
API 우선 + 로컬 백업 하이브리드 방식
최적화 버전: VideoInfo 캐싱, ProPainter 재사용, 향상된 에러 처리
"""

import os
from pathlib import Path
from utils.logger import logger
from utils.video_utils import verify_video
from api_clients.replicate_client import ReplicateClient
import config


# 사용자 정의 예외
class ProcessingError(Exception):
    """처리 중 발생한 에러"""
    pass


class APIError(Exception):
    """API 관련 에러"""
    pass


class ValidationError(Exception):
    """검증 실패 에러"""
    pass


class WatermarkRemover:
    """동적 워터마크 제거 시스템 - 최적화 버전"""

    def __init__(self):
        """
        WatermarkRemover 초기화 (Replicate API 사용)
        """
        self.replicate_client = None

        # 디렉토리 생성
        self._ensure_directories()

        # Replicate API 클라이언트 초기화
        self._initialize_replicate_client()

        logger.info("WatermarkRemover initialized")

    def _ensure_directories(self):
        """필요한 디렉토리 생성"""
        for directory in [config.OUTPUT_DIR, config.TEMP_DIR, config.LOG_DIR]:
            try:
                os.makedirs(directory, exist_ok=True)
            except Exception as e:
                logger.warning(f"Failed to create directory {directory}: {str(e)}")

    def _initialize_replicate_client(self):
        """Replicate API 클라이언트 초기화"""
        api_token = config.REPLICATE_API_TOKEN

        if not api_token:
            logger.error("REPLICATE_API_TOKEN not set in .env")
            return

        try:
            self.replicate_client = ReplicateClient(api_token)
            logger.info("Replicate client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Replicate client: {str(e)}")
            self.replicate_client = None


    def validate_video(self, video_path):
        """
        비디오 유효성 검사 (파일 존재 및 포맷만 확인)
        """
        try:
            # 파일 존재 여부 및 형식 확인
            valid, message = verify_video(video_path)
            if not valid:
                raise ValidationError(f"Invalid video: {message}")

            logger.info(f"Video validated: {video_path}")
            return True

        except ValidationError as e:
            logger.error(f"Validation error: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected validation error: {str(e)}")
            return False

    def remove_with_replicate(self, video_path, output_path):
        """
        Replicate API를 이용한 워터마크 제거

        Args:
            video_path: 입력 비디오 경로
            output_path: 출력 비디오 경로

        Returns:
            bool: 성공 여부
        """
        if not self.replicate_client:
            logger.error("Replicate client not available")
            return False

        try:
            logger.info(f"Attempting Replicate watermark removal...")
            success = self.replicate_client.remove_watermark(video_path, output_path)

            if success:
                logger.info(f"Replicate watermark removal successful!")
                return True

            return False

        except Exception as e:
            logger.error(f"Replicate removal failed: {str(e)}")
            return False


    def _get_output_path(self, video_path, output_path=None):
        """
        출력 경로 생성 (pathlib 사용으로 최적화)
        """
        if output_path is None:
            output_path = Path(config.OUTPUT_DIR) / f"{Path(video_path).stem}_cleaned.mp4"
        else:
            output_path = Path(output_path)

        # 출력 디렉토리 생성
        output_path.parent.mkdir(parents=True, exist_ok=True)
        return str(output_path)

    def _log_results(self, success, output_path):
        """
        최적화: 중복 로직 제거, 불필요한 파일 체크 제거
        """
        if success:
            logger.info(f"\n{'='*60}")
            logger.info(f"✓ WATERMARK REMOVAL COMPLETED SUCCESSFULLY")
            logger.info(f"{'='*60}")

            try:
                file_size = Path(output_path).stat().st_size / (1024 * 1024)
                logger.info(f"Output file size: {file_size:.2f} MB")
            except Exception as e:
                logger.warning(f"Could not get output file size: {str(e)}")
        else:
            logger.error(f"\n{'='*60}")
            logger.error(f"✗ WATERMARK REMOVAL FAILED")
            logger.error(f"{'='*60}")

    def remove_watermark(self, video_path, output_path=None, force_method=None):
        """
        메인 워터마크 제거 함수 (Replicate API 사용)

        Args:
            video_path: 입력 비디오 경로
            output_path: 출력 비디오 경로 (생략하면 자동 생성)
            force_method: 처리 방법 (현재 "replicate" 만 지원, None으로도 작동)

        Returns:
            bool: 성공 여부
        """
        try:
            # 입력 검증
            video_path = str(Path(video_path).resolve())
            if not os.path.exists(video_path):
                raise ValidationError(f"Video file not found: {video_path}")

            # 출력 경로 생성 (최적화: 중복 제거)
            output_path = self._get_output_path(video_path, output_path)

            logger.info(f"\n{'='*60}")
            logger.info(f"WATERMARK REMOVAL STARTED")
            logger.info(f"{'='*60}")
            logger.info(f"Input: {video_path}")
            logger.info(f"Output: {output_path}")

            # 비디오 검증
            if not self.validate_video(video_path):
                self._log_results(False, output_path)
                return False

            # Replicate API로 처리
            logger.info("\nStarting watermark removal with Replicate API...")
            success = self.remove_with_replicate(video_path, output_path)

            self._log_results(success, output_path)
            return success

        except ValidationError as e:
            logger.error(f"Validation error: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            return False

    def batch_process(self, video_dir, output_dir=None, method=None):
        """
        배치 처리 (디렉토리의 모든 비디오 처리)

        Args:
            video_dir: 비디오 디렉토리
            output_dir: 출력 디렉토리 (생략하면 자동 생성)
            method: 처리 방법

        Returns:
            dict: 처리 결과
        """
        try:
            video_dir = Path(video_dir)
            if not video_dir.is_dir():
                raise ValidationError(f"Directory not found: {video_dir}")

            # 비디오 파일 찾기 (최적화: pathlib 사용)
            video_files = [
                f for f in video_dir.iterdir()
                if f.is_file() and f.suffix.lower() in {f'.{ext}' for ext in config.SUPPORTED_FORMATS}
            ]

            if not video_files:
                logger.warning(f"No video files found in {video_dir}")
                return None

            if output_dir is None:
                output_dir = Path(config.OUTPUT_DIR)
            else:
                output_dir = Path(output_dir)

            output_dir.mkdir(parents=True, exist_ok=True)

            results = {
                'total': len(video_files),
                'success': 0,
                'failed': 0,
                'files': {}
            }

            logger.info(f"Batch processing {len(video_files)} videos...")

            for i, video_file in enumerate(video_files, 1):
                video_path = str(video_file)
                output_path = str(output_dir / f"{video_file.stem}_cleaned.mp4")

                logger.info(f"\n[{i}/{len(video_files)}] Processing: {video_file.name}")

                success = self.remove_watermark(video_path, output_path, force_method=method)

                results['files'][video_file.name] = {
                    'success': success,
                    'input': video_path,
                    'output': output_path
                }

                if success:
                    results['success'] += 1
                else:
                    results['failed'] += 1

            logger.info(f"\n{'='*60}")
            logger.info(f"BATCH PROCESSING COMPLETED")
            logger.info(f"Total: {results['total']}, Success: {results['success']}, Failed: {results['failed']}")
            logger.info(f"Success rate: {(results['success']/results['total']*100):.1f}%")
            logger.info(f"{'='*60}")

            return results

        except ValidationError as e:
            logger.error(f"Batch processing error: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected batch processing error: {str(e)}", exc_info=True)
            return None

    def __del__(self):
        """소멸자"""
        pass

"""
Replicate API 클라이언트
Sora 2 Watermark Remover 사용
직접 파일 업로드 방식 (Replicate SDK가 자동으로 처리)
"""

import os
from pathlib import Path
from utils.logger import logger


class ReplicateClient:
    """Replicate API를 통한 워터마크 제거"""

    def __init__(self, api_token, stop_event=None, progress_callback=None):
        """
        Replicate 클라이언트 초기화

        Args:
            api_token: Replicate API token
            stop_event: threading.Event 객체로 처리 중단을 신호하는 데 사용
            progress_callback: 진행률 업데이트 콜백 함수 (message, progress) -> None
        """
        self.api_token = api_token
        self.stop_event = stop_event
        self.progress_callback = progress_callback

        if not api_token:
            raise ValueError("Replicate API token is required")

        # Replicate 클라이언트는 첫 사용 시에 초기화 (lazy loading)
        self._client = None

        logger.info("Replicate client initialized")

    @property
    def client(self):
        """Lazy load Replicate client on first access"""
        if self._client is None:
            try:
                import replicate
                self._client = replicate.Client(api_token=self.api_token)
            except Exception as e:
                logger.error(f"Failed to initialize Replicate client: {str(e)}")
                raise
        return self._client

    def remove_watermark(self, video_path, output_path):
        """
        Replicate를 이용한 워터마크 제거

        Args:
            video_path: 입력 비디오 경로
            output_path: 출력 비디오 경로

        Returns:
            bool: 성공 여부
        """
        try:
            # 중지 요청 확인
            if self.stop_event and self.stop_event.is_set():
                logger.warning("Replicate processing stopped by user before starting")
                return False

            logger.info(f"Removing watermark with Replicate: {video_path}")

            if not os.path.exists(video_path):
                raise FileNotFoundError(f"Video file not found: {video_path}")

            file_size = os.path.getsize(video_path) / (1024 * 1024)
            logger.info(f"Video size: {file_size:.2f}MB")

            # 파일 크기 제한 확인 (100MB)
            if file_size > 100:
                logger.error(f"File size {file_size:.2f}MB exceeds 100MB limit")
                return False

            # 최신 버전 ID
            version_id = "7b636d39f482f129dfa3429fdc7c5c2d4f4ef36e4cbc6d919b701c1d39162797"

            logger.info("Processing video with Replicate API...")
            logger.info("Uploading and processing... (this may take a few minutes)")

            # 진행상황 콜백
            if self.progress_callback:
                self.progress_callback("Uploading to Replicate API (25%)...", 25)

            # 방법 1: 바이너리 파일 객체 사용 (Replicate SDK 자동 업로드)
            logger.info("Method 1: Direct file object upload...")
            try:
                with open(video_path, 'rb') as video_file:
                    if self.progress_callback:
                        self.progress_callback("Processing video with Replicate (50%)...", 50)

                    prediction = self.client.run(
                        f"uglyrobot/sora2-watermark-remover:{version_id}",
                        input={"video": video_file}
                    )
                logger.info("Method 1 succeeded: Processing completed")
                return self._handle_prediction(prediction, output_path)
            except Exception as e:
                logger.warning(f"Method 1 failed: {str(e)}")

            # 방법 2: Base64 인코딩 사용 (작은 파일용)
            if file_size <= 50:  # 50MB 이하만 시도
                logger.info("Method 2: Base64 encoded data...")
                try:
                    import base64
                    with open(video_path, 'rb') as f:
                        video_data = f.read()
                    base64_data = base64.b64encode(video_data).decode('utf-8')
                    data_uri = f"data:video/mp4;base64,{base64_data}"

                    prediction = self.client.run(
                        f"uglyrobot/sora2-watermark-remover:{version_id}",
                        input={"video": data_uri}
                    )
                    logger.info("Method 2 succeeded: Processing completed")
                    return self._handle_prediction(prediction, output_path)
                except Exception as e:
                    logger.warning(f"Method 2 failed: {str(e)}")

            # 모든 방법이 실패
            logger.error("All upload methods failed")
            return False

        except Exception as e:
            logger.error(f"Replicate removal failed: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False

    def _handle_prediction(self, prediction, output_path):
        """
        Replicate 예측 결과 처리

        Args:
            prediction: Replicate API 응답
            output_path: 저장 경로

        Returns:
            bool: 성공 여부
        """
        if prediction:
            if isinstance(prediction, list) and len(prediction) > 0:
                output_url = prediction[0]
            else:
                output_url = prediction

            logger.info(f"Output URL: {output_url}")
            return self._download_result(str(output_url), output_path)
        else:
            logger.error("No output from Replicate")
            return False

    def _download_result(self, output_url, output_path):
        """
        처리된 비디오 다운로드

        Args:
            output_url: 결과 URL
            output_path: 저장 경로

        Returns:
            bool: 성공 여부
        """
        try:
            import requests

            logger.info(f"Downloading result to {output_path}...")

            if self.progress_callback:
                self.progress_callback("Downloading result (75%)...", 75)

            response = requests.get(output_url, timeout=300, stream=True)

            if response.status_code != 200:
                logger.error(f"Download failed: {response.status_code}")
                return False

            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # 파일 크기 가져오기 (진행률 계산용)
            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0

            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)

                        # 다운로드 진행률 표시
                        if total_size > 0 and self.progress_callback:
                            download_progress = 75 + ((downloaded_size / total_size) * 25)
                            if downloaded_size % (8192 * 10) == 0:  # 80KB마다 한 번
                                self.progress_callback(f"Downloading... ({download_progress:.0f}%)", download_progress)

            if self.progress_callback:
                self.progress_callback("Download completed (100%)", 100)

            logger.info(f"Result saved: {output_path}")
            return True

        except Exception as e:
            logger.error(f"Download error: {str(e)}")
            return False

    def check_api_token(self):
        """API 토큰 유효성 검증"""
        try:
            # Replicate 모델 존재 여부로 확인
            self.client.models.get("uglyrobot/sora2-watermark-remover")
            logger.info("Replicate API token is valid")
            return True

        except Exception as e:
            logger.error(f"Token check failed: {str(e)}")
            return False

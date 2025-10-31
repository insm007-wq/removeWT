"""
비디오 처리 유틸리티 함수들 (Replicate API용 - 경량 버전)
"""

import os
from pathlib import Path
from utils.logger import logger

def verify_video(video_path):
    """비디오 파일 검증 (파일 존재 및 확장자만 확인)"""

    if not os.path.exists(video_path):
        return False, "File not found"

    # 지원하는 형식 확인
    supported_formats = ('.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.webm')
    if not video_path.lower().endswith(supported_formats):
        return False, f"Unsupported format. Supported: {', '.join(supported_formats)}"

    # 파일 크기 확인 (0바이트 파일 체크)
    file_size = os.path.getsize(video_path)
    if file_size == 0:
        return False, "Video file is empty"

    logger.info(f"Video verification passed: {video_path} ({file_size / (1024*1024):.2f} MB)")
    return True, "Valid"

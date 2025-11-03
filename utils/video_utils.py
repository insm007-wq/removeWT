"""
비디오 처리 유틸리티 함수들 (Replicate API용 - 경량 버전)
"""

import os
import subprocess
import tempfile
from pathlib import Path
from utils.logger import logger
from utils.security_utils import validate_file_path

def verify_video(video_path):
    """비디오 파일 검증 (파일 존재, 경로 보안, 확장자 확인)"""

    # 1. 경로 검증 (보안)
    is_valid, result = validate_file_path(video_path, must_exist=True)
    if not is_valid:
        logger.error(f"Invalid video path: {result}")
        return False, result

    video_path = result  # 정규화된 절대 경로 사용

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


def _find_ffmpeg():
    """ffmpeg 경로 찾기"""
    # 먼저 현재 디렉토리의 ffmpeg 폴더 확인
    local_ffmpeg = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'ffmpeg', 'ffmpeg.exe')
    if os.path.exists(local_ffmpeg):
        return local_ffmpeg

    # PATH에서 ffmpeg 찾기
    result = subprocess.run(['where', 'ffmpeg'], capture_output=True, text=True)
    if result.returncode == 0:
        return result.stdout.strip().split('\n')[0]

    # 일반적인 설치 위치 확인
    for path in [
        'C:\\ffmpeg\\bin\\ffmpeg.exe',
        'C:\\Program Files\\ffmpeg\\bin\\ffmpeg.exe',
        'C:\\Program Files (x86)\\ffmpeg\\bin\\ffmpeg.exe',
    ]:
        if os.path.exists(path):
            return path

    raise FileNotFoundError("ffmpeg not found. Please ensure ffmpeg is installed or available in 'ffmpeg' folder.")


def extract_audio(video_path, audio_path):
    """
    비디오에서 오디오 추출

    Args:
        video_path: 입력 비디오 경로
        audio_path: 출력 오디오 경로 (.aac)

    Returns:
        bool: 성공 여부
    """
    try:
        ffmpeg_exe = _find_ffmpeg()

        # ffmpeg 명령어: -q:a 9 는 낮은 품질(빠른 처리), -q:a 0 은 높은 품질
        cmd = [
            ffmpeg_exe,
            '-i', video_path,
            '-vn',  # 비디오 스트림 무시
            '-acodec', 'aac',
            '-q:a', '5',  # 오디오 품질
            '-y',  # 기존 파일 덮어쓰기
            audio_path
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore', timeout=300)

        if result.returncode != 0:
            logger.error(f"Audio extraction failed: {result.stderr}")
            return False

        logger.info(f"Audio extracted successfully: {audio_path}")
        return True

    except Exception as e:
        logger.error(f"Audio extraction error: {str(e)}")
        return False


def merge_audio(video_path, audio_path, output_path):
    """
    비디오와 오디오 병합

    Args:
        video_path: 입력 비디오 경로 (오디오 없음)
        audio_path: 입력 오디오 경로
        output_path: 출력 경로

    Returns:
        bool: 성공 여부
    """
    try:
        ffmpeg_exe = _find_ffmpeg()

        # 오디오 파일이 없거나 너무 짧으면 오디오 없이 저장
        if not os.path.exists(audio_path):
            logger.warning(f"Audio file not found: {audio_path}. Saving video without audio.")
            return _copy_video(video_path, output_path)

        # ffmpeg 명령어: 비디오는 유지하고 오디오만 교체
        cmd = [
            ffmpeg_exe,
            '-i', video_path,
            '-i', audio_path,
            '-c:v', 'copy',  # 비디오 코덱 복사 (재인코딩 안함)
            '-c:a', 'aac',  # 오디오 코덱 설정
            '-map', '0:v:0',  # 첫 번째 입력의 비디오
            '-map', '1:a:0',  # 두 번째 입력의 오디오
            '-shortest',  # 더 짧은 스트림에 맞추기
            '-y',  # 기존 파일 덮어쓰기
            output_path
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore', timeout=600)

        if result.returncode != 0:
            logger.error(f"Audio merge failed: {result.stderr}")
            return False

        logger.info(f"Audio merge completed: {output_path}")
        return True

    except Exception as e:
        logger.error(f"Audio merge error: {str(e)}")
        return False


def _copy_video(src_path, dst_path):
    """비디오 파일 복사 (오디오 필요 없을 때)"""
    try:
        import shutil
        shutil.copy2(src_path, dst_path)
        logger.info(f"Video copied: {dst_path}")
        return True
    except Exception as e:
        logger.error(f"Video copy error: {str(e)}")
        return False

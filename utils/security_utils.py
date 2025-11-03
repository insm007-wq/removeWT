"""
보안 유틸리티 함수들
경로 검증, 파일 권한 확인, 민감 정보 마스킹 등
"""

import os
from pathlib import Path
from utils.logger import logger


def validate_file_path(file_path, must_exist=True, allowed_extensions=None):
    """
    파일 경로 검증 (경로 트래버설 방지)

    Args:
        file_path: 검증할 파일 경로
        must_exist: 파일이 존재해야 하는지 여부
        allowed_extensions: 허용된 확장자 tuple (예: ('.mp4', '.avi'))

    Returns:
        tuple: (bool, str) - (유효 여부, 메시지)
    """
    try:
        # 상대 경로를 절대 경로로 변환
        file_path = Path(file_path).resolve()

        # ".." 패턴 검사 (이미 resolve()로 정규화되었으므로 이중 검사)
        if '..' in str(file_path):
            return False, "경로에 '..' 패턴이 포함되어 있습니다"

        # 파일 존재 여부 확인
        if must_exist and not file_path.exists():
            return False, f"파일을 찾을 수 없습니다: {file_path}"

        # 파일인지 확인 (디렉토리 아님)
        if file_path.exists() and not file_path.is_file():
            return False, f"이것은 파일이 아닙니다: {file_path}"

        # 확장자 검사
        if allowed_extensions and file_path.exists():
            if not file_path.suffix.lower() in [ext.lower() for ext in allowed_extensions]:
                return False, f"지원하지 않는 파일 형식입니다: {file_path.suffix}"

        # 파일 읽기 권한 확인
        if file_path.exists() and not os.access(file_path, os.R_OK):
            return False, f"파일을 읽을 권한이 없습니다: {file_path}"

        return True, str(file_path)

    except Exception as e:
        logger.error(f"경로 검증 중 오류: {e}", exc_info=True)
        return False, f"경로 검증 실패: {str(e)}"


def validate_directory_path(dir_path, must_exist=False, writable=False):
    """
    디렉토리 경로 검증 (경로 트래버설 방지)

    Args:
        dir_path: 검증할 디렉토리 경로
        must_exist: 디렉토리가 존재해야 하는지 여부
        writable: 쓰기 권한이 필요한지 여부

    Returns:
        tuple: (bool, str) - (유효 여부, 메시지 또는 경로)
    """
    try:
        # 상대 경로를 절대 경로로 변환
        dir_path = Path(dir_path).resolve()

        # ".." 패턴 검사
        if '..' in str(dir_path):
            return False, "경로에 '..' 패턴이 포함되어 있습니다"

        # 디렉토리 존재 여부 확인
        if must_exist and not dir_path.exists():
            return False, f"디렉토리를 찾을 수 없습니다: {dir_path}"

        # 디렉토리인지 확인
        if dir_path.exists() and not dir_path.is_dir():
            return False, f"이것은 디렉토리가 아닙니다: {dir_path}"

        # 쓰기 권한 확인
        if dir_path.exists() and writable:
            if not os.access(dir_path, os.W_OK):
                return False, f"디렉토리에 쓸 권한이 없습니다: {dir_path}"

        return True, str(dir_path)

    except Exception as e:
        logger.error(f"디렉토리 경로 검증 중 오류: {e}", exc_info=True)
        return False, f"디렉토리 경로 검증 실패: {str(e)}"


def mask_sensitive_string(sensitive_str, show_chars=4):
    """
    민감한 정보(토큰, 비밀번호) 마스킹

    Args:
        sensitive_str: 마스킹할 문자열
        show_chars: 마지막 표시할 문자 수

    Returns:
        str: 마스킹된 문자열 (예: "sk-****...****abc123")
    """
    if not sensitive_str or len(sensitive_str) == 0:
        return "***"

    if len(sensitive_str) <= show_chars:
        return "*" * len(sensitive_str)

    # 앞 부분 표시 + 마스킹 + 뒷 부분 표시
    prefix = sensitive_str[:2] if len(sensitive_str) >= 2 else ""
    suffix = sensitive_str[-show_chars:] if len(sensitive_str) > show_chars else ""
    masked_part = "*" * (len(sensitive_str) - len(prefix) - len(suffix))

    return f"{prefix}{masked_part}{suffix}"


def get_safe_filename(filename):
    """
    파일명에서 위험한 문자 제거

    Args:
        filename: 원본 파일명

    Returns:
        str: 안전한 파일명
    """
    # 위험한 문자 정의
    dangerous_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*', '\0']

    # 문자 제거
    safe_name = filename
    for char in dangerous_chars:
        safe_name = safe_name.replace(char, '_')

    # 연속된 언더스코어 제거
    while '__' in safe_name:
        safe_name = safe_name.replace('__', '_')

    return safe_name.strip('_')


def validate_api_token(token):
    """
    API 토큰 기본 검증

    Args:
        token: API 토큰 문자열

    Returns:
        tuple: (bool, str) - (유효 여부, 메시지 또는 마스킹된 토큰)
    """
    if not token:
        return False, "API 토큰이 설정되지 않았습니다"

    if len(token) < 10:
        return False, "API 토큰이 너무 짧습니다"

    # 민감 정보이므로 로그에는 마스킹된 버전만 반환
    masked_token = mask_sensitive_string(token, show_chars=4)
    return True, masked_token

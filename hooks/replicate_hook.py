"""
PyInstaller Runtime Hook for Replicate
This hook patches replicate to handle missing metadata in bundled executables
"""

import sys
from importlib import metadata

# Replicate 패키지의 버전 메타데이터 조회 실패를 처리
original_version = metadata.version

def patched_version(distribution_name):
    """버전 조회 실패 시 기본값 반환"""
    try:
        return original_version(distribution_name)
    except metadata.PackageNotFoundError:
        # 번들된 실행 파일에서 메타데이터를 찾을 수 없으면 기본 버전 반환
        if distribution_name.lower() == 'replicate':
            return '0.0.0'
        raise

# Monkey-patch the metadata.version function
metadata.version = patched_version

# replicate가 이미 로드되었으면 그것도 패치
if 'replicate' in sys.modules:
    try:
        replicate_module = sys.modules['replicate']
        if hasattr(replicate_module, '__version__'):
            # 버전 속성이 있으면 그냥 두기
            pass
    except Exception:
        pass

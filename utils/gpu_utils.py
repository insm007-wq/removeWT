"""
GPU 정보 유틸리티
NVIDIA GPU 정보 조회 및 모니터링
"""

import subprocess
from typing import Dict, Optional
from utils.logger import logger


class GPUInfo:
    """GPU 정보 조회 클래스"""

    def __init__(self):
        self.has_gpu = False
        self.gpu_name = "No GPU detected"
        self.use_pynvml = False
        self.use_torch = False
        self.try_pynvml()
        if not self.has_gpu:
            self.try_torch()

    def try_pynvml(self):
        """pynvml을 사용한 GPU 정보 조회 (권장)"""
        try:
            import pynvml
            pynvml.nvmlInit()
            self.has_gpu = True
            self.use_pynvml = True
            logger.info("GPU monitoring enabled via pynvml")
        except Exception as e:
            logger.debug(f"pynvml not available: {str(e)}")
            self.has_gpu = False

    def try_torch(self):
        """PyTorch를 사용한 GPU 정보 조회 (fallback)"""
        try:
            import torch
            if torch.cuda.is_available():
                self.has_gpu = True
                self.use_torch = True
                logger.info("GPU monitoring enabled via PyTorch")
            else:
                logger.info("No CUDA GPU detected")
                self.has_gpu = False
        except Exception as e:
            logger.debug(f"PyTorch GPU check failed: {str(e)}")
            self.has_gpu = False

    def get_gpu_info(self) -> Dict[str, str]:
        """
        GPU 정보 조회

        Returns:
            Dict: GPU 정보
                - name: GPU 이름
                - memory_used: 사용 중인 메모리 (GB)
                - memory_total: 전체 메모리 (GB)
                - utilization: GPU 사용률 (%)
                - status: 상태 메시지
        """
        if not self.has_gpu:
            return {
                "name": "GPU not detected",
                "memory_used": "-",
                "memory_total": "-",
                "utilization": "-",
                "status": "No GPU available"
            }

        # pynvml 방식 (더 자세한 정보)
        if self.use_pynvml:
            return self._get_gpu_info_pynvml()

        # PyTorch 방식 (fallback)
        if self.use_torch:
            return self._get_gpu_info_torch()

        return {
            "name": "GPU not detected",
            "memory_used": "-",
            "memory_total": "-",
            "utilization": "-",
            "status": "No GPU available"
        }

    def _get_gpu_info_pynvml(self) -> Dict[str, str]:
        """pynvml을 사용한 GPU 정보 조회"""
        try:
            import pynvml

            # GPU 0 (첫 번째 GPU) 정보 조회
            device_count = pynvml.nvmlDeviceGetCount()
            if device_count == 0:
                return {
                    "name": "No GPU available",
                    "memory_used": "-",
                    "memory_total": "-",
                    "utilization": "-",
                    "status": "No NVIDIA GPU detected"
                }

            handle = pynvml.nvmlDeviceGetHandleByIndex(0)

            # GPU 이름
            gpu_name = pynvml.nvmlDeviceGetName(handle)
            if isinstance(gpu_name, bytes):
                gpu_name = gpu_name.decode('utf-8')

            # 메모리 정보
            mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
            memory_used_mb = mem_info.used / (1024 * 1024)
            memory_total_mb = mem_info.total / (1024 * 1024)
            memory_used_gb = memory_used_mb / 1024
            memory_total_gb = memory_total_mb / 1024

            # GPU 사용률
            try:
                utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)
                gpu_utilization = utilization.gpu
            except pynvml.NVMLError:
                gpu_utilization = 0

            return {
                "name": gpu_name,
                "memory_used": f"{memory_used_gb:.1f}",
                "memory_total": f"{memory_total_gb:.1f}",
                "utilization": str(int(gpu_utilization)),
                "status": "OK"
            }

        except Exception as e:
            logger.warning(f"Error getting GPU info via pynvml: {str(e)}")
            return {
                "name": "Error reading GPU",
                "memory_used": "-",
                "memory_total": "-",
                "utilization": "-",
                "status": f"Error: {str(e)}"
            }

    def _get_gpu_info_torch(self) -> Dict[str, str]:
        """PyTorch를 사용한 GPU 정보 조회"""
        try:
            import torch

            if not torch.cuda.is_available():
                return {
                    "name": "CUDA not available",
                    "memory_used": "-",
                    "memory_total": "-",
                    "utilization": "-",
                    "status": "CUDA disabled"
                }

            # GPU 이름
            gpu_name = torch.cuda.get_device_name(0)

            # 메모리 정보
            memory_allocated = torch.cuda.memory_allocated(0) / (1024 ** 3)  # GB
            memory_reserved = torch.cuda.memory_reserved(0) / (1024 ** 3)  # GB

            return {
                "name": gpu_name,
                "memory_used": f"{memory_allocated:.1f}",
                "memory_total": f"{memory_reserved:.1f}",
                "utilization": "-",  # PyTorch로는 사용률을 가져올 수 없음
                "status": "OK (PyTorch)"
            }

        except Exception as e:
            logger.warning(f"Error getting GPU info via PyTorch: {str(e)}")
            return {
                "name": "Error reading GPU",
                "memory_used": "-",
                "memory_total": "-",
                "utilization": "-",
                "status": f"Error: {str(e)}"
            }

    def shutdown(self):
        """GPU 모니터링 종료"""
        try:
            import pynvml
            pynvml.nvmlShutdown()
        except Exception:
            pass


# 전역 GPU 정보 객체
_gpu_info = None


def get_gpu_info() -> Dict[str, str]:
    """
    GPU 정보 조회 (글로벌 함수)

    Returns:
        Dict: GPU 정보
    """
    global _gpu_info
    if _gpu_info is None:
        _gpu_info = GPUInfo()

    return _gpu_info.get_gpu_info()


def get_gpu_display_text() -> str:
    """
    GUI 표시용 GPU 정보 문자열 생성

    Returns:
        str: 포맷된 GPU 정보 문자열
    """
    info = get_gpu_info()

    if info["status"] != "OK":
        return f"🎮 {info['name']}"

    memory = f"{info['memory_used']}GB / {info['memory_total']}GB"
    utilization = f"{info['utilization']}%"

    return f"🎮 {info['name']}  |  사용률: {utilization}  |  메모리: {memory}"

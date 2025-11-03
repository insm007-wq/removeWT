"""
GPU 정보 유틸리티
NVIDIA GPU 정보 조회 및 모니터링
"""

import subprocess
import psutil
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
            device_count = pynvml.nvmlDeviceGetCount()
            if device_count > 0:
                self.has_gpu = True
                self.use_pynvml = True
                logger.info(f"GPU monitoring enabled via pynvml ({device_count} GPU(s) found)")
            else:
                logger.info("pynvml initialized but no GPUs found")
                self.has_gpu = False
        except Exception as e:
            logger.debug(f"pynvml not available: {str(e)}")
            self.has_gpu = False

    def try_torch(self):
        """PyTorch를 사용한 GPU 정보 조회 (fallback)"""
        try:
            import torch
            cuda_available = torch.cuda.is_available()
            device_count = torch.cuda.device_count() if cuda_available else 0

            if cuda_available and device_count > 0:
                self.has_gpu = True
                self.use_torch = True
                logger.info(f"GPU monitoring enabled via PyTorch ({device_count} GPU(s) found)")
            else:
                logger.info(f"PyTorch CUDA check - Available: {cuda_available}, Count: {device_count}")
                self.has_gpu = False
        except Exception as e:
            logger.warning(f"PyTorch GPU check failed: {str(e)}")
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


# 전역 GPU 정보 객체 (캐시)
_gpu_info = None
_last_detection_attempt = None


def get_gpu_info() -> Dict[str, str]:
    """
    GPU 정보 조회 (글로벌 함수)
    매번 GPU 감지를 재시도하여 동적 로드 지원

    Returns:
        Dict: GPU 정보
    """
    global _gpu_info

    # GPU 정보 객체가 없으면 생성, 있으면 재감지 시도
    if _gpu_info is None:
        _gpu_info = GPUInfo()
    else:
        # 이미 GPU 감지 시도했다면, 다시 시도해봄 (CUDA 동적 로드 지원)
        if not _gpu_info.has_gpu:
            _gpu_info = GPUInfo()

    return _gpu_info.get_gpu_info()


def get_gpu_display_text() -> str:
    """
    GUI 표시용 GPU 정보 문자열 생성
    GPU와 CPU 정보 함께 표시 (PyTorch 우선, pynvml 폴백)

    Returns:
        str: 포맷된 GPU/CPU 정보 문자열
    """
    try:
        gpu_text = ""

        # ===== PyTorch를 사용한 GPU 정보 조회 (우선 방식) =====
        try:
            import torch

            if torch.cuda.is_available():
                gpu_name = torch.cuda.get_device_name(0)
                memory_allocated = torch.cuda.memory_allocated(0) / (1024 ** 3)  # GB
                memory_reserved = torch.cuda.memory_reserved(0) / (1024 ** 3)    # GB

                # 실제 total 메모리 가져오기
                props = torch.cuda.get_device_properties(0)
                memory_total_gb = props.total_memory / (1024 ** 3)

                # GPU 메모리 사용률 계산 (할당된 메모리 기준)
                memory_usage_percent = (memory_allocated / memory_total_gb) * 100 if memory_total_gb > 0 else 0

                gpu_text = f"🎮 {gpu_name}  |  메모리: {memory_allocated:.1f}GB / {memory_total_gb:.1f}GB ({memory_usage_percent:.0f}%)"

                # GPU 사용률은 nvidia-smi로 가져오기 (보조)
                gpu_util_str = ""
                try:
                    result = subprocess.run(
                        ["nvidia-smi", "--query-gpu=utilization.gpu", "--format=csv,noheader,nounits"],
                        capture_output=True,
                        text=True,
                        timeout=1
                    )
                    if result.returncode == 0:
                        gpu_util = result.stdout.strip().split('\n')[0].strip()
                        if gpu_util and gpu_util.isdigit():
                            gpu_util_str = f"  |  GPU 활용: {gpu_util}%"
                except Exception as e:
                    logger.debug(f"nvidia-smi error: {str(e)}")

                # gpu_text += gpu_util_str  # GPU 활용률 표시 (숨김 - 나중에 필요시 활성화)
            else:
                gpu_text = "🎮 CUDA not available"

        except ImportError:
            logger.debug("PyTorch not available, trying pynvml...")
            # PyTorch 없으면 nvidia-smi로 시도
            try:
                result = subprocess.run(
                    ["nvidia-smi", "--query-gpu=name,memory.used,memory.total,utilization.gpu", "--format=csv,noheader,nounits"],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                if result.returncode == 0:
                    output = result.stdout.strip().split('\n')[0]
                    parts = [p.strip() for p in output.split(',')]
                    if len(parts) >= 4:
                        gpu_name = parts[0]
                        memory_used = float(parts[1]) / 1024  # MB to GB
                        memory_total = float(parts[2]) / 1024  # MB to GB
                        gpu_util = parts[3]
                        # GPU 활용률 표시 제거 (숨김 - 나중에 필요시 추가)
                        gpu_text = f"🎮 {gpu_name}  |  메모리: {memory_used:.1f}GB / {memory_total:.1f}GB"
                    else:
                        gpu_text = "🎮 GPU not detected"
                else:
                    gpu_text = "🎮 GPU not detected"
            except Exception as e:
                logger.debug(f"nvidia-smi error: {str(e)}")
                gpu_text = "🎮 GPU not detected"

        # ===== CPU 정보 추가 (비블로킹 샘플링) =====
        try:
            cpu_percent = psutil.cpu_percent(interval=None)  # Non-blocking (최근 값 사용)
            gpu_text += f"  |  CPU: {cpu_percent}%"
        except Exception as e:
            logger.debug(f"CPU info error: {str(e)}")

        return gpu_text

    except Exception as e:
        logger.warning(f"Failed to get display text: {str(e)}")
        return "🎮 System info unavailable"

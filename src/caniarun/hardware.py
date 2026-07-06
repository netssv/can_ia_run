"""
hardware.py  –  Public API for hardware detection.
Delegates OS-specific detection to hardware_detection.detectors and
bandwidth estimation to hardware_detection.bandwidth.
"""
import platform
import psutil
from dataclasses import dataclass
from typing import Optional

from .gpu_db import APPLE_DB, match_gpu
from .hardware_detection.detectors import (
    _detect_android,
    _detect_apple_silicon,
    _detect_nvidia_nvml,
    _detect_nvidia_smi,
    _detect_linux_lspci,
)
from .hardware_detection.bandwidth import estimate_bandwidth_heuristic


@dataclass
class HardwareInfo:
    gpu_name: Optional[str]
    gpu_vendor: Optional[str]
    vram_gb: Optional[float]
    total_usable_ram: Optional[float]
    system_ram_gb: Optional[float]
    memory_bandwidth: Optional[float]
    is_apple_silicon: bool
    platform: str


def _detect_system_ram() -> float:
    return round(psutil.virtual_memory().total / (1024 ** 3), 1)


def detect() -> HardwareInfo:
    plat = platform.system()
    system_ram = _detect_system_ram()

    # 0. Android (often reports itself as Linux)
    android_info = _detect_android()
    if android_info:
        return HardwareInfo(
            gpu_name=android_info["name"],
            gpu_vendor=android_info["vendor"],
            vram_gb=None,
            total_usable_ram=system_ram,
            system_ram_gb=system_ram,
            memory_bandwidth=android_info["bw"],
            is_apple_silicon=False,
            platform="Android"
        )

    # 1. Apple Silicon
    apple_info = _detect_apple_silicon()
    if apple_info:
        key = apple_info["chip_key"]
        spec = APPLE_DB.get(key)
        bw = spec.bw if spec else 100.0

        return HardwareInfo(
            gpu_name=apple_info["name"],
            gpu_vendor="Apple",
            vram_gb=None,
            total_usable_ram=apple_info["system_ram"],
            system_ram_gb=apple_info["system_ram"],
            memory_bandwidth=bw,
            is_apple_silicon=True,
            platform=plat
        )

    # 2. NVIDIA (NVML first, then nvidia-smi)
    gpu_info = _detect_nvidia_nvml()
    if not gpu_info:
        gpu_info = _detect_nvidia_smi()

    # 3. Linux generic fallback
    if not gpu_info and plat == "Linux":
        gpu_info = _detect_linux_lspci()

    # Build result from GPU info
    if gpu_info:
        name = gpu_info["name"]
        vendor = gpu_info["vendor"]
        vram_gb = gpu_info["vram_gb"]

        match = match_gpu(name)
        bw = None
        if match:
            matched_name, spec = match
            if not vram_gb:
                vram_gb = spec.vram
            bw = spec.bw

        if not bw:
            bw = estimate_bandwidth_heuristic(name, vram_gb, plat)

        total_usable_ram = vram_gb if vram_gb else system_ram

        return HardwareInfo(
            gpu_name=name,
            gpu_vendor=vendor,
            vram_gb=vram_gb,
            total_usable_ram=total_usable_ram,
            system_ram_gb=system_ram,
            memory_bandwidth=bw,
            is_apple_silicon=False,
            platform=plat
        )

    # 4. Total fallback — no GPU detected
    return HardwareInfo(
        gpu_name=None,
        gpu_vendor=None,
        vram_gb=None,
        total_usable_ram=system_ram,
        system_ram_gb=system_ram,
        memory_bandwidth=estimate_bandwidth_heuristic("", None, plat),
        is_apple_silicon=False,
        platform=plat
    )

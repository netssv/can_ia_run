"""
hardware_detection/bandwidth.py
Heuristic bandwidth estimator used as fallback when a GPU is not in GPU_DB.
"""
from typing import Optional


def estimate_bandwidth_heuristic(
    gpu_name: str,
    vram_gb: Optional[float],
    plat: str
) -> Optional[float]:
    """Return a rough memory-bandwidth estimate (GB/s) for unknown GPUs."""
    if not gpu_name:
        return 60.0 if plat in ("Windows", "Linux") else None

    upper = gpu_name.upper()
    is_nvidia = "NVIDIA" in upper or "GEFORCE" in upper or "RTX" in upper or "GTX" in upper
    is_amd = "AMD" in upper or "ATI" in upper or "RADEON" in upper
    is_intel = "INTEL" in upper

    if is_intel and ("UHD" in upper or "IRIS" in upper or "HD GRAPHICS" in upper):
        return 50.0

    if is_nvidia:
        if "RTX" in upper:
            if vram_gb and vram_gb >= 20: return 700.0
            if vram_gb and vram_gb >= 12: return 450.0
            if vram_gb and vram_gb >= 8:  return 300.0
            return 250.0
        if "GTX" in upper:
            if vram_gb and vram_gb >= 8: return 250.0
            if vram_gb and vram_gb >= 4: return 150.0
            return 112.0
        if vram_gb and vram_gb >= 8: return 300.0
        return 150.0

    if is_amd:
        if "RADEON GRAPHICS" in upper:
            return 55.0
        if vram_gb and vram_gb >= 16: return 500.0
        if vram_gb and vram_gb >= 8:  return 300.0
        if vram_gb and vram_gb >= 4:  return 180.0
        return 150.0

    return 60.0 if plat in ("Windows", "Linux") else None

import platform
import subprocess
import psutil
from dataclasses import dataclass
from typing import Optional

from .gpu_db import GPU_DB, APPLE_DB, GPUSpec, match_gpu

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

def _estimate_bandwidth_heuristic(gpu_name: str, vram_gb: Optional[float], plat: str) -> Optional[float]:
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
            if vram_gb and vram_gb >= 8: return 300.0
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
        if vram_gb and vram_gb >= 8: return 300.0
        if vram_gb and vram_gb >= 4: return 180.0
        return 150.0
        
    return 60.0 if plat in ("Windows", "Linux") else None

def _detect_nvidia_nvml() -> Optional[dict]:
    try:
        import pynvml
        pynvml.nvmlInit()
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        name = pynvml.nvmlDeviceGetName(handle)
        if isinstance(name, bytes):
            name = name.decode('utf-8')
        mem = pynvml.nvmlDeviceGetMemoryInfo(handle)
        vram_gb = mem.total / (1024 ** 3)
        return {"name": name, "vendor": "NVIDIA", "vram_gb": vram_gb}
    except Exception:
        return None

def _detect_nvidia_smi() -> Optional[dict]:
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, check=True
        )
        lines = result.stdout.strip().split('\n')
        if lines and lines[0]:
            parts = lines[0].split(',')
            name = parts[0].strip()
            vram_mb = float(parts[1].strip())
            return {"name": name, "vendor": "NVIDIA", "vram_gb": vram_mb / 1024.0}
    except Exception:
        pass
    return None

def _detect_apple_silicon() -> Optional[dict]:
    plat = platform.system()
    if plat != "Darwin":
        return None
    try:
        proc = platform.processor()
        if proc != "arm":
            return None
            
        result = subprocess.run(
            ["sysctl", "-n", "machdep.cpu.brand_string"],
            capture_output=True, text=True, check=True
        )
        brand = result.stdout.strip()
        
        # Apple M1 Pro -> m1 pro
        lower_brand = brand.lower().replace("apple ", "").strip()
        
        mem_result = subprocess.run(
            ["sysctl", "-n", "hw.memsize"],
            capture_output=True, text=True, check=True
        )
        system_ram = float(mem_result.stdout.strip()) / (1024 ** 3)
        
        # For Apple Silicon, we don't have dedicated VRAM, just unified memory.
        return {
            "name": brand,
            "vendor": "Apple",
            "vram_gb": None,
            "system_ram": system_ram,
            "chip_key": lower_brand
        }
    except Exception:
        return None

def _detect_linux_lspci() -> Optional[dict]:
    try:
        result = subprocess.run(["lspci"], capture_output=True, text=True, check=True)
        for line in result.stdout.split('\n'):
            if "VGA compatible controller" in line or "3D controller" in line:
                if "NVIDIA" in line.upper():
                    # Wait, if nvidia, smi should have caught it. But just in case:
                    return {"name": line.split(":")[-1].strip(), "vendor": "NVIDIA", "vram_gb": None}
                elif "AMD" in line.upper() or "ATI" in line.upper() or "RADEON" in line.upper():
                    return {"name": line.split(":")[-1].strip(), "vendor": "AMD", "vram_gb": None}
                elif "INTEL" in line.upper():
                    return {"name": line.split(":")[-1].strip(), "vendor": "Intel", "vram_gb": None}
    except Exception:
        pass
    return None

def detect() -> HardwareInfo:
    plat = platform.system()
    system_ram = _detect_system_ram()
    
    # 1. Try Apple Silicon
    apple_info = _detect_apple_silicon()
    if apple_info:
        key = apple_info["chip_key"]
        spec = APPLE_DB.get(key)
        
        bw = spec.bw if spec else 100.0 # fallback
        
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
        
    # 2. Try NVIDIA
    gpu_info = _detect_nvidia_nvml()
    if not gpu_info:
        gpu_info = _detect_nvidia_smi()
        
    # 3. Try Linux lspci as generic fallback
    if not gpu_info and plat == "Linux":
        gpu_info = _detect_linux_lspci()
        
    # Build result
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
            bw = _estimate_bandwidth_heuristic(name, vram_gb, plat)
            
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
        
    # 4. Total Fallback (No GPU detected)
    return HardwareInfo(
        gpu_name=None,
        gpu_vendor=None,
        vram_gb=None,
        total_usable_ram=system_ram,
        system_ram_gb=system_ram,
        memory_bandwidth=_estimate_bandwidth_heuristic("", None, plat),
        is_apple_silicon=False,
        platform=plat
    )

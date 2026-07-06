"""
hardware_detection/detectors.py
Platform-specific GPU detection functions.
Each returns a dict with keys: name, vendor, vram_gb (+ optional extras),
or None if detection fails.
"""
import platform
import subprocess
from typing import Optional


def _detect_nvidia_nvml() -> Optional[dict]:
    try:
        import pynvml
        pynvml.nvmlInit()
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        name = pynvml.nvmlDeviceGetName(handle)
        if isinstance(name, bytes):
            name = name.decode("utf-8")
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
        lines = result.stdout.strip().split("\n")
        if lines and lines[0]:
            parts = lines[0].split(",")
            name = parts[0].strip()
            vram_mb = float(parts[1].strip())
            return {"name": name, "vendor": "NVIDIA", "vram_gb": vram_mb / 1024.0}
    except Exception:
        pass
    return None


def _detect_apple_silicon() -> Optional[dict]:
    if platform.system() != "Darwin":
        return None
    try:
        if platform.processor() != "arm":
            return None
        result = subprocess.run(
            ["sysctl", "-n", "machdep.cpu.brand_string"],
            capture_output=True, text=True, check=True
        )
        brand = result.stdout.strip()
        lower_brand = brand.lower().replace("apple ", "").strip()

        mem_result = subprocess.run(
            ["sysctl", "-n", "hw.memsize"],
            capture_output=True, text=True, check=True
        )
        system_ram = float(mem_result.stdout.strip()) / (1024 ** 3)

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
        for line in result.stdout.split("\n"):
            if "VGA compatible controller" in line or "3D controller" in line:
                tail = line.split(":")[-1].strip()
                upper = line.upper()
                if "NVIDIA" in upper:
                    return {"name": tail, "vendor": "NVIDIA", "vram_gb": None}
                elif "AMD" in upper or "ATI" in upper or "RADEON" in upper:
                    return {"name": tail, "vendor": "AMD", "vram_gb": None}
                elif "INTEL" in upper:
                    return {"name": tail, "vendor": "Intel", "vram_gb": None}
    except Exception:
        pass
    return None


def _detect_android() -> Optional[dict]:
    import os
    is_android = (
        "ANDROID_ROOT" in os.environ
        or "ANDROID_DATA" in os.environ
        or os.path.exists("/system/build.prop")
    )
    if not is_android:
        return None

    gpu_name = "Android Mobile Device"
    bw = 30.0  # conservative LPDDR4x/5 bandwidth

    try:
        result = subprocess.run(["getprop", "ro.soc.model"], capture_output=True, text=True)
        if result.stdout.strip():
            gpu_name = result.stdout.strip()
        else:
            result = subprocess.run(["getprop", "ro.board.platform"], capture_output=True, text=True)
            if result.stdout.strip():
                gpu_name = result.stdout.strip()
    except Exception:
        pass

    return {"name": gpu_name, "vendor": "Mobile", "vram_gb": None, "bw": bw}

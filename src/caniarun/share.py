import base64
from caniarun.hardware import HardwareInfo

def generate_share_id(hw: HardwareInfo) -> str:
    """Generate a shareable ID representing the hardware performance profile."""
    vram = hw.vram_gb or 0.0
    ram = hw.system_ram_gb or 0.0
    bw = hw.memory_bandwidth or 0.0
    apple = 1 if hw.is_apple_silicon else 0
    
    # We strip out pipes from the name to avoid breaking the split, and truncate
    gpu = (hw.gpu_name or "Unknown").replace('|', ' ').strip()
    if len(gpu) > 30:
        gpu = gpu[:30].strip()
    
    plat = (hw.platform or "Unknown").replace('|', ' ').strip()
    if len(plat) > 15:
        plat = plat[:15].strip()

    # Format: vram|ram|bw|apple|gpu|platform
    raw = f"{vram:.1f}|{ram:.1f}|{bw:.1f}|{apple}|{gpu}|{plat}"
    
    # Base64 encode and remove padding for cleaner look
    b64 = base64.urlsafe_b64encode(raw.encode('utf-8')).decode('utf-8').rstrip('=')
    return f"HW2-{b64}"

def decode_share_id(share_id: str) -> HardwareInfo:
    """Decode a shareable ID back into a HardwareInfo profile."""
    is_v2 = False
    if share_id.startswith("HW2-"):
        share_id = share_id[4:]
        is_v2 = True
    elif share_id.startswith("HW-"):
        share_id = share_id[3:]
        
    # Re-add padding
    padding = len(share_id) % 4
    if padding:
        share_id += '=' * (4 - padding)

    try:
        raw = base64.urlsafe_b64decode(share_id).decode('utf-8')
        parts = raw.split('|')
        
        vram = float(parts[0])
        ram = float(parts[1])
        bw = float(parts[2])
        apple = bool(int(parts[3]))
        
        gpu_name = "Shared Hardware Profile"
        platform_name = "Shared Profile"
        
        if is_v2 and len(parts) >= 6:
            gpu_name = parts[4]
            platform_name = parts[5]

        return HardwareInfo(
            gpu_name=gpu_name,
            gpu_vendor="Unknown",
            vram_gb=vram if vram > 0 else None,
            total_usable_ram=ram if ram > 0 else None,
            system_ram_gb=ram if ram > 0 else None,
            memory_bandwidth=bw if bw > 0 else None,
            is_apple_silicon=apple,
            platform=platform_name
        )
    except Exception as e:
        raise ValueError(f"Invalid Share ID: {share_id}") from e

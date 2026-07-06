from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from ..hardware import HardwareInfo

console = Console()

def format_hw_panel(hw: HardwareInfo) -> None:
    gpu_str = hw.gpu_name if hw.gpu_name else "No dedicated GPU detected"
    vram_str = f"{hw.vram_gb:.1f} GB" if hw.vram_gb else "Shared (Uses RAM)"
    bw_str = f"{hw.memory_bandwidth:.0f} GB/s" if hw.memory_bandwidth else "Unknown bandwidth"
    ram_str = f"{hw.system_ram_gb:.1f} GB" if hw.system_ram_gb else "N/A"
    
    text = Text()
    text.append(f"🖥️  {gpu_str}\n", style="bold")
    
    if hw.is_apple_silicon:
        text.append(f"Unified Memory: {ram_str}  ·  BW: {bw_str}\n")
        text.append(f"Platform: {hw.platform} (Apple Silicon)")
    else:
        text.append(f"VRAM: {vram_str}  ·  BW: {bw_str}\n")
        text.append(f"System RAM: {ram_str}  ·  {hw.platform}")
        
    panel = Panel(text, expand=False, border_style="blue")
    console.print(panel)

def _get_grade_markup(grade: str) -> str:
    emoji_map = {
        "S": "🧈",
        "A": "🔥",
        "B": "😐",
        "C": "🐌",
        "D": "🗑️",
        "F": "🗑️",
        "?": "🗑️"
    }
    return emoji_map.get(grade, "🗑️")

def _rule(title: str = "", style: str = "grey50") -> None:
    from rich.rule import Rule
    if title:
        console.print(Rule(f"[dim]{title}[/dim]", style=style))
    else:
        console.print(Rule(style=style))

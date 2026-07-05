from textual.app import ComposeResult
from textual.widgets import Static
from textual.containers import Container

from caniarun.hardware import HardwareInfo
from caniarun.share import generate_share_id


class HardwareBanner(Static):
    """Widget to display the detected hardware info."""

    def __init__(self, hw: HardwareInfo, **kwargs):
        super().__init__(**kwargs)
        self.hw = hw
        self.border_title = "Your Hardware"

    def compose(self) -> ComposeResult:
        gpu_str = self.hw.gpu_name if self.hw.gpu_name else "Unknown GPU"
        vram_str = f"{self.hw.vram_gb:.1f} GB" if self.hw.vram_gb else "[warning-text]⚠️ VRAM Not Detected[/warning-text]"
        ram_str = f"{self.hw.system_ram_gb:.1f} GB" if self.hw.system_ram_gb else "N/A"
        share_id = generate_share_id(self.hw)


        text = (
            f"[bold cyan]💻[/]  {gpu_str} · VRAM: {vram_str} · RAM: {ram_str} · {self.hw.platform}"
        )
        yield Static(text, classes="hardware-content")
        yield Static(f"[dim]share id:[/dim]  [bold]{share_id}[/bold]", id="share-id-input")

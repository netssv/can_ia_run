from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Input, Label, Static, Button, TabbedContent, TabPane
from textual.containers import Vertical, Horizontal
from textual.binding import Binding

from caniarun.hardware import HardwareInfo
from caniarun.share import generate_share_id, decode_share_id
from caniarun.compat import evaluate_all


class ShareScreen(ModalScreen):
    """Modal to share your hardware ID or compare against another."""

    BINDINGS = [Binding("escape", "dismiss", "Close")]

    CSS = """
    ShareScreen {
        align: center middle;
    }
    #share-dialog {
        width: 76;
        background: #1e293b;
        border: round #00ff9c;
        padding: 1 2;
        height: auto;
    }
    #share-dialog Label {
        color: #94a3b8;
        margin-bottom: 1;
    }
    #share-id-box {
        background: #0f172a;
        color: #00ff9c;
        text-align: center;
        border: round #334155;
        padding: 1 1;
        height: auto;
        margin-bottom: 1;
    }
    #copy-status {
        height: 1;
        text-align: center;
        margin-bottom: 1;
    }
    #compare-label {
        margin-top: 1;
    }
    #compare-input {
        margin-bottom: 1;
    }
    #compare-status {
        height: 1;
        text-align: center;
        margin-bottom: 1;
    }
    #btn-row {
        height: 3;
        align: right middle;
    }
    Button {
        margin-left: 1;
    }
    """

    def __init__(self, hw: HardwareInfo, **kwargs):
        super().__init__(**kwargs)
        self._hw = hw
        self._share_id = generate_share_id(hw)

    def compose(self) -> ComposeResult:
        with Vertical(id="share-dialog"):
            yield Label("Your Share ID  (select to copy):")
            yield Static(self._share_id, id="share-id-box")
            yield Static("", id="copy-status")
            yield Button("Copy to clipboard", id="btn-copy", variant="primary")

            yield Label("─" * 40, id="compare-label")
            yield Label("Paste another Share ID to compare:")
            yield Input(placeholder="HW-...", id="compare-input")
            yield Static("", id="compare-status")

            with Horizontal(id="btn-row"):
                yield Button("Load results", id="btn-load", variant="success")
                yield Button("Close", id="btn-close")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id

        if bid == "btn-close":
            self.dismiss()

        elif bid == "btn-copy":
            self._copy_to_clipboard(self._share_id)

        elif bid == "btn-load":
            raw = self.query_one("#compare-input", Input).value.strip()
            if not raw:
                self.query_one("#compare-status", Static).update("[red]Please enter a Share ID.[/red]")
                return
            try:
                hw = decode_share_id(raw)
                results = evaluate_all(hw)
                # Pass the new hw+results back to the caller via dismiss
                self.dismiss((hw, results))
            except ValueError as e:
                self.query_one("#compare-status", Static).update(f"[red]Invalid ID: {e}[/red]")

    def _copy_to_clipboard(self, text: str) -> None:
        import subprocess, shutil
        status = self.query_one("#copy-status", Static)
        for cmd in (["xclip", "-selection", "clipboard"], ["xsel", "--clipboard", "--input"], ["wl-copy"]):
            if shutil.which(cmd[0]):
                try:
                    subprocess.run(cmd, input=text.encode(), check=True)
                    status.update("[green]Copied to clipboard![/green]")
                    return
                except Exception:
                    pass
        status.update("[yellow]No clipboard tool found — select the ID above manually[/yellow]")

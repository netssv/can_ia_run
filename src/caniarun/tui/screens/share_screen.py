from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Static, TabbedContent, TabPane
from textual.containers import Vertical, Horizontal, Center
from textual.binding import Binding

from caniarun.share import generate_share_id, decode_share_id
from caniarun.compat import evaluate_all


class ShareScreen(ModalScreen):
    """Modal to share your hardware ID or load another user's results."""

    BINDINGS = [Binding("escape", "dismiss", "Close")]

    CSS = """
    ShareScreen {
        align: center middle;
    }
    #share-dialog {
        width: 64;
        height: auto;
        max-height: 22;
        background: #1e293b;
        border: round #00ff9c;
        padding: 1 2;
    }
    #share-dialog Label {
        margin-bottom: 1;
    }
    #share-id-display {
        background: #0f172a;
        color: #00ff9c;
        text-align: center;
        border: round #334155;
        padding: 1;
        margin-bottom: 1;
    }
    #compare-input {
        margin-bottom: 1;
    }
    #btn-row {
        height: 3;
        align: right middle;
    }
    Button {
        margin-left: 1;
    }
    #status-msg {
        color: #f97316;
        text-align: center;
        height: 1;
    }
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._share_id = generate_share_id(self.app.hw)

    def compose(self) -> ComposeResult:
        with Vertical(id="share-dialog"):
            with TabbedContent():
                with TabPane("My Share ID", id="tab-my-id"):
                    yield Label("Your hardware profile ID:")
                    yield Static(self._share_id, id="share-id-display")
                    yield Static("", id="status-msg")
                    with Horizontal(id="btn-row"):
                        yield Button("📋 Copy to clipboard", id="btn-copy", variant="primary")
                        yield Button("Close", id="btn-close")

                with TabPane("Compare with another", id="tab-compare"):
                    yield Label("Paste a Share ID to see results on that hardware:")
                    yield Input(placeholder="HW-...", id="compare-input")
                    yield Static("", id="compare-status")
                    with Horizontal(id="btn-row"):
                        yield Button("🔍 Load results", id="btn-load", variant="success")
                        yield Button("Close", id="btn-close-2")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id

        if btn_id == "btn-close" or btn_id == "btn-close-2":
            self.dismiss()

        elif btn_id == "btn-copy":
            self._copy_to_clipboard(self._share_id)

        elif btn_id == "btn-load":
            raw = self.query_one("#compare-input", Input).value.strip()
            if not raw:
                self.query_one("#compare-status", Static).update("[red]Please enter a Share ID.[/red]")
                return
            try:
                hw = decode_share_id(raw)
                results = evaluate_all(hw)
                # Push results to app state and reload
                self.app.hw = hw
                self.app.results = results
                self.query_one("#compare-status", Static).update(
                    f"[green]Loaded! VRAM={hw.vram_gb} GB  RAM={hw.system_ram_gb} GB[/green]"
                )
                # Dismiss after short delay so user sees the message
                self.set_timer(1.5, self.dismiss)
            except ValueError as e:
                self.query_one("#compare-status", Static).update(f"[red]Invalid ID: {e}[/red]")

    def _copy_to_clipboard(self, text: str) -> None:
        import subprocess, shutil
        status = self.query_one("#status-msg", Static)
        # Try xclip, xsel, wl-copy in order
        for cmd in (["xclip", "-selection", "clipboard"], ["xsel", "--clipboard", "--input"], ["wl-copy"]):
            if shutil.which(cmd[0]):
                try:
                    subprocess.run(cmd, input=text.encode(), check=True)
                    status.update("[green]Copied![/green]")
                    return
                except Exception:
                    pass
        status.update("[yellow]Could not copy — select the ID above manually.[/yellow]")

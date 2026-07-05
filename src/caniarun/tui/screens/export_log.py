from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static, Footer, Header, Button
from textual.binding import Binding
from textual.containers import Vertical, Center

class ExportLogScreen(Screen):
    """Option 4: Export log file."""
    
    BINDINGS = [Binding("escape", "app.pop_screen", "Back")]

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="export-container"):
            with Center():
                yield Static("This will generate a 'caniarun.log' file in the current directory.", id="export-msg")
            with Center():
                yield Button("Export Now", variant="primary", id="btn-export")
                yield Button("Cancel", id="btn-cancel")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-cancel":
            self.app.pop_screen()
        elif event.button.id == "btn-export":
            # Do the export
            from caniarun.log_emitter import emit_log
            emit_log(self.app.hw, self.app.results, "caniarun.log", include_f16=False)
            
            msg = self.query_one("#export-msg", Static)
            msg.update("[bold green]Success![/] Log generated at caniarun.log\nPress Escape to go back.")
            
            # Disable export button
            event.button.disabled = True

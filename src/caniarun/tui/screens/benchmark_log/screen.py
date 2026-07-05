from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import TabbedContent, TabPane, Header, Footer
from textual.binding import Binding

from .tab_valid import TabValid
from .tab_filter import TabFilter
from .tab_invalid import TabInvalid
from .tab_metrics import TabMetrics

class BenchmarkLogScreen(Screen):
    """Option 6: Benchmark Run Log explorer."""
    
    BINDINGS = [Binding("escape", "app.pop_screen", "Back")]

    def compose(self) -> ComposeResult:
        yield Header()
        with TabbedContent():
            with TabPane("Valid Runs", id="tab-valid"):
                yield TabValid()
            with TabPane("Filter", id="tab-filter"):
                yield TabFilter()
            with TabPane("Invalid Runs", id="tab-invalid"):
                yield TabInvalid()
            with TabPane("Metrics", id="tab-metrics"):
                yield TabMetrics()
        yield Footer()

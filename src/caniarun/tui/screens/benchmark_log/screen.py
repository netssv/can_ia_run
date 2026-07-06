from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import TabbedContent, TabPane, Header, Footer, Static, Button, Input
from textual.containers import Horizontal, Center
from textual.binding import Binding

from .tab_valid import TabValid
from .tab_filter import TabFilter
from .tab_invalid import TabInvalid
from .tab_metrics import TabMetrics

class BenchmarkLogScreen(Screen):
    """Benchmark Run Log explorer with live data, export and import."""
    
    BINDINGS = [Binding("escape", "app.pop_screen", "Back")]

    DEFAULT_CSS = """
    #bench-actions {
        height: 3;
        margin: 0 1;
        align: center middle;
    }
    #bench-actions Button {
        margin: 0 1;
    }
    #bench-status {
        height: 1;
        text-align: center;
        color: #94a3b8;
        margin-bottom: 1;
    }
    #import-path-input {
        width: 60;
        margin: 0 1;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        
        total = len(self.app.benchmark_records)
        valid = sum(1 for r in self.app.benchmark_records if r.is_valid)
        invalid = total - valid
        share_id = ""
        try:
            from caniarun.share import generate_share_id
            share_id = generate_share_id(self.app.hw)
        except Exception:
            pass
        
        yield Static(
            f"[bold cyan]📊 Live Benchmark[/] — [green]{valid}[/] valid · [red]{invalid}[/] invalid · {total} total   [dim]ID: {share_id}[/dim]",
            id="bench-status"
        )
        
        with Center(id="bench-actions"):
            yield Button("🔄 Re-run Benchmark", id="btn-rerun", variant="primary")
            yield Button("💾 Export Results", id="btn-export", variant="success")
            yield Button("📂 Import Results", id="btn-import", variant="warning")
        
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

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-rerun":
            self._rerun_benchmark()
        elif event.button.id == "btn-export":
            self._export_results()
        elif event.button.id == "btn-import":
            self._import_results()

    def _rerun_benchmark(self) -> None:
        """Re-run the benchmark using current hardware + fresh evaluation."""
        from caniarun.benchmarklog.runner import run_benchmark
        from caniarun.compat import evaluate_all
        
        # Re-evaluate with current hardware
        self.app.results = evaluate_all(self.app.hw)
        self.app.benchmark_records = run_benchmark(self.app.hw, self.app.results)
        
        # Refresh the screen
        self.app.pop_screen()
        self.app.push_screen(BenchmarkLogScreen())

    def _export_results(self) -> None:
        """Export current benchmark records to a JSON file."""
        from caniarun.benchmarklog.runner import export_benchmark
        
        try:
            path = export_benchmark(
                self.app.benchmark_records,
                self.app.hw,
                filepath="benchmark_export.json"
            )
            self.notify(f"✅ Exported to {path}", title="Export Complete", severity="information")
        except Exception as e:
            self.notify(f"❌ Export failed: {e}", title="Error", severity="error")

    def _import_results(self) -> None:
        """Import benchmark records from a JSON file."""
        from caniarun.benchmarklog.runner import import_benchmark
        import os
        
        filepath = "benchmark_export.json"
        if not os.path.exists(filepath):
            self.notify("❌ No benchmark_export.json found in current directory", title="Error", severity="error")
            return
            
        try:
            records, metadata = import_benchmark(filepath)
            self.app.benchmark_records = records
            
            share_id = metadata.get("share_id", "Unknown")
            hw_info = metadata.get("hardware", {})
            gpu = hw_info.get("gpu_name", "Unknown GPU")
            exported_at = metadata.get("exported_at", "Unknown")
            
            self.notify(
                f"📂 Loaded {len(records)} records from {gpu} ({share_id[:20]}...)\nExported: {exported_at}",
                title="Import Complete",
                severity="information"
            )
            
            # Refresh the screen
            self.app.pop_screen()
            self.app.push_screen(BenchmarkLogScreen())
            
        except Exception as e:
            self.notify(f"❌ Import failed: {e}", title="Error", severity="error")

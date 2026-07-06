from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import TabbedContent, TabPane, Header, Footer, Static, Button
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
        height: 2;
        text-align: center;
        color: #94a3b8;
        padding: 0 2;
        margin-bottom: 1;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("", id="bench-status")

        with Center(id="bench-actions"):
            yield Button("🔄 Re-run", id="btn-rerun", variant="primary")
            yield Button("💾 Export", id="btn-export", variant="success")
            yield Button("📂 Import", id="btn-import", variant="warning")
            if getattr(self.app, "benchmark_source", "live") != "live":
                yield Button("🏠 My Results", id="btn-local", variant="default")

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

    def on_mount(self) -> None:
        self._update_status_banner()

    def _update_status_banner(self) -> None:
        total = len(self.app.benchmark_records)
        valid = sum(1 for r in self.app.benchmark_records if r.is_valid)
        invalid = total - valid

        source = getattr(self.app, "benchmark_source", "live")

        try:
            from caniarun.share import generate_share_id
            share_id = generate_share_id(self.app.hw)
            short_id = share_id[:28] + "…"
        except Exception:
            short_id = "Unknown"

        if source == "live":
            line1 = f"[bold cyan]📊 Live Benchmark[/] · [dim]{short_id}[/dim]"
        else:
            # Show the imported source's info
            hw_info = getattr(self.app, "benchmark_hw_meta", {})
            gpu = hw_info.get("gpu_name", "Unknown GPU")[:30]
            plat = hw_info.get("platform", "")
            imported_id = source[:28] + ("…" if len(source) > 28 else "")
            line1 = f"[bold yellow]📂 Imported:[/] [cyan]{gpu}[/] · {plat} · [dim]{imported_id}[/dim]"

        line2 = f"[green]{valid}[/] valid · [red]{invalid}[/] invalid · {total} total records"

        self.query_one("#bench-status", Static).update(f"{line1}\n{line2}")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-rerun":
            self._rerun_benchmark()
        elif event.button.id == "btn-export":
            self._export_results()
        elif event.button.id == "btn-import":
            self._import_results()
        elif event.button.id == "btn-local":
            self._restore_local()

    def _rerun_benchmark(self) -> None:
        from caniarun.benchmarklog.runner import run_benchmark
        from caniarun.compat import evaluate_all

        self.app.results = evaluate_all(self.app.hw)
        self.app.benchmark_records = run_benchmark(self.app.hw, self.app.results)
        self.app.benchmark_source = "live"
        if hasattr(self.app, "benchmark_hw_meta"):
            del self.app.benchmark_hw_meta

        self.app.pop_screen()
        self.app.push_screen(BenchmarkLogScreen())

    def _export_results(self) -> None:
        from caniarun.benchmarklog.runner import export_benchmark

        try:
            path = export_benchmark(self.app.benchmark_records, self.app.hw)
            self.notify(f"✅ Exported to:\n{path}", title="Export Complete", severity="information")
        except Exception as e:
            self.notify(f"❌ Export failed: {e}", title="Error", severity="error")

    def _import_results(self) -> None:
        from caniarun.benchmarklog.runner import import_benchmark
        import os
        import glob

        # Look for any benchmark_*.json in current dir
        files = sorted(glob.glob("benchmark_*.json") + ["benchmark_export.json"])
        files = [f for f in files if os.path.exists(f)]

        if not files:
            self.notify(
                "❌ No benchmark JSON found.\nRun Export first or place a file here.",
                title="No file found", severity="error"
            )
            return

        # Use the most recent file
        filepath = max(files, key=os.path.getmtime)

        try:
            records, metadata = import_benchmark(filepath)

            # Save imported context on the app
            self.app.benchmark_records = records
            self.app.benchmark_source = metadata.get("share_id", "imported")
            self.app.benchmark_hw_meta = metadata.get("hardware", {})

            hw_info = metadata.get("hardware", {})
            gpu = hw_info.get("gpu_name", "Unknown GPU")
            share_id = metadata.get("share_id", "Unknown")[:24]

            self.notify(
                f"📂 Loaded {len(records)} records\n{gpu}\n{share_id}…",
                title="Import Complete",
                severity="information"
            )

            self.app.pop_screen()
            self.app.push_screen(BenchmarkLogScreen())

        except Exception as e:
            self.notify(f"❌ Import failed: {e}", title="Error", severity="error")

    def _restore_local(self) -> None:
        """Restore live results from this machine."""
        from caniarun.benchmarklog.runner import run_benchmark

        self.app.benchmark_records = run_benchmark(self.app.hw, self.app.results)
        self.app.benchmark_source = "live"
        if hasattr(self.app, "benchmark_hw_meta"):
            del self.app.benchmark_hw_meta

        self.app.pop_screen()
        self.app.push_screen(BenchmarkLogScreen())

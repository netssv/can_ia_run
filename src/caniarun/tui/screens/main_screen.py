from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Footer, Header, Input, TabbedContent, TabPane, Static, Button
from textual.containers import Vertical, Horizontal
from textual.binding import Binding

from caniarun.tui.widgets.hardware_banner import HardwareBanner
from caniarun.tui.screens.benchmark_log.tab_metrics import TabMetrics
from caniarun.tui.screens.benchmark_log.tab_valid import TabValid
from caniarun.tui.screens.benchmark_log.tab_invalid import TabInvalid
from caniarun.tui.screens.tabs.tab_overview import TabOverview
from caniarun.tui.screens.tabs.tab_breakdown import TabBreakdown

from caniarun.share import generate_share_id

class MainScreen(Screen):
    """Unified God Screen Dashboard."""

    BINDINGS = [
        Binding("q", "app.exit", "Quit"),
        Binding("s", "action_share", "Share/Compare"),
        Binding("e", "action_export", "Export JSON")
    ]

    CSS = """
    #main-header-container {
        padding: 1 2 0 2;
        height: auto;
        background: #0f172a;
    }
    HardwareBanner {
        /* Override styles.tcss fixed width */
        width: 100%;
        margin-bottom: 1;
        border: round #00ff9c;
        padding: 0 1;
        background: #1e293b;
    }
    #header-tools {
        height: 3;
        margin-bottom: 1;
    }
    #quick-dashboard {
        /* Override styles.tcss fixed width */
        width: 1fr;
        padding: 0 1;
        content-align: left middle;
        background: transparent;
        border: none;
    }
    #action-buttons {
        width: auto;
        align: right middle;
    }
    #action-buttons Button {
        margin-left: 1;
    }
    #filter-container {
        padding: 0 2;
        margin: 1 0;
        height: 3;
    }
    .filter-input {
        width: 100%;
    }
    DataTable {
        height: 1fr;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        
        # 1. TOP SECTION (Always Visible)
        with Vertical(id="main-header-container"):
            yield HardwareBanner(self.app.hw, id="hardware-banner")
            
            with Horizontal(id="header-tools"):
                yield Static("", id="quick-dashboard")
                
                with Horizontal(id="action-buttons"):
                    yield Button("🔄 Share / Compare ID", id="btn-share", variant="primary")
                    yield Button("💾 Export JSON", id="btn-export", variant="success")
                    yield Button("❌ Quit", id="btn-quit", variant="error")

        # 2. MAIN BODY (Tabs)
        with TabbedContent(id="main-tabs"):
            with TabPane("📑 Vibe Check", id="tab-overview"):
                yield TabOverview(id="comp-overview")
                
            with TabPane("📑 Full Breakdown", id="tab-breakdown"):
                yield TabBreakdown(id="comp-breakdown")
                
            with TabPane("📊 Report Card", id="tab-metrics"):
                yield TabMetrics()
                
            with TabPane("📝 Benchmark Valid", id="tab-valid"):
                yield TabValid()
                
            with TabPane("⚠️ Benchmark Invalid", id="tab-invalid"):
                yield TabInvalid()
                
        yield Footer()

    def on_mount(self) -> None:
        self._update_quick_stats()
        self._update_banner_context()

    def _update_banner_context(self) -> None:
        banner = self.query_one(HardwareBanner)
        local_id = generate_share_id(self.app.hw)
        if getattr(self.app, "benchmark_source", local_id) != local_id:
            hw_meta = getattr(self.app, "benchmark_hw_meta", {})
            gpu_name = hw_meta.get("gpu_name", "Unknown GPU").replace("[", "\\[")
            platform = hw_meta.get("platform", "Unknown OS").replace("[", "\\[")
            source_id = getattr(self.app, "benchmark_source", "").replace("[", "\\[")
            display_id = f"{source_id[:20]}..." if len(source_id) > 20 else source_id
            
            # Subvert the banner content directly for imported
            text = f"[cyan]📂 Imported:[/] [bold]{gpu_name}[/bold] · {platform}"
            banner.query_one(".hardware-content", Static).update(text)
            banner.query_one("#share-id-input", Static).update(f"[dim]Share ID:[/] [dim]{display_id}[/dim]")
        else:
            banner.update_hw(self.app.hw)

    def _update_quick_stats(self) -> None:
        can_run = 0
        tight = 0
        cannot_run = 0

        STATUS_RANK = {"can-run": 3, "tight": 2, "can-run-slow": 1, "cannot-run": 0}

        for r in self.app.results:
            best_status = None
            best_rank = -1
            for q in r.quants:
                if q.quant_name == "F16": continue
                rank = STATUS_RANK.get(q.status, -1)
                if rank > best_rank:
                    best_rank = rank
                    best_status = q.status

            if best_status == "can-run":
                can_run += 1
            elif best_status == "tight":
                tight += 1
            elif best_status in ("cannot-run", "can-run-slow"):
                cannot_run += 1

        total = len(self.app.results)
        text = f"[bold green]🧈/🔥 {can_run} Smooth/Dope[/]   [bold yellow]😐 {tight} Meh usable[/]   [bold red]🐌/🗑️ {cannot_run} Laggy/Trash[/]   [dim]({total} unique models)[/dim]"
        self.query_one("#quick-dashboard", Static).update(text)

    # ── EVENTS ────────────────────────────────────────────────────────
    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.has_class("filter-input"):
            filter_val = event.value.strip().lower()
            # Sync inputs
            for inp in self.query(".filter-input"):
                if inp.id != event.input.id:
                    inp.value = event.value
            
            # Tell tabs to update
            self.query_one("#comp-overview", TabOverview).update_filter(filter_val)
            self.query_one("#comp-breakdown", TabBreakdown).update_filter(filter_val)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id
        if bid == "btn-quit":
            self.app.exit()
        elif bid == "btn-share":
            self.action_share()
        elif bid == "btn-export":
            self.action_export()

    # ── ACTIONS ───────────────────────────────────────────────────────
    def action_share(self) -> None:
        from caniarun.tui.screens.share_screen import ShareScreen
        
        def on_share_close(result) -> None:
            if result is not None:
                hw, results = result
                self.app.hw = hw
                self.app.results = results
                
                from caniarun.benchmarklog.runner import run_benchmark
                self.app.benchmark_records = run_benchmark(hw, results)
                self.app.benchmark_source = generate_share_id(hw)
                self.app.benchmark_hw_meta = {
                    "gpu_name": hw.gpu_name or "Unknown GPU",
                    "platform": hw.platform or "Unknown"
                }
                # Fully remount to reload all tabs and stats with new data
                self.app.pop_screen()
                self.app.push_screen(MainScreen())

        self.app.push_screen(ShareScreen(hw=self.app.hw), on_share_close)

    def action_export(self) -> None:
        from caniarun.benchmarklog.runner import export_benchmark
        path = export_benchmark(self.app.benchmark_records, self.app.hw)
        self.notify(f"Benchmark exported to:\n{path}", title="Export Success", severity="information", timeout=5)

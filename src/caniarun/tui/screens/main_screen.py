from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Header, Input, TabbedContent, TabPane, Static, Button
from textual.containers import Vertical, Horizontal, Center
from textual.binding import Binding

from caniarun.tui.widgets.hardware_banner import HardwareBanner
from caniarun.tui.screens.benchmark_log.tab_metrics import TabMetrics
from caniarun.tui.screens.benchmark_log.tab_valid import TabValid
from caniarun.tui.screens.benchmark_log.tab_invalid import TabInvalid

from caniarun.log_emitter import GRADE_TO_LEVEL
from caniarun.benchmarklog.rules import STATUS_DISPLAY
from caniarun.share import generate_share_id

# Reuse Sorting definitions from the old Model Explorer
OVERVIEW_SORT_KEYS = {
    0: lambda r: r.model.name,
    1: lambda r: r.model.family,
    2: lambda r: r.model.params_billions,
    3: lambda r: r.best_grade,
    4: lambda r: getattr(max(r.quants, key=lambda q: {"S":6,"A":5,"B":4,"C":3,"D":2,"F":1,"?":0}.get(q.grade, 0)), "toks_per_sec", 0) or 0
}
OVERVIEW_COLUMNS = ["Model", "Family", "Params", "Vibe", "Speed"]

BREAKDOWN_SORT_KEYS = {
    0: lambda item: item[0].model.name,
    1: lambda item: item[0].model.params_billions,
    2: lambda item: item[1].quant_name,
    3: lambda item: item[1].vram_gb,
    4: lambda item: item[1].status,
    5: lambda item: item[1].toks_per_sec or 0
}
BREAKDOWN_COLUMNS = ["Model", "Params", "Quant", "VRAM Req", "Vibe Status", "Speed"]


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

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._filter_text = ""
        # Overview sorting state
        self._over_sort_col = 3  # Vibe
        self._over_sort_asc = False
        # Breakdown sorting state
        self._break_sort_col = 4  # Vibe Status
        self._break_sort_asc = False

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
                with Vertical(id="filter-container"):
                    yield Input(placeholder="Search by family or model name...", id="filter-input-1", classes="filter-input")
                yield DataTable(id="overview-table")
                
            with TabPane("📑 Full Breakdown", id="tab-breakdown"):
                with Vertical(id="filter-container"):
                    yield Input(placeholder="Search by family or model name...", id="filter-input-2", classes="filter-input")
                yield DataTable(id="breakdown-table")
                
            with TabPane("📊 Report Card", id="tab-metrics"):
                yield TabMetrics()
                
            with TabPane("📝 Benchmark Valid", id="tab-valid"):
                yield TabValid()
                
            with TabPane("⚠️ Benchmark Invalid", id="tab-invalid"):
                yield TabInvalid()
                
        yield Footer()

    def on_mount(self) -> None:
        self._update_quick_stats()
        self._render_tables()
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

    # ── TAB 1 & 2 RENDERING ───────────────────────────────────────────
    def _render_tables(self) -> None:
        self._render_overview()
        self._render_breakdown()

    def _render_overview(self) -> None:
        table = self.query_one("#overview-table", DataTable)
        table.cursor_type = "row"
        table.zebra_stripes = True
        table.clear(columns=True)

        headers = []
        for i, col in enumerate(OVERVIEW_COLUMNS):
            if i == self._over_sort_col:
                arrow = " ▲" if self._over_sort_asc else " ▼"
                headers.append(col + arrow)
            else:
                headers.append(col)
        table.add_columns(*headers)

        filtered = []
        for r in self.app.results:
            match_fam = self._filter_text in r.model.family.lower()
            match_name = self._filter_text in r.model.name.lower()
            if not self._filter_text or match_fam or match_name:
                filtered.append(r)

        grade_order = {"S": 6, "A": 5, "B": 4, "C": 3, "D": 2, "F": 1, "?": 0}
        key_fn = (lambda r: grade_order.get(r.best_grade, 0)) if self._over_sort_col == 3 else OVERVIEW_SORT_KEYS.get(self._over_sort_col, lambda r: r.model.name)
        sorted_results = sorted(filtered, key=key_fn, reverse=not self._over_sort_asc)

        for r in sorted_results:
            best_q = max(r.quants, key=lambda q: grade_order.get(q.grade, 0))
            vibe = GRADE_TO_LEVEL.get(best_q.grade, "🗑️ Trash mode")
            speed = f"{best_q.toks_per_sec:.0f} tok/s" if best_q.toks_per_sec else "N/A"
            table.add_row(r.model.name, r.model.family, f"{r.model.params_billions}B", vibe, speed)

    def _render_breakdown(self) -> None:
        table = self.query_one("#breakdown-table", DataTable)
        table.cursor_type = "row"
        table.zebra_stripes = True
        table.clear(columns=True)

        headers = []
        for i, col in enumerate(BREAKDOWN_COLUMNS):
            if i == self._break_sort_col:
                arrow = " ▲" if self._break_sort_asc else " ▼"
                headers.append(col + arrow)
            else:
                headers.append(col)
        table.add_columns(*headers)

        flat_list = []
        for r in self.app.results:
            match_fam = self._filter_text in r.model.family.lower()
            match_name = self._filter_text in r.model.name.lower()
            if not self._filter_text or match_fam or match_name:
                for q in r.quants:
                    if q.quant_name == "F16": continue
                    flat_list.append((r, q))

        status_order = {"can-run": 3, "tight": 2, "can-run-slow": 1, "cannot-run": 0, "unknown": -1}
        key_fn = (lambda item: status_order.get(item[1].status, 0)) if self._break_sort_col == 4 else BREAKDOWN_SORT_KEYS.get(self._break_sort_col, lambda item: item[0].model.name)
        sorted_items = sorted(flat_list, key=key_fn, reverse=not self._break_sort_asc)

        STATUS_VIBE = {
            "can-run": "[green]🧈 Runs clean[/]",
            "tight": "[yellow]😐 Tight squeeze[/]",
            "can-run-slow": "[orange1]🐌 CPU crawl[/]",
            "cannot-run": "[red]🗑️ No chance[/]",
            "unknown": "[dim]🗑️ No chance[/]"
        }

        for r, q in sorted_items:
            vibe_status = STATUS_VIBE.get(q.status, "[dim]🗑️ No chance[/]")
            speed = f"{q.toks_per_sec:.0f} tok/s" if q.toks_per_sec else "N/A"
            table.add_row(r.model.name, f"{r.model.params_billions}B", q.quant_name, f"{q.vram_gb:.1f} GB", vibe_status, speed)

    # ── EVENTS ────────────────────────────────────────────────────────
    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.has_class("filter-input"):
            self._filter_text = event.value.strip().lower()
            for inp in self.query(".filter-input"):
                if inp.id != event.input.id:
                    inp.value = event.value
            self._render_tables()

    def on_data_table_header_selected(self, event: DataTable.HeaderSelected) -> None:
        table_id = event.data_table.id
        col_index = event.column_index
        
        if table_id == "overview-table":
            if col_index not in OVERVIEW_SORT_KEYS: return
            if self._over_sort_col == col_index:
                self._over_sort_asc = not self._over_sort_asc
            else:
                self._over_sort_col = col_index
                self._over_sort_asc = True
            self._render_overview()
            
        elif table_id == "breakdown-table":
            if col_index not in BREAKDOWN_SORT_KEYS: return
            if self._break_sort_col == col_index:
                self._break_sort_asc = not self._break_sort_asc
            else:
                self._break_sort_col = col_index
                self._break_sort_asc = True
            self._render_breakdown()

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

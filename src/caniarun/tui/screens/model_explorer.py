from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Header, Input, TabbedContent, TabPane
from textual.containers import Vertical
from textual.binding import Binding

from caniarun.log_emitter import GRADE_TO_LEVEL

STATUS_VIBE = {
    "can-run": "[green]🧈 Runs clean[/]",
    "tight": "[yellow]😐 Tight squeeze[/]",
    "can-run-slow": "[orange1]🐌 CPU crawl[/]",
    "cannot-run": "[red]🗑️ No chance[/]",
    "unknown": "[dim]🗑️ No chance[/]"
}

# Sorting keys for Overview Table
OVERVIEW_SORT_KEYS = {
    0: lambda r: r.model.name,
    1: lambda r: r.model.family,
    2: lambda r: r.model.params_billions,
    3: lambda r: r.best_grade,
    4: lambda r: getattr(max(r.quants, key=lambda q: {"S":6,"A":5,"B":4,"C":3,"D":2,"F":1,"?":0}.get(q.grade, 0)), "toks_per_sec", 0) or 0
}
OVERVIEW_COLUMNS = ["Model", "Family", "Params", "Vibe", "Speed"]

# Sorting keys for Breakdown Table
BREAKDOWN_SORT_KEYS = {
    0: lambda item: item[0].model.name,
    1: lambda item: item[0].model.params_billions,
    2: lambda item: item[1].quant_name,
    3: lambda item: item[1].vram_gb,
    4: lambda item: item[1].status,
    5: lambda item: item[1].toks_per_sec or 0
}
BREAKDOWN_COLUMNS = ["Model", "Params", "Quant", "VRAM Req", "Vibe Status", "Speed"]


class ModelExplorerScreen(Screen):
    """Unified Model Explorer Screen with Tabbed Content."""
    
    BINDINGS = [Binding("escape", "app.pop_screen", "Back")]

    DEFAULT_CSS = """
    #filter-container {
        padding: 0 1;
        margin-bottom: 0;
    }
    #filter-input {
        margin: 1 0;
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
        with Vertical(id="filter-container"):
            yield Input(placeholder="Search by family or model name...", id="filter-input")
        
        with TabbedContent(id="tabs"):
            with TabPane("Vibe Check", id="tab-overview"):
                yield DataTable(id="overview-table")
            with TabPane("Full Breakdown", id="tab-breakdown"):
                yield DataTable(id="breakdown-table")
        yield Footer()

    def on_mount(self) -> None:
        self._render_tables()
        self.query_one("#filter-input", Input).focus()

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

        # Filter
        filtered = []
        for r in self.app.results:
            match_fam = self._filter_text in r.model.family.lower()
            match_name = self._filter_text in r.model.name.lower()
            if not self._filter_text or match_fam or match_name:
                filtered.append(r)

        # Sort
        grade_order = {"S": 6, "A": 5, "B": 4, "C": 3, "D": 2, "F": 1, "?": 0}
        if self._over_sort_col == 3:
            key_fn = lambda r: grade_order.get(r.best_grade, 0)
        else:
            key_fn = OVERVIEW_SORT_KEYS.get(self._over_sort_col, lambda r: r.model.name)
            
        sorted_results = sorted(filtered, key=key_fn, reverse=not self._over_sort_asc)

        for r in sorted_results:
            best_q = max(r.quants, key=lambda q: grade_order.get(q.grade, 0))
            vibe = GRADE_TO_LEVEL.get(best_q.grade, "🗑️ Trash mode")
            speed = f"{best_q.toks_per_sec:.0f} tok/s" if best_q.toks_per_sec else "N/A"
            table.add_row(
                r.model.name,
                r.model.family,
                f"{r.model.params_billions}B",
                vibe,
                speed
            )

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

        # Flatten & Filter
        flat_list = []
        for r in self.app.results:
            match_fam = self._filter_text in r.model.family.lower()
            match_name = self._filter_text in r.model.name.lower()
            if not self._filter_text or match_fam or match_name:
                for q in r.quants:
                    if q.quant_name == "F16":
                        continue
                    flat_list.append((r, q))

        # Sort
        status_order = {"can-run": 3, "tight": 2, "can-run-slow": 1, "cannot-run": 0, "unknown": -1}
        if self._break_sort_col == 4:
            key_fn = lambda item: status_order.get(item[1].status, 0)
        else:
            key_fn = BREAKDOWN_SORT_KEYS.get(self._break_sort_col, lambda item: item[0].model.name)

        sorted_items = sorted(flat_list, key=key_fn, reverse=not self._break_sort_asc)

        for r, q in sorted_items:
            vibe_status = STATUS_VIBE.get(q.status, "[dim]🗑️ No chance[/]")
            speed = f"{q.toks_per_sec:.0f} tok/s" if q.toks_per_sec else "N/A"
            table.add_row(
                r.model.name,
                f"{r.model.params_billions}B",
                q.quant_name,
                f"{q.vram_gb:.1f} GB",
                vibe_status,
                speed
            )

    def on_input_changed(self, event: Input.Changed) -> None:
        self._filter_text = event.value.strip().lower()
        self._render_tables()

    def on_data_table_header_selected(self, event: DataTable.HeaderSelected) -> None:
        table_id = event.data_table.id
        col_index = event.column_index
        
        if table_id == "overview-table":
            if col_index not in OVERVIEW_SORT_KEYS:
                return
            if self._over_sort_col == col_index:
                self._over_sort_asc = not self._over_sort_asc
            else:
                self._over_sort_col = col_index
                self._over_sort_asc = True
            self._render_overview()
            
        elif table_id == "breakdown-table":
            if col_index not in BREAKDOWN_SORT_KEYS:
                return
            if self._break_sort_col == col_index:
                self._break_sort_asc = not self._break_sort_asc
            else:
                self._break_sort_col = col_index
                self._break_sort_asc = True
            self._render_breakdown()

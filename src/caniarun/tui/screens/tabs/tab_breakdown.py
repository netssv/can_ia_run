from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import DataTable, Input

BREAKDOWN_SORT_KEYS = {
    0: lambda item: item[0].model.name,
    1: lambda item: item[0].model.params_billions,
    2: lambda item: item[1].quant_name,
    3: lambda item: item[1].vram_gb,
    4: lambda item: item[1].status,
    5: lambda item: item[1].toks_per_sec or 0
}
BREAKDOWN_COLUMNS = ["Model", "Params", "Quant", "VRAM Req", "Vibe Status", "Speed"]

class TabBreakdown(Vertical):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.filter_text = ""
        self._break_sort_col = 4  # Vibe Status
        self._break_sort_asc = False

    def compose(self) -> ComposeResult:
        with Vertical(id="filter-container"):
            yield Input(placeholder="Search by family or model name...", id="filter-input-2", classes="filter-input")
        yield DataTable(id="breakdown-table")

    def on_mount(self) -> None:
        self.render_table()

    def update_filter(self, text: str) -> None:
        self.filter_text = text
        self.render_table()

    def render_table(self) -> None:
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
            match_fam = self.filter_text in r.model.family.lower()
            match_name = self.filter_text in r.model.name.lower()
            if not self.filter_text or match_fam or match_name:
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

    def on_data_table_header_selected(self, event: DataTable.HeaderSelected) -> None:
        if event.data_table.id != "breakdown-table":
            return
            
        col_index = event.column_index
        if col_index not in BREAKDOWN_SORT_KEYS: return
        
        if self._break_sort_col == col_index:
            self._break_sort_asc = not self._break_sort_asc
        else:
            self._break_sort_col = col_index
            self._break_sort_asc = True
            
        self.render_table()

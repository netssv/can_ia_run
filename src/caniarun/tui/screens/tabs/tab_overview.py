from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import DataTable, Input

from caniarun.log_emitter import GRADE_TO_LEVEL

OVERVIEW_SORT_KEYS = {
    0: lambda r: r.model.name,
    1: lambda r: r.model.family,
    2: lambda r: r.model.params_billions,
    3: lambda r: r.best_grade,
    4: lambda r: getattr(max(r.quants, key=lambda q: {"S":6,"A":5,"B":4,"C":3,"D":2,"F":1,"?":0}.get(q.grade, 0)), "toks_per_sec", 0) or 0
}
OVERVIEW_COLUMNS = ["Model", "Family", "Params", "Vibe", "Speed"]

class TabOverview(Vertical):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.filter_text = ""
        self._over_sort_col = 3  # Vibe
        self._over_sort_asc = False

    def compose(self) -> ComposeResult:
        with Vertical(id="filter-container"):
            yield Input(placeholder="Search by family or model name...", id="filter-input-1", classes="filter-input")
        yield DataTable(id="overview-table")

    def on_mount(self) -> None:
        self.render_table()

    def update_filter(self, text: str) -> None:
        self.filter_text = text
        self.render_table()

    def render_table(self) -> None:
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
            match_fam = self.filter_text in r.model.family.lower()
            match_name = self.filter_text in r.model.name.lower()
            if not self.filter_text or match_fam or match_name:
                filtered.append(r)

        grade_order = {"S": 6, "A": 5, "B": 4, "C": 3, "D": 2, "F": 1, "?": 0}
        key_fn = (lambda r: grade_order.get(r.best_grade, 0)) if self._over_sort_col == 3 else OVERVIEW_SORT_KEYS.get(self._over_sort_col, lambda r: r.model.name)
        sorted_results = sorted(filtered, key=key_fn, reverse=not self._over_sort_asc)

        for r in sorted_results:
            best_q = max(r.quants, key=lambda q: grade_order.get(q.grade, 0))
            vibe = GRADE_TO_LEVEL.get(best_q.grade, "🗑️ Trash mode")
            speed = f"{best_q.toks_per_sec:.0f} tok/s" if best_q.toks_per_sec else "N/A"
            table.add_row(r.model.name, r.model.family, f"{r.model.params_billions}B", vibe, speed)

    def on_data_table_header_selected(self, event: DataTable.HeaderSelected) -> None:
        if event.data_table.id != "overview-table":
            return
            
        col_index = event.column_index
        if col_index not in OVERVIEW_SORT_KEYS: return
        
        if self._over_sort_col == col_index:
            self._over_sort_asc = not self._over_sort_asc
        else:
            self._over_sort_col = col_index
            self._over_sort_asc = True
            
        self.render_table()

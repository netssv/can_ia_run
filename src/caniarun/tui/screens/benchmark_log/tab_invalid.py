from textual.app import ComposeResult
from textual.widgets import DataTable
from textual.containers import Container

SORT_KEYS = {
    0: lambda r: r.id,
    1: lambda r: r.source,
    2: lambda r: r.model_name,
    3: lambda r: len(r.validation_errors),
}

COLUMNS = ["ID", "Source", "Model", "Errors"]

class TabInvalid(Container):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._sort_col = 3
        self._sort_asc = False
        self._records = []

    def compose(self) -> ComposeResult:
        yield DataTable(id="invalid-table")

    def on_mount(self) -> None:
        self._records = [r for r in self.app.benchmark_records if not r.is_valid]
        self._render_table()

    def _render_table(self) -> None:
        table = self.query_one(DataTable)
        table.cursor_type = "row"
        table.zebra_stripes = True
        table.clear(columns=True)

        headers = []
        for i, col in enumerate(COLUMNS):
            if i == self._sort_col:
                arrow = " ▲" if self._sort_asc else " ▼"
                headers.append(col + arrow)
            else:
                headers.append(col)
        table.add_columns(*headers)

        key_fn = SORT_KEYS.get(self._sort_col, lambda r: r.id)
        sorted_records = sorted(self._records, key=key_fn, reverse=not self._sort_asc)

        for r in sorted_records:
            errors = " | ".join(r.validation_errors)
            table.add_row(r.id, r.source, r.model_name, f"[red]{errors}[/red]")

    def on_data_table_header_selected(self, event: DataTable.HeaderSelected) -> None:
        col_index = event.column_index
        if col_index not in SORT_KEYS:
            return
        if self._sort_col == col_index:
            self._sort_asc = not self._sort_asc
        else:
            self._sort_col = col_index
            self._sort_asc = True
        self._render_table()

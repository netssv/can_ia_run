from textual.app import ComposeResult
from textual.widgets import DataTable, Input
from textual.containers import Container, Horizontal

class TabFilter(Container):
    def compose(self) -> ComposeResult:
        with Horizontal(id="filter-inputs"):
            yield Input(placeholder="Filter by status (e.g. runnable)...", id="input-status")
            yield Input(placeholder="Filter by model name...", id="input-model")
        yield DataTable(id="filter-table")
        
    def on_mount(self) -> None:
        self.table = self.query_one(DataTable)
        self.table.cursor_type = "row"
        self.table.add_columns("Model", "Status", "Source", "Score")
        self._populate_table()
        
    def _populate_table(self, status_filter="", model_filter=""):
        self.table.clear()
        valid_records = [r for r in self.app.benchmark_records if r.is_valid]
        
        for r in valid_records:
            if status_filter and status_filter.lower() not in r.fit_status.lower():
                continue
            if model_filter and model_filter.lower() not in r.model_name.lower():
                continue
            
            self.table.add_row(
                r.model_name, r.fit_status, r.source, str(r.score)
            )

    def on_input_changed(self, event: Input.Changed) -> None:
        status_filter = self.query_one("#input-status").value
        model_filter = self.query_one("#input-model").value
        self._populate_table(status_filter, model_filter)

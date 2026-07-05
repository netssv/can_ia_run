from textual.app import ComposeResult
from textual.widgets import DataTable
from textual.containers import Container

class TabInvalid(Container):
    def compose(self) -> ComposeResult:
        yield DataTable(id="invalid-table")
        
    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.cursor_type = "row"
        table.add_columns("ID", "Source", "Validation Errors")
        
        # Populate
        invalid_records = [r for r in self.app.benchmark_records if not r.is_valid]
        for r in invalid_records:
            errors = " | ".join(r.validation_errors)
            # Use red text for errors
            table.add_row(r.id, r.source, f"[red]{errors}[/red]")

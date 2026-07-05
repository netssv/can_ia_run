from textual.app import ComposeResult
from textual.widgets import DataTable
from textual.containers import Container

class TabValid(Container):
    def compose(self) -> ComposeResult:
        yield DataTable(id="valid-table")
        
    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.cursor_type = "row"
        table.zebra_stripes = True
        table.add_columns("ID", "Model", "Source", "Quant", "VRAM (Norm)", "Score", "Vibe", "Speed")
        
        # Populate
        valid_records = [r for r in self.app.benchmark_records if r.is_valid]
        for r in valid_records:
            speed = f"{r.toks_per_sec:.0f}" if r.toks_per_sec else "N/A"
            table.add_row(
                r.id, r.model_name, r.source, r.quant_level, 
                f"{r.vram_normalized_gb:.1f} GB", str(r.score), 
                r.vibe_level, speed
            )

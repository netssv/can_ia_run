from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Header
from textual.binding import Binding

class AllModelsScreen(Screen):
    """Option 1: Show all models (log format) in a DataTable."""
    
    BINDINGS = [Binding("escape", "app.pop_screen", "Back")]

    def compose(self) -> ComposeResult:
        yield Header()
        yield DataTable(id="all-models-table")
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.cursor_type = "row"
        table.zebra_stripes = True
        
        # Columns: timestamp, familia, modelo, vibe, tok/s
        table.add_columns("Timestamp", "Family", "Model", "Vibe", "Speed")
        
        from datetime import datetime
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # We need the grade mapping
        from caniarun.log_emitter import GRADE_TO_LEVEL
        
        # Sort results like CLI does: best grade first, then params
        def grade_val(g: str) -> int:
            return {"S": 6, "A": 5, "B": 4, "C": 3, "D": 2, "F": 1, "?": 0}.get(g, 0)
            
        sorted_results = sorted(
            self.app.results, 
            key=lambda r: (-grade_val(r.best_grade), r.model.params_billions)
        )
        
        for r in sorted_results:
            best_q = max(r.quants, key=lambda q: grade_val(q.grade))
            vibe = GRADE_TO_LEVEL.get(best_q.grade, "🗑️ Trash mode")
            speed = f"{best_q.toks_per_sec:.0f} tok/s" if best_q.toks_per_sec else "N/A"
            
            table.add_row(
                now,
                r.model.family,
                r.model.name,
                vibe,
                speed
            )

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Header, Input
from textual.binding import Binding
from textual.containers import Vertical

class FilterFamilyScreen(Screen):
    """Option 2: Filter by family."""
    
    BINDINGS = [Binding("escape", "app.pop_screen", "Back")]

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical():
            yield Input(placeholder="Type family to filter (e.g., Llama, Qwen)...", id="family-input")
            yield DataTable(id="filtered-table")
        yield Footer()

    def on_mount(self) -> None:
        self.table = self.query_one(DataTable)
        self.table.cursor_type = "row"
        self.table.zebra_stripes = True
        self.table.add_columns("Timestamp", "Family", "Model", "Vibe", "Speed")
        self._populate_table()
        
        # Focus input automatically
        self.query_one(Input).focus()

    def _populate_table(self, filter_text: str = "") -> None:
        self.table.clear()
        filter_text = filter_text.lower()
        
        from datetime import datetime
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        from caniarun.log_emitter import GRADE_TO_LEVEL
        
        def grade_val(g: str) -> int:
            return {"S": 6, "A": 5, "B": 4, "C": 3, "D": 2, "F": 1, "?": 0}.get(g, 0)
            
        sorted_results = sorted(
            self.app.results, 
            key=lambda r: (-grade_val(r.best_grade), r.model.params_billions)
        )
        
        for r in sorted_results:
            if filter_text and filter_text not in r.model.family.lower():
                continue
                
            best_q = max(r.quants, key=lambda q: grade_val(q.grade))
            vibe = GRADE_TO_LEVEL.get(best_q.grade, "🗑️ Trash mode")
            speed = f"{best_q.toks_per_sec:.0f} tok/s" if best_q.toks_per_sec else "N/A"
            
            self.table.add_row(now, r.model.family, r.model.name, vibe, speed)

    def on_input_changed(self, event: Input.Changed) -> None:
        self._populate_table(event.value)

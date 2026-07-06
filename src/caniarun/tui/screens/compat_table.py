from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Header
from textual.binding import Binding

class CompatTableScreen(Screen):
    """Option 3: Show full compatibility table with colors."""
    
    BINDINGS = [Binding("escape", "app.pop_screen", "Back")]

    def compose(self) -> ComposeResult:
        yield Header()
        yield DataTable(id="compat-table")
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.cursor_type = "row"
        
        table.add_columns("Model", "Params", "Quant", "RAM Req", "VRAM Req", "Fit Status", "Grade")
        
        def grade_val(g: str) -> int:
            return {"S": 6, "A": 5, "B": 4, "C": 3, "D": 2, "F": 1, "?": 0}.get(g, 0)
            
        sorted_results = sorted(
            self.app.results, 
            key=lambda r: (-grade_val(r.best_grade), r.model.params_billions)
        )
        
        for r in sorted_results:
            for q in r.quants:
                if q.quant_name == "F16": continue # skip F16 by default as in CLI
                
                # Assign colors based on fit_status
                # can-run = green, tight = yellow, can-run-slow = orange, cannot-run = red
                color = "white"
                status = q.status
                if status == "can-run":
                    color = "green"
                elif status == "tight":
                    color = "yellow"
                elif status == "can-run-slow":
                    color = "orange"
                elif status == "cannot-run":
                    color = "red"
                
                # We can use rich markup directly in the cells
                status_styled = f"[{color}]{status}[/{color}]"
                grade_styled = f"[{color}]{q.grade}[/]"
                
                ram_str = f"{r.model.min_ram_gb:.1f} GB" if r.model.min_ram_gb else "-"
                vram_str = f"{q.vram_gb:.1f} GB" if q.vram_gb else "-"
                
                table.add_row(
                    r.model.name,
                    f"{r.model.params_billions}B",
                    q.quant_name,
                    ram_str,
                    vram_str,
                    status_styled,
                    grade_styled
                )

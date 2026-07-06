from typing import List
from rich.table import Table

from ..compat import ModelResult
from .common import console, _get_grade_markup

def render_table(results: List[ModelResult], show_f16: bool = False, specific_quant: str = None) -> None:
    if not results:
        console.print("[yellow]No models match the given filters.[/yellow]")
        return
        
    # Sort results: best grade first (S=6 to F=1), then by params ascending
    def grade_val(g: str) -> int:
        return {"S": 6, "A": 5, "B": 4, "C": 3, "D": 2, "F": 1, "?": 0}.get(g, 0)
        
    sorted_results = sorted(results, key=lambda r: (-grade_val(r.best_grade), r.model.params_billions))
    
    table = Table(show_header=True, header_style="bold magenta", border_style="grey50")
    table.add_column("Model", style="cyan", no_wrap=True)
    table.add_column("Params", justify="right")
    
    # Determine which columns to show
    quants_to_show = ["Q2_K", "Q3_K_M", "Q4_K_M", "Q5_K_M", "Q6_K", "Q8_0"]
    if show_f16:
        quants_to_show.append("F16")
    if specific_quant:
        quants_to_show = [specific_quant]
        
    for q in quants_to_show:
        table.add_column(q, justify="center")
        
    for res in sorted_results:
        row = [res.model.name, res.model.params]
        q_map = {q.quant_name: q for q in res.quants}
        
        for q_name in quants_to_show:
            if q_name in q_map:
                row.append(_get_grade_markup(q_map[q_name].grade))
            else:
                row.append("[dim]-[/dim]")
                
        table.add_row(*row)
        
    console.print(table)
    
    # Legend using vibes
    legend = (
        "[bold green]🧈 Smooth[/]   "
        "[green]🔥 Dope[/]   "
        "[bright_green]😐 Meh[/]   "
        "[yellow]🐌 Laggy[/]   "
        "[red]🗑️ Trash[/]"
    )
    console.print(legend)

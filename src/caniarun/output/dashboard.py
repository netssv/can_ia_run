import datetime
from typing import List

from rich.panel import Panel
from rich.text import Text

from ..hardware import HardwareInfo
from ..compat import ModelResult
from ..share import generate_share_id
from .common import console

def render_dashboard(hw: HardwareInfo, results: List[ModelResult]) -> None:
    console.print()
    canary_logo = """[bold yellow]
       __
      ('v')  [bold cyan]caniarun[/bold cyan]
     //-=-\\\\ [dim]AI Hardware Checker[/dim]
     (\\_=_/)
      ^^ ^^  [/bold yellow]
"""
    console.print(canary_logo)
    
    gpu_str = hw.gpu_name if hw.gpu_name else "Unknown GPU"
    vram_str = f"{hw.vram_gb:.1f} GB" if hw.vram_gb else "N/A"
    ram_str = f"{hw.system_ram_gb:.1f} GB" if hw.system_ram_gb else "N/A"
    share_id = generate_share_id(hw)
    
    console.print(Panel(
        Text.assemble(
            ("  🖥  Your Hardware\n", "bold white"),
            (f"  {gpu_str} · VRAM: {vram_str} · RAM: {ram_str} · {hw.platform}\n", "bright_blue"),
            (f"  Share ID: {share_id}", "dim")
        ),
        border_style="cyan",
        padding=(0, 1),
        expand=False
    ))
    console.print()
    
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    grade_levels = {
        "S": "[🧈 Smooth as butter]",
        "A": "[🔥 Dope run]",
        "B": "[😐 Meh usable]",
        "C": "[🐌 Laggy vibes]",
        "D": "[🗑️ Trash mode]",
        "F": "[🗑️ Trash mode]"
    }
    
    tier_messages = {
        "S": "runs great, no issues",
        "A": "smooth, {toks:.0f} tok/s",
        "B": "usable but tight, {toks:.0f} tok/s",
        "C": "slow response, high RAM usage",
        "D": "barely fits, expect freezing",
        "F": "won't fit, crashes likely"
    }
    
    tiered_results = {"S": [], "A": [], "B": [], "C": [], "D": [], "F": []}
    for r in results:
        tiered_results[r.best_grade].append(r)
        
    displayed_count = 0
    
    for grade in ["S", "A", "B", "C", "D", "F"]:
        if grade not in tiered_results or not tiered_results[grade]:
            continue
            
        tier_models = tiered_results[grade]
        tier_models.sort(key=lambda x: x.model.params_billions)
        
        for r in tier_models[:2]:
            if displayed_count >= 8:
                break
                
            level_str = grade_levels[grade]
            best_q = max(r.quants, key=lambda q: {"S":6,"A":5,"B":4,"C":3,"D":2,"F":1,"?":0}.get(q.grade, 0))
            msg = tier_messages[grade].format(toks=best_q.toks_per_sec or 0)
            
            color = "white"
            if grade == "S": color = "bold green"
            elif grade == "A": color = "green"
            elif grade == "B": color = "bright_yellow"
            elif grade == "C": color = "yellow"
            elif grade in ["D", "F"]: color = "red"
            
            console.print(f"[{color}]{level_str:<21}[/{color}] [dim]{now}[/dim] {r.model.name} — {msg}")
            displayed_count += 1
            
        if displayed_count >= 8:
            break
            
    console.print()
    
    total = len(results)
    if total > 0:
        smooth_pct = sum(1 for r in results if r.best_grade in ["S", "A"]) / total * 100
        if smooth_pct >= 60:
            verdict = "🚀 This rig runs AI like a pro. You've got serious headroom."
        elif smooth_pct >= 30:
            verdict = "⚡ Decent hardware, smart choices needed. Stick to Q4_K_M."
        elif smooth_pct > 0:
            verdict = "🐌 Small models only — a dedicated GPU would change everything."
        else:
            verdict = "🚨 Hardware limit reached. Consider cloud inference."
    else:
        verdict = "Unknown health"
        
    console.print(f"System Health: {verdict}")
    console.print()

import json
from typing import List, Dict, Any

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from .hardware import HardwareInfo
from .compat import ModelResult

console = Console()

def format_hw_panel(hw: HardwareInfo) -> None:
    gpu_str = hw.gpu_name if hw.gpu_name else "No dedicated GPU detected"
    vram_str = f"{hw.vram_gb:.1f} GB" if hw.vram_gb else "N/A"
    bw_str = f"{hw.memory_bandwidth:.0f} GB/s" if hw.memory_bandwidth else "Unknown bandwidth"
    ram_str = f"{hw.system_ram_gb:.1f} GB" if hw.system_ram_gb else "N/A"
    
    text = Text()
    text.append(f"🖥️  {gpu_str}\n", style="bold")
    
    if hw.is_apple_silicon:
        text.append(f"Unified Memory: {ram_str}  ·  BW: {bw_str}\n")
        text.append(f"Platform: {hw.platform} (Apple Silicon)")
    else:
        text.append(f"VRAM: {vram_str}  ·  BW: {bw_str}\n")
        text.append(f"System RAM: {ram_str}  ·  {hw.platform}")
        
    panel = Panel(text, expand=False, border_style="blue")
    console.print(panel)

def _get_grade_markup(grade: str) -> str:
    color_map = {
        "S": "bold green",
        "A": "green",
        "B": "bright_green",
        "C": "yellow",
        "D": "orange1",
        "F": "red",
        "?": "dim"
    }
    color = color_map.get(grade, "white")
    return f"[{color}][{grade}][/{color}]"

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
    # Standard quants: Q2_K, Q3_K_M, Q4_K_M, Q5_K_M, Q6_K, Q8_0, (F16 if requested)
    quants_to_show = ["Q2_K", "Q3_K_M", "Q4_K_M", "Q5_K_M", "Q6_K", "Q8_0"]
    if show_f16:
        quants_to_show.append("F16")
    if specific_quant:
        quants_to_show = [specific_quant]
        
    for q in quants_to_show:
        table.add_column(q, justify="center")
        
    for res in sorted_results:
        row = [res.model.name, res.model.params]
        
        # Build quant map
        q_map = {q.quant_name: q for q in res.quants}
        
        for q_name in quants_to_show:
            if q_name in q_map:
                row.append(_get_grade_markup(q_map[q_name].grade))
            else:
                row.append("[dim]-[/dim]")
                
        table.add_row(*row)
        
    console.print(table)
    
    # Legend
    legend = (
        "[bold green]S[/] = Runs great  "
        "[green]A[/] = Runs well  "
        "[bright_green]B[/] = Decent  "
        "[yellow]C[/] = Tight fit  "
        "[orange1]D[/] = Barely runs  "
        "[red]F[/] = Too heavy"
    )
    console.print(legend)

def render_json(hw: HardwareInfo, results: List[ModelResult]) -> None:
    data: Dict[str, Any] = {
        "hardware": {
            "gpu_name": hw.gpu_name,
            "gpu_vendor": hw.gpu_vendor,
            "vram_gb": hw.vram_gb,
            "system_ram_gb": hw.system_ram_gb,
            "memory_bandwidth": hw.memory_bandwidth,
            "is_apple_silicon": hw.is_apple_silicon,
            "platform": hw.platform
        },
        "models": []
    }
    
    for r in results:
        model_data = {
            "id": r.model.id,
            "name": r.model.name,
            "params": r.model.params,
            "quants": {}
        }
        for q in r.quants:
            model_data["quants"][q.quant_name] = {
                "grade": q.grade,
                "score": q.score,
                "toks_per_sec": q.toks_per_sec,
                "vram_gb": q.vram_gb
            }
        data["models"].append(model_data)
        
    print(json.dumps(data, indent=2))

def render_dashboard(hw: HardwareInfo, results: List[ModelResult]) -> None:
    from rich.panel import Panel
    from rich.text import Text
    import datetime
    from caniarun.share import generate_share_id
    
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
    
    # Select best models for each tier
    grade_val = {"S": 6, "A": 5, "B": 4, "C": 3, "D": 2, "F": 1, "?": 0}
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
    
    # Group results by grade
    tiered_results = {"S": [], "A": [], "B": [], "C": [], "D": [], "F": []}
    for r in results:
        tiered_results[r.best_grade].append(r)
        
    displayed_count = 0
    
    for grade in ["S", "A", "B", "C", "D", "F"]:
        if grade not in tiered_results or not tiered_results[grade]:
            continue
            
        tier_models = tiered_results[grade]
        # Sort by params to show a good variety (e.g. smallest first, or some specific order)
        tier_models.sort(key=lambda x: x.model.params_billions)
        
        # Take up to 2 models per tier to show about 8 total
        for r in tier_models[:2]:
            if displayed_count >= 8:
                break
                
            level_str = grade_levels[grade]
            
            # Find best quant for this grade
            best_q = max(r.quants, key=lambda q: {"S":6,"A":5,"B":4,"C":3,"D":2,"F":1,"?":0}.get(q.grade, 0))
            
            msg = tier_messages[grade].format(toks=best_q.toks_per_sec or 0)
            
            # Color coding
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
    
    # Calculate health verdict
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

def _rule(title: str = "", style: str = "grey50") -> None:
    from rich.rule import Rule
    if title:
        console.print(Rule(f"[dim]{title}[/dim]", style=style))
    else:
        console.print(Rule(style=style))

def render_analysis_report(
    report: Any,
    filepath: str,
    hw_info: str = "Unknown Hardware",
    results: list = None
) -> None:
    console.print()

    # ── HEADER ──────────────────────────────────────────────────────────────
    console.print(Panel(
        Text.assemble(
            ("  canIArun · System Report\n", "bold white"),
            (f"  {hw_info}\n", "bright_blue"),
            (f"  {filepath}", "dim"),
        ),
        border_style="bright_blue",
        padding=(0, 1),
    ))

    if report.total_processed == 0:
        console.print("\n[yellow]No events found in scan.[/yellow]\n")
        return

    # ── PERFORMANCE BREAKDOWN ────────────────────────────────────────────────
    _rule("Performance Breakdown")
    console.print()

    level_styles = {
        "🧈 Smooth as butter": ("bold green",   "S"),
        "🔥 Dope run":         ("green",         "A"),
        "😐 Meh usable":       ("bright_yellow", "B"),
        "🐌 Laggy vibes":      ("yellow",        "C"),
        "🗑️ Trash mode":      ("red",            "F"),
    }

    total = report.total_processed
    bar_width = 30

    for level, (style, grade) in level_styles.items():
        count = report.level_counts.get(level, 0)
        pct   = (count / total) * 100
        filled = round((count / total) * bar_width)
        bar = f"[{style}]{'█' * filled}[/{style}][dim]{'░' * (bar_width - filled)}[/dim]"
        console.print(f"  {level:<22}  {bar}  [{style}]{count:>3}[/{style}] [dim]{pct:>4.1f}%[/dim]")

    if report.malformed_count > 0:
        pct = (report.malformed_count / total) * 100
        console.print(f"\n  [red]⚠  Malformed lines:[/]  {report.malformed_count}  ({pct:.1f}%)")

    # ── COMMON ISSUES ────────────────────────────────────────────────────────
    console.print()
    _rule("Compatibility Issues")
    console.print()

    issue_icons = {
        "Crash Risk":          ("💥", "red"),
        "GPU Incompatible":    ("🎮", "orange1"),
        "Excessive RAM Usage": ("💾", "yellow"),
        "CPU Offloading":      ("🐢", "bright_yellow"),
        "Low Bandwidth":       ("⚡", "cyan"),
    }
    issue_tips = {
        "Crash Risk":          "Model too large for your RAM — use a smaller quant or model",
        "GPU Incompatible":    "No dedicated VRAM — models run on system RAM (slow)",
        "Excessive RAM Usage": ">80% memory used — risk of swap / freezing",
        "CPU Offloading":      "Model split between GPU and CPU — big speed penalty",
        "Low Bandwidth":       "Memory bandwidth too low — expect <10 tok/s",
    }

    any_issue = False
    for issue, (icon, style) in issue_icons.items():
        count = report.issue_counts.get(issue, 0)
        if count > 0:
            any_issue = True
            tip = issue_tips.get(issue, "")
            console.print(f"  {icon}  [{style}]{issue:<22}[/{style}]  {count:>3} events  [dim]{tip}[/dim]")

    if not any_issue:
        console.print("  [bold green]✓  No compatibility issues — your hardware is solid![/]")

    # ── TOP MODEL PICKS ──────────────────────────────────────────────────────
    if results:
        console.print()
        _rule("Top Models for Your Hardware")
        console.print()

        grade_val = {"S": 6, "A": 5, "B": 4, "C": 3, "D": 2, "F": 1, "?": 0}
        grade_style = {"S": "bold green", "A": "green", "B": "bright_yellow",
                       "C": "yellow", "D": "orange1", "F": "red", "?": "dim"}

        # Top 8 by best grade, then params ascending
        top = sorted(
            [r for r in results if grade_val.get(r.best_grade, 0) >= 3],
            key=lambda r: (-grade_val.get(r.best_grade, 0), r.model.params_billions)
        )[:8]

        if top:
            tbl = Table(box=None, show_header=True, header_style="dim", pad_edge=False, padding=(0, 2))
            tbl.add_column("Grade", justify="center", width=7)
            tbl.add_column("Model", style="cyan")
            tbl.add_column("Params", justify="right", style="dim")
            tbl.add_column("Best Quant", justify="center")
            tbl.add_column("~Speed", justify="right", style="bright_blue")

            for r in top:
                g = r.best_grade
                st = grade_style.get(g, "white")
                # Find the best quant result
                best_q = max(r.quants, key=lambda q: {"S":6,"A":5,"B":4,"C":3,"D":2,"F":1,"?":0}.get(q.grade, 0))
                speed_str = f"{best_q.toks_per_sec:.0f} t/s" if best_q.toks_per_sec else "?"
                tbl.add_row(
                    f"[{st}][{g}][/{st}]",
                    r.model.name,
                    r.model.params,
                    best_q.quant_name,
                    speed_str,
                )
            console.print(tbl)
        else:
            console.print("  [dim]No models with grade C or above on this hardware.[/dim]")

    # ── SYSTEM HEALTH VERDICT ────────────────────────────────────────────────
    console.print()
    _rule("System Health Verdict")
    console.print()

    # Determine strongest and weakest performance bucket
    smooth_pct = (report.level_counts.get("🧈 Smooth as butter", 0) +
                  report.level_counts.get("🔥 Dope run", 0)) / total * 100
    trash_pct  = report.level_counts.get("🗑️ Trash mode", 0) / total * 100

    if smooth_pct >= 60:
        verdict   = "🚀  This rig runs AI like a pro"
        verdict_s = "bold green"
        body      = (
            f"  {smooth_pct:.0f}% of models run great on your hardware.\n"
            "  You've got serious headroom — go run those big models!"
        )
    elif smooth_pct >= 30:
        verdict   = "⚡  Decent hardware, smart choices needed"
        verdict_s = "bright_yellow"
        body      = (
            f"  {smooth_pct:.0f}% models are buttery smooth, {trash_pct:.0f}% are dead weight.\n"
            "  Stick to Q4_K_M and under 14B for a solid daily-driver experience."
        )
    elif smooth_pct > 0:
        verdict   = "🐌  Small models only — choose wisely"
        verdict_s = "yellow"
        body      = (
            f"  Only {smooth_pct:.0f}% of models run well — focus on anything under 8B.\n"
            "  A dedicated GPU would change everything."
        )
    else:
        verdict   = "🚨  Hardware limit reached"
        verdict_s = "bold red"
        body      = (
            "  No models run well on this hardware without offloading to RAM.\n"
            "  Consider cloud inference or upgrading to a dedicated GPU."
        )

    console.print(f"  [{verdict_s}]{verdict}[/{verdict_s}]")
    console.print(f"[dim]{body}[/dim]")
    console.print()
    _rule()
    console.print()

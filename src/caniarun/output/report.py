from typing import Any

from rich.panel import Panel
from rich.text import Text
from rich.table import Table

from .common import console, _rule

def render_analysis_report(
    report: Any,
    filepath: str,
    hw_info: str = "Unknown Hardware",
    results: list = None
) -> None:
    console.print()

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

    if results:
        console.print()
        _rule("Top Models for Your Hardware")
        console.print()

        grade_val = {"S": 6, "A": 5, "B": 4, "C": 3, "D": 2, "F": 1, "?": 0}
        grade_style = {"S": "bold green", "A": "green", "B": "bright_yellow",
                       "C": "yellow", "D": "orange1", "F": "red", "?": "dim"}

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

    console.print()
    _rule("System Health Verdict")
    console.print()

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

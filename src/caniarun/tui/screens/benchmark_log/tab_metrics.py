from textual.app import ComposeResult
from textual.widgets import Static
from textual.containers import Container, ScrollableContainer

from caniarun.benchmarklog.metrics import compute_metrics
from caniarun.benchmarklog.rules import STATUS_DISPLAY


def _bar(pct: float, width: int = 20) -> str:
    """Render a Unicode block progress bar with color based on percentage."""
    filled = round(pct / 100 * width)
    empty = width - filled

    if pct >= 70:
        color = "green"
    elif pct >= 40:
        color = "yellow"
    else:
        color = "red"

    bar = f"[{color}]{'█' * filled}[/{color}][dim]{'░' * empty}[/dim]"
    return bar


def _hardware_grade(runnable_pct: float) -> tuple:
    """Return (emoji, label, color) for the hardware grade."""
    if runnable_pct >= 70:
        return "🏆", "Beast Mode", "bold green"
    elif runnable_pct >= 50:
        return "💪", "Solid", "green"
    elif runnable_pct >= 30:
        return "😐", "Gets the job done", "yellow"
    else:
        return "🪫", "Limited", "red"


class TabMetrics(Container):
    def compose(self) -> ComposeResult:
        yield ScrollableContainer(Static(id="metrics-content"))

    def on_mount(self) -> None:
        m = compute_metrics(self.app.benchmark_records)

        # ── Hardware Grade ──────────────────────────────────────────────────
        total_models = len({r.model_name for r in self.app.benchmark_records if r.is_valid})
        runnable_models = len({
            r.model_name for r in self.app.benchmark_records
            if r.is_valid and r.fit_status in ("runnable", "runnable_tight")
        })
        runnable_pct = round((runnable_models / total_models * 100) if total_models > 0 else 0, 1)

        grade_emoji, grade_label, grade_color = _hardware_grade(runnable_pct)

        # ── Top family ──────────────────────────────────────────────────────
        top_family = max(m.source_counts, key=m.source_counts.get) if m.source_counts else "—"

        lines = []

        # ── Report Card ─────────────────────────────────────────────────────
        lines.append(f"[bold]── 🎯 Hardware Report Card ──[/bold]\n")
        lines.append(f"  [{grade_color}]{grade_emoji}  {grade_label}[/{grade_color}]\n")
        lines.append(
            f"  Your hardware can run [bold]{runnable_models}[/bold] of [bold]{total_models}[/bold] "
            f"unique models ([bold]{runnable_pct}%[/bold]) without issues."
        )
        lines.append(
            f"  The family with the most compatible models is [cyan][bold]{top_family}[/bold][/cyan]."
        )
        lines.append(f"  Average score: [bold]{m.avg_score}[/bold]/100\n")

        # ── Vibe Breakdown ──────────────────────────────────────────────────
        lines.append(f"[bold]── 🎨 Vibe Breakdown ──[/bold]\n")
        for vibe, count in m.vibe_counts.items():
            pct = (count / m.valid_count * 100) if m.valid_count > 0 else 0
            bar = _bar(pct)
            lines.append(f"  {vibe:<22} {bar}  [bold]{count:>3}[/bold] ({pct:>4.1f}%)")
        lines.append("")

        # ── Evaluation Summary ───────────────────────────────────────────────
        lines.append(f"[bold]── 📊 Evaluation Summary ──[/bold]\n")
        lines.append(f"  Total evaluations:  [bold]{m.total}[/bold]")
        valid_bar = _bar(m.valid_pct)
        lines.append(f"  Valid:   {valid_bar}  [green][bold]{m.valid_count}[/bold][/green] ({m.valid_pct}%)")
        invalid_bar = _bar(m.invalid_pct)
        lines.append(f"  Invalid: {invalid_bar}  [red][bold]{m.invalid_count}[/bold][/red] ({m.invalid_pct}%)")
        lines.append("")

        # ── Status Distribution ─────────────────────────────────────────────
        lines.append(f"[bold]── 🚦 Status Distribution ──[/bold]\n")
        total_status = sum(m.status_counts.values()) or 1
        for status, count in m.status_counts.items():
            display = STATUS_DISPLAY.get(status, status)
            pct = count / total_status * 100
            bar = _bar(pct)
            lines.append(f"  {display:<30} {bar}  [bold]{count:>3}[/bold]")
        lines.append("")

        # ── Models by Family ────────────────────────────────────────────────
        lines.append(f"[bold]── 🤖 Models by Family ──[/bold]\n")
        total_evals = sum(m.source_counts.values()) or 1
        for source, count in m.source_counts.items():
            pct = count / total_evals * 100
            bar = _bar(pct, width=15)
            lines.append(f"  {source:<15} {bar}  [bold]{count:>3}[/bold] evals")
        lines.append("")

        # ── Avg Speed by Vibe ───────────────────────────────────────────────
        if m.avg_toks_by_vibe:
            lines.append(f"[bold]── ⚡ Avg Speed by Vibe ──[/bold]\n")
            max_speed = max(m.avg_toks_by_vibe.values()) or 1
            for vibe, avg in m.avg_toks_by_vibe.items():
                pct = avg / max_speed * 100
                bar = _bar(pct)
                lines.append(f"  {vibe:<22} {bar}  ~[bold]{avg:.0f}[/bold] tok/s")

        widget = self.query_one("#metrics-content", Static)
        widget.update("\n".join(lines))

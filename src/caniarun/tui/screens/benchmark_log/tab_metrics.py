from textual.app import ComposeResult
from textual.widgets import Static
from textual.containers import Container

from caniarun.benchmarklog.metrics import compute_metrics
from caniarun.benchmarklog.rules import STATUS_DISPLAY

class TabMetrics(Container):
    def compose(self) -> ComposeResult:
        yield Static(id="metrics-content")
        
    def on_mount(self) -> None:
        m = compute_metrics(self.app.benchmark_records)
        
        lines = []
        lines.append("[b]── Evaluation Summary ──[/b]\n")
        lines.append(f"Total evaluations:  [b]{m.total}[/b]")
        lines.append(f"Valid:              [green][b]{m.valid_count}[/b][/green] ({m.valid_pct}%)")
        lines.append(f"Invalid:            [red][b]{m.invalid_count}[/b][/red] ({m.invalid_pct}%)")
        lines.append(f"Runnable models:    [cyan][b]{m.runnable_count}[/b][/cyan]")
        lines.append(f"Average score:      [b]{m.avg_score}[/b]/100\n")

        lines.append("[b]── Vibe Breakdown ──[/b]\n")
        for vibe, count in m.vibe_counts.items():
            if m.valid_count > 0:
                pct = count / m.valid_count
            else:
                pct = 0
            lines.append(f"{vibe:<22} {count:>3} ({pct*100:>4.1f}%)")

        lines.append("\n[b]── Status Distribution ──[/b]\n")
        for status, count in m.status_counts.items():
            display = STATUS_DISPLAY.get(status, status)
            lines.append(f"{display:<30} {count:>3}")

        lines.append("\n[b]── Models by Family ──[/b]\n")
        for source, count in m.source_counts.items():
            lines.append(f"{source:<20} {count:>3} evaluations")

        if m.avg_toks_by_vibe:
            lines.append("\n[b]── Avg Speed by Vibe ──[/b]\n")
            for vibe, avg in m.avg_toks_by_vibe.items():
                lines.append(f"{vibe:<22} ~{avg:.0f} tok/s")

        widget = self.query_one("#metrics-content", Static)
        widget.update("\n".join(lines))

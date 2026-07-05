from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static, OptionList
from textual.containers import Vertical, Center

from caniarun.tui.widgets.hardware_banner import HardwareBanner

LOGO = (
    "[bold yellow]"
    "    __\n"
    "  ('v')\n"
    " //-=-\\\\\n"
    " (\\_=_/)\n"
    "  ^^ ^^\n"
    "[/bold yellow]"
    "[bold cyan]  caniarun[/bold cyan]\n"
    "[dim]  AI Hardware Checker[/dim]"
)

class HomeScreen(Screen):
    """The main menu screen of caniarun."""

    def compose(self) -> ComposeResult:
        with Vertical(id="home-layout"):
            with Center():
                yield Static(LOGO, id="ascii-logo")

            with Center():
                yield HardwareBanner(self.app.hw, id="hardware-banner")

            with Center():
                yield Static("", id="quick-dashboard")

            with Center():
                yield Static("What do you want to do?", classes="menu-prompt")

            with Center():
                yield OptionList(
                    "Show all models (log format)",
                    "Filter by family (e.g., Llama, Qwen)",
                    "Show full compatibility table",
                    "Export log file",
                    "Exit",
                    "Benchmark Run Log",
                    id="main-menu"
                )

    def on_mount(self) -> None:
        can_run = 0
        tight = 0
        cannot_run = 0

        STATUS_RANK = {"can-run": 3, "tight": 2, "can-run-slow": 1, "cannot-run": 0}

        for r in self.app.results:
            # Pick the best status across all non-F16 quants for this model
            best_status = None
            best_rank = -1
            for q in r.quants:
                if q.quant_name == "F16":
                    continue
                rank = STATUS_RANK.get(q.status, -1)
                if rank > best_rank:
                    best_rank = rank
                    best_status = q.status

            if best_status == "can-run":
                can_run += 1
            elif best_status == "tight":
                tight += 1
            elif best_status in ("cannot-run", "can-run-slow"):
                cannot_run += 1

        text = f"[bold green]✅ {can_run} fast models[/]   [bold yellow]⚠ {tight} tight[/]   [bold red]❌ {cannot_run} slow/no[/]"
        self.query_one("#quick-dashboard", Static).update(text)
        # Ensure keyboard focus always starts on the menu, not the share ID input
        self.query_one("#main-menu", OptionList).focus()

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        idx = event.option_index
        if idx == 0:
            from caniarun.tui.screens.all_models import AllModelsScreen
            self.app.push_screen(AllModelsScreen())
        elif idx == 1:
            from caniarun.tui.screens.filter_family import FilterFamilyScreen
            self.app.push_screen(FilterFamilyScreen())
        elif idx == 2:
            from caniarun.tui.screens.compat_table import CompatTableScreen
            self.app.push_screen(CompatTableScreen())
        elif idx == 3:
            from caniarun.tui.screens.export_log import ExportLogScreen
            self.app.push_screen(ExportLogScreen())
        elif idx == 4:
            self.app.exit()
        elif idx == 5:
            from caniarun.tui.screens.benchmark_log.screen import BenchmarkLogScreen
            self.app.push_screen(BenchmarkLogScreen())

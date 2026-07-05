from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static, OptionList, Button
from textual.widgets.option_list import Option
from textual.containers import Vertical, Center, Horizontal

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

            with Center(id="share-btn-center"):
                yield Button("🔗 Share / Compare hardware", id="btn-share", variant="default")

            with Center():
                yield Static("What do you want to do?", classes="menu-prompt")

            with Center():
                yield OptionList(
                    Option("Show all models (log format)", id="opt-all"),
                    Option("─" * 28, id="sep-1", disabled=True),
                    Option("Filter by family (e.g., Llama, Qwen)", id="opt-family"),
                    Option("─" * 28, id="sep-2", disabled=True),
                    Option("Show full compatibility table", id="opt-compat"),
                    Option("─" * 28, id="sep-3", disabled=True),
                    Option("Export log file", id="opt-export"),
                    Option("─" * 28, id="sep-4", disabled=True),
                    Option("Exit", id="opt-exit"),
                    Option("─" * 28, id="sep-5", disabled=True),
                    Option("Benchmark Run Log", id="opt-bench"),
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
        opt_id = event.option.id
        if opt_id == "opt-all":
            from caniarun.tui.screens.all_models import AllModelsScreen
            self.app.push_screen(AllModelsScreen())
        elif opt_id == "opt-family":
            from caniarun.tui.screens.filter_family import FilterFamilyScreen
            self.app.push_screen(FilterFamilyScreen())
        elif opt_id == "opt-compat":
            from caniarun.tui.screens.compat_table import CompatTableScreen
            self.app.push_screen(CompatTableScreen())
        elif opt_id == "opt-export":
            from caniarun.tui.screens.export_log import ExportLogScreen
            self.app.push_screen(ExportLogScreen())
        elif opt_id == "opt-exit":
            self.app.exit()
        elif opt_id == "opt-bench":
            from caniarun.tui.screens.benchmark_log.screen import BenchmarkLogScreen
            self.app.push_screen(BenchmarkLogScreen())

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-share":
            from caniarun.tui.screens.share_screen import ShareScreen
            self.app.push_screen(ShareScreen())

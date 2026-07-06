from textual.app import App, ComposeResult
from textual.widgets import LoadingIndicator
from textual import work
from caniarun.hardware import detect, HardwareInfo
from caniarun.compat import evaluate_all
from caniarun.tui.screens.home import HomeScreen

class CaniarunApp(App):
    """Main Textual application for caniarun."""
    
    CSS_PATH = "styles.tcss"

    def __init__(self, hw=None, results=None, **kwargs):
        super().__init__(**kwargs)
        self.hw = hw
        self.results = results
        self.benchmark_records = []
        self.benchmark_source = "live"   # "live" or a share_id string when imported
        
    def compose(self) -> ComposeResult:
        yield LoadingIndicator(id="loading")

    def on_mount(self) -> None:
        if self.hw is None or self.results is None:
            self.load_data()
        else:
            self._finish_loading()

    @work(thread=True)
    def load_data(self) -> None:
        # Run detection in a background thread
        if self.hw is None:
            self.hw = detect()
        if self.results is None:
            self.results = evaluate_all(self.hw)
        
        self.app.call_from_thread(self._finish_loading)
        
    def _finish_loading(self) -> None:
        # Run the live benchmark pipeline on real evaluation results
        from caniarun.benchmarklog.runner import run_benchmark
        
        self.benchmark_records = run_benchmark(self.hw, self.results)

        # Remove loading and go to home screen
        try:
            self.query_one("#loading").remove()
        except Exception:
            pass
            
        self.push_screen(HomeScreen())

if __name__ == "__main__":
    app = CaniarunApp()
    app.run()

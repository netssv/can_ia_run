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
        # Load benchmark records
        import json
        from datetime import datetime
        import os
        from caniarun.benchmarklog.normalizer import NormalizedEvaluation
        from caniarun.benchmarklog.validator import validate_all
        
        if os.path.exists("data/eval_dirty.json"):
            with open("data/eval_dirty.json", "r", encoding="utf-8") as f:
                raw = json.load(f)
            records = []
            for item in raw:
                records.append(NormalizedEvaluation(
                    id=item.get("id", "unknown"),
                    source=item.get("source", ""),
                    model_name=item.get("model_name", ""),
                    provider=item.get("provider", ""),
                    quant_level=item.get("quant_level", ""),
                    vram_required_gb=item.get("vram_required_gb"),
                    vram_normalized_gb=item.get("vram_normalized_gb"),
                    score=item.get("score", 0),
                    vibe_level=item.get("vibe_level", ""),
                    fit_status=item.get("fit_status", ""),
                    toks_per_sec=item.get("toks_per_sec"),
                    timestamp=datetime.fromisoformat(item["timestamp"]),
                ))
            self.benchmark_records = validate_all(records)

        # Remove loading and go to home screen
        try:
            self.query_one("#loading").remove()
        except Exception:
            pass
            
        self.push_screen(HomeScreen())

if __name__ == "__main__":
    app = CaniarunApp()
    app.run()

import json
from datetime import datetime
from caniarun.benchmarklog.normalizer import NormalizedEvaluation
from caniarun.benchmarklog.validator import validate_all
from caniarun.benchmarklog.metrics import compute_metrics

def run_test():
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
        
    validated = validate_all(records)
    m = compute_metrics(validated)
    
    print(f"Total: {m.total}")
    print(f"Valid: {m.valid_count}")
    print(f"Invalid: {m.invalid_count}")
    
    assert m.valid_count > 0
    assert m.invalid_count > 0
    print("Regression test PASSED")

if __name__ == "__main__":
    run_test()

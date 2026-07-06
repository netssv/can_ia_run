"""
Benchmark runner — generates NormalizedEvaluation records from real hardware
scan results instead of loading from a static JSON file.

This bridges the gap between the live hardware evaluation engine and the
benchmark log normalizer/validator pipeline.
"""

import json
import os
from datetime import datetime
from typing import List, Optional

from caniarun.compat import ModelResult
from caniarun.hardware import HardwareInfo
from caniarun.share import generate_share_id
from caniarun.benchmarklog.normalizer import normalize_all, NormalizedEvaluation
from caniarun.benchmarklog.validator import validate_all


def run_benchmark(hw: HardwareInfo, results: List[ModelResult]) -> List[NormalizedEvaluation]:
    """
    Run the full benchmark pipeline on live evaluation results:
    1. Normalize all model × quant pairs into flat records
    2. Validate each record for data integrity
    Returns the validated list of NormalizedEvaluation records.
    """
    normalized = normalize_all(results)
    validated = validate_all(normalized)
    return validated


def export_benchmark(
    records: List[NormalizedEvaluation],
    hw: HardwareInfo,
    filepath: str = "",
) -> str:
    """
    Export benchmark records + hardware profile to a JSON file.
    Filename auto-uses the Share ID if no filepath given.
    Returns the absolute path of the exported file.
    """
    share_id = generate_share_id(hw)

    if not filepath:
        # Use truncated share_id as filename: benchmark_HW2-MC4w.json
        safe_id = share_id.replace("/", "_").replace("=", "")[:20]
        filepath = f"benchmark_{safe_id}.json"


    data = {
        "share_id": share_id,
        "hardware": {
            "gpu_name": hw.gpu_name,
            "gpu_vendor": hw.gpu_vendor,
            "vram_gb": hw.vram_gb,
            "system_ram_gb": hw.system_ram_gb,
            "memory_bandwidth": hw.memory_bandwidth,
            "is_apple_silicon": hw.is_apple_silicon,
            "platform": hw.platform,
        },
        "exported_at": datetime.now().isoformat(),
        "total_records": len(records),
        "records": [],
    }

    for r in records:
        data["records"].append({
            "id": r.id,
            "source": r.source,
            "model_name": r.model_name,
            "provider": r.provider,
            "quant_level": r.quant_level,
            "vram_required_gb": r.vram_required_gb,
            "vram_normalized_gb": r.vram_normalized_gb,
            "score": r.score,
            "vibe_level": r.vibe_level,
            "fit_status": r.fit_status,
            "toks_per_sec": r.toks_per_sec,
            "timestamp": r.timestamp.isoformat(),
            "is_valid": r.is_valid,
            "validation_errors": r.validation_errors,
        })

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return os.path.abspath(filepath)


def import_benchmark(filepath: str) -> tuple:
    """
    Import benchmark records from a previously exported JSON file.
    Returns (records: List[NormalizedEvaluation], metadata: dict).
    metadata contains share_id, hardware info, and export timestamp.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    records = []
    for item in data.get("records", []):
        rec = NormalizedEvaluation(
            id=item["id"],
            source=item.get("source", ""),
            model_name=item.get("model_name", ""),
            provider=item.get("provider", ""),
            quant_level=item.get("quant_level", ""),
            vram_required_gb=item.get("vram_required_gb", 0),
            vram_normalized_gb=item.get("vram_normalized_gb", 0),
            score=item.get("score", 0),
            vibe_level=item.get("vibe_level", ""),
            fit_status=item.get("fit_status", ""),
            toks_per_sec=item.get("toks_per_sec"),
            timestamp=datetime.fromisoformat(item["timestamp"]),
            is_valid=item.get("is_valid", True),
            validation_errors=item.get("validation_errors", []),
        )
        records.append(rec)

    metadata = {
        "share_id": data.get("share_id", ""),
        "hardware": data.get("hardware", {}),
        "exported_at": data.get("exported_at", ""),
        "total_records": data.get("total_records", len(records)),
    }

    return records, metadata

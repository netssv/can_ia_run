"""
Normalizer module — transforms raw ModelResult evaluations into a flat,
uniform NormalizedEvaluation record.

This is the "transaction normalizer" that takes heterogeneous evaluation
data from different model families and produces a consistent schema.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List

from caniarun.compat import ModelResult, QuantResult
from .rules import VIBE_MAPPING, VRAM_OVERHEAD_FACTOR, STATUS_NORMALIZATION


@dataclass
class NormalizedEvaluation:
    """A single normalized evaluation record — the 'transaction' in our system."""
    id: str                             # unique key: "model-id__quant-level"
    source: str                         # model family (Qwen, Llama, etc.)
    model_name: str                     # human-readable model name
    provider: str                       # who made it (Meta, Alibaba, etc.)
    quant_level: str                    # compression level (Q4_K_M, etc.)
    vram_required_gb: float             # raw VRAM from catalog
    vram_normalized_gb: float           # after applying overhead factor
    score: int                          # 0-100 compatibility score
    vibe_level: str                     # emoji vibe string
    fit_status: str                     # normalized status (runnable, degraded, etc.)
    toks_per_sec: Optional[float]       # estimated generation speed
    timestamp: datetime                 # when the evaluation was produced
    is_valid: bool = True               # set by validator later
    validation_errors: List[str] = field(default_factory=list)


def normalize_single(
    model_result: ModelResult,
    quant_result: QuantResult,
    eval_time: datetime,
) -> NormalizedEvaluation:
    """
    Convert one model-quant pair into a NormalizedEvaluation.

    Applies:
    - VRAM overhead factor (rules.VRAM_OVERHEAD_FACTOR)
    - Status normalization (rules.STATUS_NORMALIZATION)
    - Vibe level mapping (rules.VIBE_MAPPING)
    """
    model = model_result.model

    # Build unique ID from model id + quant level
    record_id = f"{model.id}__{quant_result.quant_name}"

    # Apply VRAM overhead to get real-world estimate
    vram_normalized = round(quant_result.vram_gb * VRAM_OVERHEAD_FACTOR, 2)

    # Map grade → vibe level
    vibe = VIBE_MAPPING.get(quant_result.grade, "🗑️ Trash mode")

    # Normalize fit status
    status = STATUS_NORMALIZATION.get(quant_result.status, "unknown")

    return NormalizedEvaluation(
        id=record_id,
        source=model.family,
        model_name=model.name,
        provider=model.provider,
        quant_level=quant_result.quant_name,
        vram_required_gb=quant_result.vram_gb,
        vram_normalized_gb=vram_normalized,
        score=quant_result.score,
        vibe_level=vibe,
        fit_status=status,
        toks_per_sec=quant_result.toks_per_sec,
        timestamp=eval_time,
    )


def normalize_all(results: List[ModelResult]) -> List[NormalizedEvaluation]:
    """
    Normalize all model evaluation results into flat records.
    Each model × quant combination becomes one NormalizedEvaluation.
    """
    now = datetime.now()
    normalized = []

    for model_result in results:
        for quant_result in model_result.quants:
            record = normalize_single(model_result, quant_result, now)
            normalized.append(record)

    return normalized

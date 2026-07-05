"""
Metrics module — computes summary statistics from normalized evaluation data.

All metrics are derived from a list of NormalizedEvaluation records.
"""

from dataclasses import dataclass, field
from typing import Dict, List
from collections import Counter

from .normalizer import NormalizedEvaluation
from .rules import VIBE_MAPPING, STATUS_DISPLAY


@dataclass
class EvaluationMetrics:
    """Complete metrics summary for a set of normalized evaluations."""
    total: int = 0
    valid_count: int = 0
    invalid_count: int = 0
    valid_pct: float = 0.0
    invalid_pct: float = 0.0

    # Counts by vibe level
    vibe_counts: Dict[str, int] = field(default_factory=dict)

    # Counts by normalized fit status
    status_counts: Dict[str, int] = field(default_factory=dict)

    # Counts by model family/source
    source_counts: Dict[str, int] = field(default_factory=dict)

    # Average VRAM per quant level (only valid records)
    avg_vram_by_quant: Dict[str, float] = field(default_factory=dict)

    # Average tok/s by vibe level (only valid records with speed data)
    avg_toks_by_vibe: Dict[str, float] = field(default_factory=dict)

    # Total runnable models (runnable or runnable_tight)
    runnable_count: int = 0

    # Average score (valid only)
    avg_score: float = 0.0


def compute_metrics(records: List[NormalizedEvaluation]) -> EvaluationMetrics:
    """Compute all metrics from a list of normalized evaluations."""
    m = EvaluationMetrics()
    m.total = len(records)

    if m.total == 0:
        return m

    valid = [r for r in records if r.is_valid]
    invalid = [r for r in records if not r.is_valid]

    m.valid_count = len(valid)
    m.invalid_count = len(invalid)
    m.valid_pct = round((m.valid_count / m.total) * 100, 1)
    m.invalid_pct = round((m.invalid_count / m.total) * 100, 1)

    # ── Vibe level counts (valid only) ──
    vibe_counter = Counter(r.vibe_level for r in valid)
    # Ensure all vibes appear even if zero
    for vibe in VIBE_MAPPING.values():
        m.vibe_counts[vibe] = vibe_counter.get(vibe, 0)

    # ── Fit status counts (valid only) ──
    status_counter = Counter(r.fit_status for r in valid)
    for status, display in STATUS_DISPLAY.items():
        m.status_counts[status] = status_counter.get(status, 0)

    # ── Source/family counts (valid only) ──
    m.source_counts = dict(Counter(r.source for r in valid).most_common())

    # ── Average VRAM by quant level ──
    quant_vrams: Dict[str, List[float]] = {}
    for r in valid:
        quant_vrams.setdefault(r.quant_level, []).append(r.vram_normalized_gb)
    m.avg_vram_by_quant = {
        q: round(sum(v) / len(v), 1) for q, v in quant_vrams.items()
    }

    # ── Average tok/s by vibe level ──
    vibe_toks: Dict[str, List[float]] = {}
    for r in valid:
        if r.toks_per_sec is not None and r.toks_per_sec > 0:
            vibe_toks.setdefault(r.vibe_level, []).append(r.toks_per_sec)
    m.avg_toks_by_vibe = {
        v: round(sum(t) / len(t), 1) for v, t in vibe_toks.items()
    }

    # ── Runnable count ──
    m.runnable_count = sum(
        1 for r in valid if r.fit_status in ("runnable", "runnable_tight")
    )

    # ── Average score ──
    if valid:
        m.avg_score = round(sum(r.score for r in valid) / len(valid), 1)

    return m

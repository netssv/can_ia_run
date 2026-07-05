"""
Explicit rules and configuration for normalizing caniarun evaluation results.

These rules are STUDENT DECISIONS — they define how raw evaluation data
gets transformed into a normalized, consistent format.
"""

from typing import Dict, List

# ── Vibe Level Mapping ──────────────────────────────────────────────────────
# Maps internal letter grades to user-facing vibe levels.
# Decision: D and F both map to "Trash mode" because below 40 score
# the experience is equally bad regardless of the exact number.
VIBE_MAPPING: Dict[str, str] = {
    "S": "🧈 Smooth as butter",
    "A": "🔥 Dope run",
    "B": "😐 Meh usable",
    "C": "🐌 Laggy vibes",
    "D": "🗑️ Trash mode",
    "F": "🗑️ Trash mode",
    "?": "🗑️ Trash mode",
}

# ── VRAM Overhead Factor ────────────────────────────────────────────────────
# Real-world VRAM usage is higher than theoretical due to KV cache,
# CUDA context, and OS overhead. We apply a 12% overhead.
# Decision: 1.12 is conservative — some setups see 15-20% overhead,
# but we prefer to underestimate rather than scare users away.
VRAM_OVERHEAD_FACTOR: float = 1.12

# ── Fit Status Normalization ────────────────────────────────────────────────
# Maps internal status strings to cleaner, normalized labels.
# Decision: We rename to verbs that describe the outcome, not the mechanism.
STATUS_NORMALIZATION: Dict[str, str] = {
    "can-run":      "runnable",
    "tight":        "runnable_tight",
    "can-run-slow": "degraded",
    "cannot-run":   "blocked",
    "unknown":      "unknown",
}

# Reverse mapping for display purposes
STATUS_DISPLAY: Dict[str, str] = {
    "runnable":       "✅ Runnable",
    "runnable_tight": "⚠️  Tight fit",
    "degraded":       "🐢 Degraded (CPU offload)",
    "blocked":        "🚫 Blocked",
    "unknown":        "❓ Unknown",
}

# ── Supported Quantization Levels ───────────────────────────────────────────
# These are the "currencies" of model compression.
# Decision: We support all 7 standard GGUF quant levels.
# Any quant not in this list is flagged as invalid during validation.
SUPPORTED_QUANTS: List[str] = [
    "Q2_K",
    "Q3_K_M",
    "Q4_K_M",
    "Q5_K_M",
    "Q6_K",
    "Q8_0",
    "F16",
]

# ── Score Boundaries ────────────────────────────────────────────────────────
# Valid score range for evaluation results.
SCORE_MIN: int = 0
SCORE_MAX: int = 100

# ── Vibe Level Score Ranges ─────────────────────────────────────────────────
# Maps score ranges to vibe levels for metrics grouping.
VIBE_SCORE_RANGES: Dict[str, tuple] = {
    "🧈 Smooth as butter": (85, 100),
    "🔥 Dope run":         (70, 84),
    "😐 Meh usable":       (55, 69),
    "🐌 Laggy vibes":      (40, 54),
    "🗑️ Trash mode":      (0, 39),
}

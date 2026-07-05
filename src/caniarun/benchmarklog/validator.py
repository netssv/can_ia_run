"""
Validator module — checks each NormalizedEvaluation for completeness and
data integrity.

STUDENT DECISIONS on what counts as invalid:
- Missing or zero VRAM → invalid (a model must have a size)
- Unknown quant level → invalid (not in our supported list)
- Score outside 0-100 → invalid (evaluation math went wrong)
- Unknown fit status → invalid (hardware detection failed)
- Missing model name or source → invalid (catalog corruption)
- Negative tok/s → invalid (estimation error)

Invalid records are NOT discarded. They stay in the dataset with
is_valid=False and reasons stored in validation_errors.
"""

from typing import List

from .normalizer import NormalizedEvaluation
from .rules import SUPPORTED_QUANTS, SCORE_MIN, SCORE_MAX, STATUS_NORMALIZATION


def validate_single(record: NormalizedEvaluation) -> NormalizedEvaluation:
    """
    Run all validation checks on a single record.
    Mutates is_valid and validation_errors in place, then returns it.
    """
    errors: List[str] = []

    # 1. VRAM must be positive
    if record.vram_required_gb is None or record.vram_required_gb <= 0:
        errors.append("VRAM required is missing or zero")

    # 2. Quant level must be recognized
    if record.quant_level not in SUPPORTED_QUANTS:
        errors.append(f"Unknown quant level: {record.quant_level}")

    # 3. Score must be within valid range
    if record.score < SCORE_MIN or record.score > SCORE_MAX:
        errors.append(f"Score {record.score} outside valid range [{SCORE_MIN}-{SCORE_MAX}]")

    # 4. Fit status must be recognized
    valid_statuses = set(STATUS_NORMALIZATION.values())
    if record.fit_status not in valid_statuses:
        errors.append(f"Unknown fit status: {record.fit_status}")

    # 5. Model name and source must exist
    if not record.model_name or not record.model_name.strip():
        errors.append("Missing model name")
    if not record.source or not record.source.strip():
        errors.append("Missing source/family")

    # 6. Tokens per second must not be negative (None is acceptable)
    if record.toks_per_sec is not None and record.toks_per_sec < 0:
        errors.append(f"Negative tok/s: {record.toks_per_sec}")

    # Apply results
    record.validation_errors = errors
    record.is_valid = len(errors) == 0

    return record


def validate_all(records: List[NormalizedEvaluation]) -> List[NormalizedEvaluation]:
    """
    Validate every record in the list. Returns the same list with
    is_valid and validation_errors populated.
    """
    for record in records:
        validate_single(record)
    return records

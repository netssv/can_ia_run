"""
gpu_db.py  –  Public GPU/Apple database API.

Data is kept in gpu_data/ sub-modules (split by vendor).
This module merges them into the GPU_DB and APPLE_DB dicts that the
rest of the codebase already imports, preserving full backward compatibility.
"""
# Re-export the dataclasses from gpu_specs so existing `from .gpu_db import GPUSpec` imports keep working
from .gpu_specs import GPUSpec, AppleSpec  # noqa: F401


def _build_gpu_db() -> dict[str, GPUSpec]:
    from .gpu_data.nvidia import NVIDIA_GPUS
    from .gpu_data.nvidia_pro import NVIDIA_PRO_GPUS
    from .gpu_data.other import AMD_GPUS, INTEL_GPUS
    db: dict[str, GPUSpec] = {}
    db.update(NVIDIA_GPUS)
    db.update(NVIDIA_PRO_GPUS)
    db.update(AMD_GPUS)
    db.update(INTEL_GPUS)
    return db


def _build_apple_db() -> dict[str, AppleSpec]:
    from .gpu_data.other import APPLE_SILICON
    return dict(APPLE_SILICON)


GPU_DB: dict[str, GPUSpec] = _build_gpu_db()
APPLE_DB: dict[str, AppleSpec] = _build_apple_db()


def match_gpu(renderer: str) -> tuple[str, GPUSpec] | None:
    """Return the best-matching (name, GPUSpec) from GPU_DB, or None."""
    upper = renderer.upper().replace("(TM)", "").strip()
    upper = " ".join(upper.split())  # collapse whitespace
    best_match = None
    best_len = 0

    for name, spec in GPU_DB.items():
        if name.upper() in upper and len(name) > best_len:
            best_match = (name, spec)
            best_len = len(name)

    return best_match

"""Shared GPU spec dataclasses used by both gpu_db.py and gpu_data/ sub-modules."""
from dataclasses import dataclass


@dataclass(frozen=True)
class GPUSpec:
    vram: float
    bw: float
    cores: int


@dataclass(frozen=True)
class AppleSpec:
    ram: float
    bw: float
    cpu_cores: int
    gpu_cores: int

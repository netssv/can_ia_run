from dataclasses import dataclass
from typing import Optional, List, Dict, Any

@dataclass(frozen=True)
class Quantization:
    name: str
    bits: int
    vram_gb: float
    disk_gb: float
    quality: str

@dataclass(frozen=True)
class AIModel:
    id: str
    name: str
    provider: str
    family: str
    params: str
    params_billions: float
    architecture: str
    context_length: int
    use_case: List[str]
    description: str
    min_ram_gb: float
    recommended_ram_gb: float
    quants: List[Quantization]
    active_params: Optional[str] = None
    moe_info: Optional[Dict[str, Any]] = None
    ollama_id: Optional[str] = None
    featured: bool = False
    license: Optional[str] = None

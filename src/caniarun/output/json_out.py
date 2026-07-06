import json
from typing import List, Dict, Any

from ..hardware import HardwareInfo
from ..compat import ModelResult

def render_json(hw: HardwareInfo, results: List[ModelResult]) -> None:
    data: Dict[str, Any] = {
        "hardware": {
            "gpu_name": hw.gpu_name,
            "gpu_vendor": hw.gpu_vendor,
            "vram_gb": hw.vram_gb,
            "system_ram_gb": hw.system_ram_gb,
            "memory_bandwidth": hw.memory_bandwidth,
            "is_apple_silicon": hw.is_apple_silicon,
            "platform": hw.platform
        },
        "models": []
    }
    
    for r in results:
        model_data = {
            "id": r.model.id,
            "name": r.model.name,
            "params": r.model.params,
            "quants": {}
        }
        for q in r.quants:
            model_data["quants"][q.quant_name] = {
                "grade": q.grade,
                "score": q.score,
                "toks_per_sec": q.toks_per_sec,
                "vram_gb": q.vram_gb
            }
        data["models"].append(model_data)
        
    print(json.dumps(data, indent=2))

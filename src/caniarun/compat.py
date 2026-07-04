from typing import Literal, Optional, List
import math
from dataclasses import dataclass

from .hardware import HardwareInfo
from .models import AIModel, MODELS, Quantization

ModelStatus = Literal["can-run", "tight", "can-run-slow", "cannot-run", "unknown"]
Grade = Literal["S", "A", "B", "C", "D", "F", "?"]

SYSTEM_RAM_BW_GBS = 50.0

@dataclass
class QuantResult:
    quant_name: str
    grade: Grade
    score: int
    status: ModelStatus
    toks_per_sec: Optional[float]
    vram_gb: float

@dataclass
class ModelResult:
    model: AIModel
    quants: List[QuantResult]
    best_grade: Grade

def evaluate_model(vram_needed: float, hw: HardwareInfo) -> ModelStatus:
    if hw.is_apple_silicon and hw.total_usable_ram:
        usable = hw.total_usable_ram * 0.75
        if vram_needed <= usable * 0.7: return "can-run"
        if vram_needed <= usable:       return "tight"
        return "cannot-run"
        
    if hw.vram_gb:
        if vram_needed <= hw.vram_gb * 0.85: return "can-run"
        if vram_needed <= hw.vram_gb * 1.1:  return "tight"
        # CPU offloading check
        if hw.system_ram_gb and hw.system_ram_gb > hw.vram_gb:
            usable_ram = hw.system_ram_gb * 0.70
            total_offload = hw.vram_gb + usable_ram
            if vram_needed <= total_offload: return "can-run-slow"
        return "cannot-run"
        
    if hw.total_usable_ram:
        usable = hw.total_usable_ram * 0.7
        if vram_needed <= usable * 0.7: return "can-run"
        if vram_needed <= usable:       return "tight"
        return "cannot-run"
        
    return "unknown"

def estimate_tokens_per_second(model_vram: float, hw: HardwareInfo) -> Optional[float]:
    if not hw.memory_bandwidth:
        return None
        
    efficiency = 0.65 if hw.is_apple_silicon else 0.70
    
    # Offloading
    if hw.vram_gb and model_vram > hw.vram_gb and hw.system_ram_gb:
        fraction_vram = min(1.0, hw.vram_gb / model_vram)
        fraction_ram = 1.0 - fraction_vram
        effective_bw = 1.0 / (fraction_vram / hw.memory_bandwidth + fraction_ram / SYSTEM_RAM_BW_GBS)
        toks = (effective_bw / model_vram) * efficiency * 0.85 # PCIe penalty
        return max(1.0, round(toks))
        
    toks = (hw.memory_bandwidth / model_vram) * efficiency
    return round(toks)

def memory_percentage(vram_needed: float, hw: HardwareInfo) -> Optional[float]:
    if hw.is_apple_silicon:
        if not hw.total_usable_ram: return None
        return round((vram_needed / hw.total_usable_ram) * 100)
        
    vram = hw.vram_gb or hw.total_usable_ram
    if not vram: return None
    return round((vram_needed / vram) * 100)

def _lerp(x: float, x0: float, x1: float, y0: float, y1: float) -> float:
    return y0 + (y1 - y0) * ((x - x0) / (x1 - x0))

def compute_score(status: ModelStatus, toks_per_sec: Optional[float], params_billions: float, mem_pct: Optional[float] = None) -> int:
    if status in ("cannot-run", "unknown"):
        return 0
        
    speed_score = 0.0
    if toks_per_sec is not None:
        if toks_per_sec >= 80: speed_score = 100
        elif toks_per_sec >= 40: speed_score = _lerp(toks_per_sec, 40, 80, 80, 100)
        elif toks_per_sec >= 20: speed_score = _lerp(toks_per_sec, 20, 40, 55, 80)
        elif toks_per_sec >= 10: speed_score = _lerp(toks_per_sec, 10, 20, 35, 55)
        elif toks_per_sec >= 5: speed_score = _lerp(toks_per_sec, 5, 10, 15, 35)
        else: speed_score = _lerp(max(toks_per_sec, 0), 0, 5, 0, 15)
    else:
        speed_score = 45 if status == "can-run" else 20
        
    headroom_score = 45.0
    if mem_pct is not None:
        if mem_pct <= 20: headroom_score = 100
        elif mem_pct <= 40: headroom_score = _lerp(mem_pct, 20, 40, 100, 75)
        elif mem_pct <= 60: headroom_score = _lerp(mem_pct, 40, 60, 75, 45)
        elif mem_pct <= 80: headroom_score = _lerp(mem_pct, 60, 80, 45, 20)
        else: headroom_score = _lerp(min(mem_pct, 100), 80, 100, 20, 0)
        
    quality_bonus = min(12.0, math.log2(params_billions + 1) * 2)
    fit_multiplier = 0.60 if status == "can-run-slow" else 0.75 if status == "tight" else 1.0
    
    return round((speed_score * 0.55 + headroom_score * 0.35 + quality_bonus) * fit_multiplier)

def score_to_grade(score: int, status: ModelStatus) -> Grade:
    if status == "cannot-run": return "F"
    if status == "unknown": return "?"
    if status == "can-run-slow":
        return "C" if score >= 40 else "D"
    if score >= 85: return "S"
    if score >= 70: return "A"
    if score >= 55: return "B"
    if score >= 40: return "C"
    if score >= 20: return "D"
    return "F"

def _grade_value(g: Grade) -> int:
    mapping = {"S": 6, "A": 5, "B": 4, "C": 3, "D": 2, "F": 1, "?": 0}
    return mapping.get(g, 0)

def evaluate_all(hw: HardwareInfo) -> List[ModelResult]:
    results = []
    
    for model in MODELS:
        quant_results = []
        best_g: Grade = "F"
        
        for q in model.quants:
            status = evaluate_model(q.vram_gb, hw)
            toks = estimate_tokens_per_second(q.vram_gb, hw)
            mem_pct = memory_percentage(q.vram_gb, hw)
            score = compute_score(status, toks, model.params_billions, mem_pct)
            grade = score_to_grade(score, status)
            
            if _grade_value(grade) > _grade_value(best_g):
                best_g = grade
                
            quant_results.append(QuantResult(
                quant_name=q.name,
                grade=grade,
                score=score,
                status=status,
                toks_per_sec=toks,
                vram_gb=q.vram_gb
            ))
            
        results.append(ModelResult(
            model=model,
            quants=quant_results,
            best_grade=best_g
        ))
        
    return results

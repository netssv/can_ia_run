import datetime
import os
from typing import List

from .hardware import HardwareInfo
from .compat import ModelResult, Grade

# Mappings from grade to the requested performance level string
GRADE_TO_LEVEL = {
    "S": "🧈 Smooth as butter",
    "A": "🔥 Dope run",
    "B": "😐 Meh usable",
    "C": "🐌 Laggy vibes",
    "D": "🗑️ Trash mode",
    "F": "🗑️ Trash mode",
    "?": "🗑️ Trash mode"
}

def generate_log_line(model_name: str, quant_name: str, vram_gb: float, toks: float, score: int, grade: Grade, hw: HardwareInfo, status: str) -> str:
    """Generate a single formatted log line for a specific model quant."""
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    perf_level = GRADE_TO_LEVEL.get(grade, "🗑️ Trash mode")
    
    base_msg = f"{model_name} @ {quant_name} — {vram_gb:.1f} GB VRAM, ~{toks if toks else 0:.0f} tok/s, score {score}"
    
    issues = []
    
    # 1. GPU Incompatible: No dedicated GPU (system RAM only)
    if hw.vram_gb is None and not hw.is_apple_silicon:
        issues.append("GPU incompatible")
        
    # 2. Crash Risk / Exceeds memory
    if status == "cannot-run":
        issues.append("exceeds all memory")
        
    # 3. CPU Offloading
    if status == "can-run-slow":
        issues.append("CPU offloading")
        
    # 4. RAM Tight: Model uses >80% of available memory (if it can run at all)
    if status in ("tight", "can-run-slow") or (hw.vram_gb and vram_gb > hw.vram_gb * 0.8):
        issues.append("RAM tight")
        
    # 5. Low bandwidth: speed is too slow
    if toks and toks < 10:
        issues.append("low bandwidth")
        
    issue_str = f", {', '.join(issues)}" if issues else ", no issues"
    
    return f"[{perf_level}] {now} {base_msg}{issue_str}"

def emit_log(hw: HardwareInfo, results: List[ModelResult], filepath: str = "caniarun.log", all_quants: bool = False):
    """Write the scan results to a log file."""
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    gpu_str = hw.gpu_name if hw.gpu_name else "No dedicated GPU detected"
    vram_str = f"{hw.vram_gb:.1f} GB" if hw.vram_gb else "N/A"
    ram_str = f"{hw.system_ram_gb:.1f} GB" if hw.system_ram_gb else "N/A"
    bw_str = f"{hw.memory_bandwidth:.0f} GB/s" if hw.memory_bandwidth else "N/A"
    
    lines = []
    lines.append(f"# caniarun scan — {now}")
    lines.append(f"# Hardware: {gpu_str} | VRAM: {vram_str} | RAM: {ram_str} | BW: {bw_str} | {hw.platform}")
    lines.append("")
    
    for res in results:
        quants_to_show = res.quants if all_quants else [q for q in res.quants if q.quant_name == "Q4_K_M"]
        if not quants_to_show and not all_quants and res.quants:
            # Fallback if Q4_K_M is somehow missing, just take the first one
            quants_to_show = [res.quants[0]]
            
        for q in quants_to_show:
            lines.append(generate_log_line(
                model_name=res.model.name,
                quant_name=q.quant_name,
                vram_gb=q.vram_gb,
                toks=q.toks_per_sec,
                score=q.score,
                grade=q.grade,
                hw=hw,
                status=q.status
            ))
            
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

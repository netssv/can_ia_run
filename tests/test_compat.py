import pytest
from caniarun.compat import evaluate_model, estimate_tokens_per_second, compute_score, score_to_grade, HardwareInfo

def test_evaluate_model():
    # Basic GPU
    hw = HardwareInfo("TestGPU", "Test", 8.0, 8.0, 16.0, 300.0, False, "Windows")
    assert evaluate_model(4.0, hw) == "can-run"
    assert evaluate_model(8.5, hw) == "tight"
    assert evaluate_model(12.0, hw) == "can-run-slow" # Offloading
    assert evaluate_model(30.0, hw) == "cannot-run"

    # Apple Silicon
    apple = HardwareInfo("M2 Max", "Apple", None, 32.0, 32.0, 400.0, True, "macOS")
    assert evaluate_model(10.0, apple) == "can-run"
    assert evaluate_model(20.0, apple) == "tight" # 32 * 0.75 = 24. 20 is > 24*0.7 (16.8) but <= 24
    assert evaluate_model(30.0, apple) == "cannot-run"

def test_estimate_tokens():
    # 8GB VRAM GPU with 300 GB/s bandwidth. Running a 4GB model
    hw = HardwareInfo("TestGPU", "Test", 8.0, 8.0, 16.0, 300.0, False, "Windows")
    toks = estimate_tokens_per_second(4.0, hw)
    # (300 / 4) * 0.7 = 75 * 0.7 = 52.5 -> 52 or 53
    assert 50 <= toks <= 55

def test_score_to_grade():
    assert score_to_grade(90, "can-run") == "S"
    assert score_to_grade(75, "can-run") == "A"
    assert score_to_grade(60, "can-run") == "B"
    assert score_to_grade(50, "can-run") == "C"
    assert score_to_grade(30, "can-run") == "D"
    
    # can-run-slow maxes out at C
    assert score_to_grade(90, "can-run-slow") == "C"
    assert score_to_grade(30, "can-run-slow") == "D"
    
    # cannot-run is always F
    assert score_to_grade(90, "cannot-run") == "F"

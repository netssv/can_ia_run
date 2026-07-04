import pytest
from caniarun.hardware import HardwareInfo, _estimate_bandwidth_heuristic
from caniarun.gpu_db import match_gpu

def test_heuristic_bandwidth():
    assert _estimate_bandwidth_heuristic("NVIDIA GeForce RTX 4090", 24, "Windows") == 700.0
    assert _estimate_bandwidth_heuristic("NVIDIA GeForce RTX 4060", 8, "Linux") == 300.0
    assert _estimate_bandwidth_heuristic("AMD Radeon RX 7900 XTX", 24, "Windows") == 500.0
    assert _estimate_bandwidth_heuristic("Intel UHD Graphics", None, "Windows") == 50.0

def test_match_gpu():
    # Longest match
    m1 = match_gpu("NVIDIA GeForce RTX 4090")
    assert m1 is not None
    assert m1[0] == "RTX 4090"
    
    m2 = match_gpu("AMD Radeon RX 7900 XTX")
    assert m2 is not None
    assert m2[0] == "RX 7900 XTX"
    
    m3 = match_gpu("Unknown SuperGPU")
    assert m3 is None

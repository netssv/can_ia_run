import pytest
from caniarun.models import MODELS

def test_models_exist():
    assert len(MODELS) > 50, "Should have loaded the models catalog"
    
def test_model_uniqueness():
    ids = [m.id for m in MODELS]
    assert len(ids) == len(set(ids)), "Model IDs should be unique"

def test_quants():
    # Find a model we know, like llama3.1-8b
    llama = next((m for m in MODELS if m.id == "llama3.1-8b"), None)
    assert llama is not None
    assert len(llama.quants) == 7
    
    # Q4_K_M for 8B should be around 5.0 GB
    q4 = next(q for q in llama.quants if q.name == "Q4_K_M")
    assert 4.5 <= q4.vram_gb <= 5.5
    
    # F16 for 8B should be around 16.5 - 18 GB
    f16 = next(q for q in llama.quants if q.name == "F16")
    assert 16.0 <= f16.vram_gb <= 18.0

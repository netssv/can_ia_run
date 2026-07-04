from .core import AIModel, Quantization

MODELS = [
    AIModel(
        id="smollm3-3b",
        name="SmolLM3 3B",
        provider="HuggingFace",
        family="SmolLM",
        params="3B",
        params_billions=3,
        architecture="dense",
        context_length=131072,
        use_case=['chat', 'reasoning'],
        description="Lightweight multilingual reasoning",
        min_ram_gb=1.7,
        recommended_ram_gb=2.8,
        quants=[
            Quantization(name="Q2_K", bits=2, vram_gb=1.5, disk_gb=0.9, quality="low"),
            Quantization(name="Q3_K_M", bits=3, vram_gb=1.8, disk_gb=1.3, quality="moderate"),
            Quantization(name="Q4_K_M", bits=4, vram_gb=2.0, disk_gb=1.5, quality="good"),
            Quantization(name="Q5_K_M", bits=5, vram_gb=2.4, disk_gb=1.8, quality="good"),
            Quantization(name="Q6_K", bits=6, vram_gb=2.8, disk_gb=2.2, quality="excellent"),
            Quantization(name="Q8_0", bits=8, vram_gb=3.6, disk_gb=2.9, quality="excellent"),
            Quantization(name="F16", bits=16, vram_gb=6.6, disk_gb=5.9, quality="lossless"),
        ],
        license="Apache 2.0",
    ),
]

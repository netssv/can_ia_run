from .core import AIModel, Quantization

MODELS = [
    AIModel(
        id="gemma4-31b",
        name="Gemma 4 31B",
        provider="Google",
        family="Gemma",
        params="33B",
        params_billions=33,
        architecture="dense",
        context_length=262144,
        use_case=['vision', 'reasoning'],
        description="Gemma 4 flagship base model (official)",
        min_ram_gb=18.4,
        recommended_ram_gb=30.7,
        quants=[
            Quantization(name="Q2_K", bits=2, vram_gb=11.1, disk_gb=10.1, quality="low"),
            Quantization(name="Q3_K_M", bits=3, vram_gb=15.3, disk_gb=14.1, quality="moderate"),
            Quantization(name="Q4_K_M", bits=4, vram_gb=17.4, disk_gb=16.1, quality="good"),
            Quantization(name="Q5_K_M", bits=5, vram_gb=21.6, disk_gb=20.2, quality="good"),
            Quantization(name="Q6_K", bits=6, vram_gb=25.9, disk_gb=24.2, quality="excellent"),
            Quantization(name="Q8_0", bits=8, vram_gb=34.3, disk_gb=32.3, quality="excellent"),
            Quantization(name="F16", bits=16, vram_gb=68.1, disk_gb=64.5, quality="lossless"),
        ],
        license="Gemma",
    ),
]

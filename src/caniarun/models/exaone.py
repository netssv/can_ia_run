from .core import AIModel, Quantization

MODELS = [
    AIModel(
        id="exaone-4-32b",
        name="EXAONE 4.0 32B",
        provider="LG AI",
        family="EXAONE",
        params="32B",
        params_billions=32,
        architecture="dense",
        context_length=131072,
        use_case=['chat', 'reasoning'],
        description="Hybrid reasoning, multilingual",
        min_ram_gb=17.9,
        recommended_ram_gb=29.8,
        quants=[
            Quantization(name="Q2_K", bits=2, vram_gb=10.7, disk_gb=9.8, quality="low"),
            Quantization(name="Q3_K_M", bits=3, vram_gb=14.8, disk_gb=13.7, quality="moderate"),
            Quantization(name="Q4_K_M", bits=4, vram_gb=16.9, disk_gb=15.6, quality="good"),
            Quantization(name="Q5_K_M", bits=5, vram_gb=21.0, disk_gb=19.6, quality="good"),
            Quantization(name="Q6_K", bits=6, vram_gb=25.1, disk_gb=23.5, quality="excellent"),
            Quantization(name="Q8_0", bits=8, vram_gb=33.3, disk_gb=31.3, quality="excellent"),
            Quantization(name="F16", bits=16, vram_gb=66.1, disk_gb=62.6, quality="lossless"),
        ],
        license="EXAONE AI",
    ),
]

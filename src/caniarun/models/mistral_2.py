from .core import AIModel, Quantization

MODELS = [
    AIModel(
        id="mixtral-8x22b",
        name="Mixtral 8x22B",
        provider="Mistral AI",
        family="Mistral",
        params="141B",
        params_billions=141,
        architecture="moe",
        context_length=65536,
        use_case=['chat', 'code', 'reasoning'],
        description="Large MoE with 39B active params",
        min_ram_gb=78.8,
        recommended_ram_gb=131.3,
        quants=[
            Quantization(name="Q2_K", bits=2, vram_gb=45.6, disk_gb=43.1, quality="low"),
            Quantization(name="Q3_K_M", bits=3, vram_gb=63.7, disk_gb=60.3, quality="moderate"),
            Quantization(name="Q4_K_M", bits=4, vram_gb=72.7, disk_gb=68.9, quality="good"),
            Quantization(name="Q5_K_M", bits=5, vram_gb=90.8, disk_gb=86.2, quality="good"),
            Quantization(name="Q6_K", bits=6, vram_gb=108.8, disk_gb=103.4, quality="excellent"),
            Quantization(name="Q8_0", bits=8, vram_gb=144.9, disk_gb=137.9, quality="excellent"),
            Quantization(name="F16", bits=16, vram_gb=289.4, disk_gb=275.8, quality="lossless"),
        ],
        active_params="39B active",
        moe_info={'numExperts': 8, 'activeExperts': 2, 'activeParameters': 39100000000},
        ollama_id="mixtral:8x22b",
        license="Apache 2.0",
    ),
]

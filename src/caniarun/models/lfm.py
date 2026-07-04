from .core import AIModel, Quantization

MODELS = [
    AIModel(
        id="lfm2-24b",
        name="LFM2 24B",
        provider="Liquid AI",
        family="LFM",
        params="24B",
        params_billions=24,
        architecture="moe",
        context_length=32768,
        use_case=['chat', 'edge', 'rag'],
        description="Hybrid MoE with convolution+attention layers — 2.3B active",
        min_ram_gb=13.4,
        recommended_ram_gb=22.4,
        quants=[
            Quantization(name="Q2_K", bits=2, vram_gb=8.2, disk_gb=7.3, quality="low"),
            Quantization(name="Q3_K_M", bits=3, vram_gb=11.3, disk_gb=10.3, quality="moderate"),
            Quantization(name="Q4_K_M", bits=4, vram_gb=12.8, disk_gb=11.7, quality="good"),
            Quantization(name="Q5_K_M", bits=5, vram_gb=15.9, disk_gb=14.7, quality="good"),
            Quantization(name="Q6_K", bits=6, vram_gb=18.9, disk_gb=17.6, quality="excellent"),
            Quantization(name="Q8_0", bits=8, vram_gb=25.1, disk_gb=23.5, quality="excellent"),
            Quantization(name="F16", bits=16, vram_gb=49.7, disk_gb=46.9, quality="lossless"),
        ],
        active_params="2.3B active",
        moe_info={'numExperts': 64, 'activeExperts': 4, 'activeParameters': 2300000000},
        ollama_id="lfm2:24b",
        license="Liquid AI",
    ),
]

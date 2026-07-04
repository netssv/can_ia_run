from .core import AIModel, Quantization

MODELS = [
    AIModel(
        id="kimi-k2",
        name="Kimi K2",
        provider="Moonshot AI",
        family="Kimi",
        params="1T",
        params_billions=1000,
        architecture="moe",
        context_length=131072,
        use_case=['chat', 'reasoning', 'code'],
        description="1T-param MoE with 384 experts — 32B active, strong agentic coding",
        min_ram_gb=558.8,
        recommended_ram_gb=931.3,
        quants=[
            Quantization(name="Q2_K", bits=2, vram_gb=320.6, disk_gb=305.6, quality="low"),
            Quantization(name="Q3_K_M", bits=3, vram_gb=448.7, disk_gb=427.8, quality="moderate"),
            Quantization(name="Q4_K_M", bits=4, vram_gb=512.7, disk_gb=488.9, quality="good"),
            Quantization(name="Q5_K_M", bits=5, vram_gb=640.8, disk_gb=611.2, quality="good"),
            Quantization(name="Q6_K", bits=6, vram_gb=768.8, disk_gb=733.4, quality="excellent"),
            Quantization(name="Q8_0", bits=8, vram_gb=1025.0, disk_gb=977.9, quality="excellent"),
            Quantization(name="F16", bits=16, vram_gb=2049.4, disk_gb=1955.8, quality="lossless"),
        ],
        active_params="32B active",
        moe_info={'numExperts': 384, 'activeExperts': 8, 'activeParameters': 32000000000},
        ollama_id="kimi-k2",
        featured=True,
        license="Kimi",
    ),
]

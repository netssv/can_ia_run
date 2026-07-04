from .core import AIModel, Quantization

MODELS = [
    AIModel(
        id="glm-4-9b",
        name="GLM-4 9B",
        provider="Zhipu AI",
        family="GLM",
        params="9B",
        params_billions=9,
        architecture="dense",
        context_length=131072,
        use_case=['chat', 'multilingual', 'code'],
        description="Multilingual model supporting 26 languages with 128K context",
        min_ram_gb=5.0,
        recommended_ram_gb=8.4,
        quants=[
            Quantization(name="Q2_K", bits=2, vram_gb=3.4, disk_gb=2.8, quality="low"),
            Quantization(name="Q3_K_M", bits=3, vram_gb=4.5, disk_gb=3.9, quality="moderate"),
            Quantization(name="Q4_K_M", bits=4, vram_gb=5.1, disk_gb=4.4, quality="good"),
            Quantization(name="Q5_K_M", bits=5, vram_gb=6.3, disk_gb=5.5, quality="good"),
            Quantization(name="Q6_K", bits=6, vram_gb=7.4, disk_gb=6.6, quality="excellent"),
            Quantization(name="Q8_0", bits=8, vram_gb=9.7, disk_gb=8.8, quality="excellent"),
            Quantization(name="F16", bits=16, vram_gb=18.9, disk_gb=17.6, quality="lossless"),
        ],
        ollama_id="glm4:9b",
        license="GLM-4",
    ),
]

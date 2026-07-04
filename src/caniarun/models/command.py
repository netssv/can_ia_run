from .core import AIModel, Quantization

MODELS = [
    AIModel(
        id="command-r-35b",
        name="Command R 35B",
        provider="Cohere",
        family="Command",
        params="35B",
        params_billions=35,
        architecture="dense",
        context_length=131072,
        use_case=['chat', 'rag'],
        description="Optimized for retrieval-augmented generation",
        min_ram_gb=19.6,
        recommended_ram_gb=32.6,
        quants=[
            Quantization(name="Q2_K", bits=2, vram_gb=11.7, disk_gb=10.7, quality="low"),
            Quantization(name="Q3_K_M", bits=3, vram_gb=16.2, disk_gb=15.0, quality="moderate"),
            Quantization(name="Q4_K_M", bits=4, vram_gb=18.4, disk_gb=17.1, quality="good"),
            Quantization(name="Q5_K_M", bits=5, vram_gb=22.9, disk_gb=21.4, quality="good"),
            Quantization(name="Q6_K", bits=6, vram_gb=27.4, disk_gb=25.7, quality="excellent"),
            Quantization(name="Q8_0", bits=8, vram_gb=36.4, disk_gb=34.2, quality="excellent"),
            Quantization(name="F16", bits=16, vram_gb=72.2, disk_gb=68.5, quality="lossless"),
        ],
        ollama_id="command-r:35b",
        license="CC BY-NC 4.0",
    ),
]

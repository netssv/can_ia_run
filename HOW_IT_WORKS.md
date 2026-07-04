# How `caniarun` Works

`caniarun` is a zero-configuration CLI tool that predicts how well a given Large Language Model (LLM) will run on your local hardware. It assigns a grade (from S to F) for each model across different quantization levels.

But how does it actually know if a model will run, and where does it get its data? 

---

## 1. Where the Data Comes From

The tool is completely offline and does not make any API calls. It relies on a rich, hardcoded catalog of models and GPUs built directly into its source code. 

### The Model Catalog (`src/caniarun/models.py`)
The tool ships with an internal database of **77 open-weights AI models** (like Llama 3, Qwen 2.5, DeepSeek R1, etc.). 
For each model, the database knows:
- **Parameter Count:** (e.g., 8 Billion, 70 Billion)
- **Architecture:** Dense or Mixture of Experts (MoE)

From the parameter count, `caniarun` mathematically calculates the exact RAM/VRAM required for **7 different quantization levels** (Q2_K, Q3_K_M, Q4_K_M, Q5_K_M, Q6_K, Q8_0, and F16). 
- *Example:* A 7B parameter model in F16 (16-bit float) takes about 14GB of RAM. But in Q4 (4-bit quantization), it only requires about 4.3GB of RAM.

### The GPU Database (`src/caniarun/gpu_db.py`)
To know the performance characteristics of your hardware, the tool contains a database of over **200 specific GPUs** (NVIDIA, AMD, Intel) and **18 Apple Silicon chips**.
For each chip, it stores:
- **Dedicated VRAM** (e.g., 24 GB for an RTX 4090)
- **Memory Bandwidth** (e.g., 1008 GB/s for an RTX 4090, or 100 GB/s for an M2 chip)

---

## 2. How it Detects Your Hardware

When you run the tool, the hardware detection module (`src/caniarun/hardware.py`) uses a "waterfall" approach to figure out what computer you are using across Windows, macOS, and Linux:

1. **NVIDIA GPUs (Cross-platform):** It first tries to use the `pynvml` Python library to communicate directly with NVIDIA drivers. If that fails, it tries to run the `nvidia-smi` command-line utility to extract the GPU name and VRAM.
2. **Apple Silicon (macOS):** It uses macOS's native `sysctl` command to read the exact chip brand (e.g., "Apple M4 Max") and the total unified memory installed.
3. **AMD / Intel (Linux/Windows):** It falls back to reading PCI devices (using `lspci` on Linux) to find AMD Radeon or Intel Arc graphics cards.
4. **System RAM:** Finally, it uses the `psutil` library to measure your total system RAM.

Once it has a string like `"NVIDIA GeForce RTX 4090"`, it does a fuzzy search against its internal `GPU_DB` to fetch the **Memory Bandwidth** and **VRAM** limits for your exact card.

---

## 3. How it Grades Compatibility (The Math)

With your hardware specs and the model requirements in hand, the compatibility engine (`src/caniarun/compat.py`) evaluates the fit.

### Step A: Does it fit in memory? (Status)
The engine checks if the model's required VRAM fits into your hardware:
- **`can-run`**: The model fits comfortably in your VRAM (or Apple Unified Memory).
- **`tight`**: The model barely fits (leaves less than 15% headroom).
- **`can-run-slow`**: The model is larger than your GPU's VRAM, but fits if we split it between your GPU and System RAM (CPU offloading).
- **`cannot-run`**: The model is too big for your entire machine.

### Step B: How fast will it be? (Tokens per Second)
LLM inference speed is almost entirely bound by **Memory Bandwidth**. 
The tool estimates generation speed (Tokens/sec) using the formula:
```
Tokens/sec = (Hardware Bandwidth GB/s ÷ Model VRAM Size GB) × Efficiency Factor
```
*(Efficiency is generally ~70% for discrete GPUs, and drops drastically if the model is offloaded to the CPU).*

### Step C: The Final Score (0-100)
The tool calculates a final score based on a weighted average of:
1. **Speed (55%):** How many tokens per second you'll get.
2. **Headroom (35%):** How much VRAM is left over for context length and OS tasks.
3. **Quality Bonus:** A slight bump for larger, smarter models.
4. **Fit Penalty:** A massive penalty if the model has to offload to system RAM (`can-run-slow`).

### Step D: The Grade (S to F)
Finally, that 0-100 score is translated into a human-readable tier:
- **S (85-100)**: Lightning fast, fits perfectly.
- **A (70-84)**: Runs very well.
- **B (55-69)**: Decent, usable experience.
- **C (40-54)**: Tight fit or slight offloading. 
- **D (20-39)**: Heavy offloading, barely readable speed.
- **F (0-19)**: Too heavy, system will likely crash or freeze.

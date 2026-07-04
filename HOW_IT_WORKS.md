# How `caniarun` Actually Works 🤓

`caniarun` is a zero-configuration CLI tool that predicts how well a given Large Language Model (LLM) will run on your local hardware. Instead of boring metrics, it assigns a fun, slang-filled vibe check (like "Smooth as butter" or "Trash mode") for each model across different compression levels.

But how does it actually know if a model will run, and where does it get its data? Let's break it down.

---

## 1. Where Does It Get Its Data?

The tool is completely offline and does not make any API calls. It relies on a rich, hardcoded catalog of models and GPUs built directly into its source code. 

### The Model Catalog (`src/caniarun/models/`)
The tool ships with an internal database of **over 80 open-weights AI models** (like Llama 3, Qwen 2.5, DeepSeek R1, etc.). 
For each model, the database knows:
- **Parameter Count:** (e.g., 8 Billion, 70 Billion)
- **Architecture:** Dense or Mixture of Experts (MoE)

Using just the parameter count, `caniarun` mathematically calculates the exact RAM/VRAM required for **7 different quantization levels** (Q2_K, Q3_K_M, Q4_K_M, Q5_K_M, Q6_K, Q8_0, and F16). 
*For context:* A 7B parameter model in F16 (16-bit float) takes about 14GB of RAM. But in Q4 (4-bit quantization), it only requires about 4.3GB of RAM.

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

### Step A: Does it even fit? (The Status)
First, we check if the model fits in your memory:
- **`can-run`**: Fits perfectly in your VRAM (or Apple Unified Memory).
- **`tight`**: Barely fits (you have less than 15% breathing room).
- **`can-run-slow`**: Too big for the GPU, so we have to split the load with your System RAM (CPU offloading). Expect a slowdown!
- **`cannot-run`**: It's just too big for your entire machine. Don't even try.

### Step B: How fast will it be? (Tokens/sec)
AI speed is almost entirely limited by **Memory Bandwidth**. 
We estimate your generation speed using this formula:
```
Tokens/sec = (Hardware Bandwidth GB/s ÷ Model VRAM Size GB) × Efficiency
```
*(Fun fact: Efficiency is usually around 70% for standard GPUs, but it tanks hard if you have to offload to your CPU).*

### Step C: The Final Score (0-100)
We mash everything together into a final score, weighted like this:
1. **Speed (55%):** Because waiting for text generation sucks.
2. **Headroom (35%):** So you have VRAM left over for your OS or large context windows.
3. **Quality Bonus:** A little bump if the model is larger/smarter.
4. **Fit Penalty:** A massive drop if the model spills over into system RAM (`can-run-slow`).

### Step D: The Vibe Check
Finally, that 0-100 score gets translated into a slang vibe level you can actually understand:
- **🧈 Smooth as butter (85-100)**: Lightning fast, fits perfectly.
- **🔥 Dope run (70-84)**: Runs great, no complaints.
- **😐 Meh usable (55-69)**: It works, but it's not breaking any speed records.
- **🐌 Laggy vibes (40-54)**: Tight fit or slight offloading. It'll test your patience.
- **🗑️ Trash mode (0-39)**: Heavy offloading or crashes. Just don't.

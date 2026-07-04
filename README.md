```text
   _____                       _                 
  / ____|                     (_)                
 | |     __ _ _ __   __ _ _ __ _ _   _ _ __ ___  
 | |    / _` | '_ \ / _` | '__| | | | | '_ ` _ \ 
 | |___| (_| | | | | (_| | |  | | |_| | | | | | |
  \_____\__,_|_| |_|\__,_|_|  |_|\__,_|_| |_| |_|
```
# caniarun 🚀

Not sure if your rig can handle that shiny new AI model? That's exactly what this tool is for!

`caniarun` checks out your hardware (GPU, CPU, and RAM) and tells you straight up which open-source AI models will actually run on your machine. Instead of throwing confusing metrics at you, it gives you a fun, easy-to-understand vibe check for over 80 models across different compression levels.

You'll get ratings like:
- 🧈 Smooth as butter
- 🔥 Dope run
- 😐 Meh usable
- 🐌 Laggy vibes
- 🗑️ Trash mode

It's basically the terminal version of [canirun.ai](https://canirun.ai).

## Installation

Getting started is super easy. Just drop this in your terminal:

```bash
pip install caniarun
```

*(Optional)* If you're rocking an NVIDIA GPU and want more precise detection, use this instead:
```bash
pip install caniarun[nvidia]
```

## How to Use

Just type this in and hit enter. We'll handle the rest!

```bash
caniarun
```

---
🌟 **Check out the source code & contribute:**  
[github.com/netssv/can_ia_run](https://github.com/netssv/can_ia_run)

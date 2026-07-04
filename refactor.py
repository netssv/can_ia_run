import os
import ast
import shutil

src_file = "src/caniarun/models.py"
dest_dir = "src/caniarun/models_pkg" # We will rename this to models later

os.makedirs(dest_dir, exist_ok=True)

with open(src_file, "r") as f:
    source_lines = f.readlines()
    
with open(src_file, "r") as f:
    source = f.read()

tree = ast.parse(source)

# 1. Write core.py
core_lines = [
    "from dataclasses import dataclass\n",
    "from typing import Optional, List, Dict, Any\n",
    "\n",
    "@dataclass(frozen=True)\n",
    "class Quantization:\n",
    "    name: str\n",
    "    bits: int\n",
    "    vram_gb: float\n",
    "    disk_gb: float\n",
    "    quality: str\n",
    "\n",
    "@dataclass(frozen=True)\n",
    "class AIModel:\n",
    "    id: str\n",
    "    name: str\n",
    "    provider: str\n",
    "    family: str\n",
    "    params: str\n",
    "    params_billions: float\n",
    "    architecture: str\n",
    "    context_length: int\n",
    "    use_case: List[str]\n",
    "    description: str\n",
    "    min_ram_gb: float\n",
    "    recommended_ram_gb: float\n",
    "    quants: List[Quantization]\n",
    "    active_params: Optional[str] = None\n",
    "    moe_info: Optional[Dict[str, Any]] = None\n",
    "    ollama_id: Optional[str] = None\n",
    "    featured: bool = False\n",
    "    license: Optional[str] = None\n",
]

with open(f"{dest_dir}/core.py", "w") as f:
    f.writelines(core_lines)

# 2. Extract models
models = []
for node in tree.body:
    is_models = False
    elements = None
    if isinstance(node, ast.Assign) and len(node.targets) == 1 and getattr(node.targets[0], 'id', '') == 'MODELS':
        is_models = True
        elements = node.value.elts
    elif isinstance(node, ast.AnnAssign) and getattr(node.target, 'id', '') == 'MODELS':
        is_models = True
        elements = node.value.elts

    if is_models:
        for el in elements:
            family = "Other"
            for kw in el.keywords:
                if kw.arg == 'family':
                    family = kw.value.value
            
            # extract exact string from source_lines
            start = el.lineno - 1
            end = el.end_lineno
            model_str = "".join(source_lines[start:end])
            models.append((family, model_str))

# Group by family
from collections import defaultdict
families = defaultdict(list)
for family, mstr in models:
    # Sanitize family name for python module
    mod_name = family.lower().replace(" ", "_").replace("-", "_")
    families[mod_name].append(mstr)

# Write families to files
# If a family is too large (like Llama might be > 200 lines, we chunk it)
# Each model is approx 20 lines. So 8 models per file = ~160 lines.
MAX_MODELS_PER_FILE = 7

all_modules = []

for mod_name, mod_models in families.items():
    chunks = [mod_models[i:i + MAX_MODELS_PER_FILE] for i in range(0, len(mod_models), MAX_MODELS_PER_FILE)]
    for idx, chunk in enumerate(chunks):
        suffix = f"_{idx+1}" if len(chunks) > 1 else ""
        file_name = f"{mod_name}{suffix}.py"
        all_modules.append((file_name, chunk))
        
        with open(f"{dest_dir}/{file_name}", "w") as f:
            f.write("from .core import AIModel, Quantization\n\n")
            f.write("MODELS = [\n")
            for m in chunk:
                # Add indentation if necessary, but the source probably already has it.
                # Actually, the AST gives us exact lines, which are indented.
                f.write(m + ",\n")
            f.write("]\n")

# 3. Write __init__.py
with open(f"{dest_dir}/__init__.py", "w") as f:
    f.write("from .core import AIModel, Quantization\n")
    for file_name, _ in all_modules:
        mod = file_name.replace('.py', '')
        f.write(f"from .{mod} import MODELS as {mod}_models\n")
    f.write("\nMODELS = (\n")
    for file_name, _ in all_modules:
        mod = file_name.replace('.py', '')
        f.write(f"    {mod}_models +\n")
    f.write("    []\n)\n")

print(f"Refactoring complete into {dest_dir}. Found {len(all_modules)} files + core.py")

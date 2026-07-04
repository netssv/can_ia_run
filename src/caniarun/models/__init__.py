from .core import AIModel, Quantization
from .qwen_1 import MODELS as qwen_1_models
from .qwen_2 import MODELS as qwen_2_models
from .qwen_3 import MODELS as qwen_3_models
from .qwen_4 import MODELS as qwen_4_models
from .llama_1 import MODELS as llama_1_models
from .llama_2 import MODELS as llama_2_models
from .gemma_1 import MODELS as gemma_1_models
from .gemma_2 import MODELS as gemma_2_models
from .gemma_3 import MODELS as gemma_3_models
from .deepseek import MODELS as deepseek_models
from .smollm import MODELS as smollm_models
from .phi import MODELS as phi_models
from .mistral_1 import MODELS as mistral_1_models
from .mistral_2 import MODELS as mistral_2_models
from .glm import MODELS as glm_models
from .nemotron import MODELS as nemotron_models
from .gpt_oss import MODELS as gpt_oss_models
from .lfm import MODELS as lfm_models
from .exaone import MODELS as exaone_models
from .olmo import MODELS as olmo_models
from .command import MODELS as command_models
from .kimi import MODELS as kimi_models

MODELS = (
    qwen_1_models +
    qwen_2_models +
    qwen_3_models +
    qwen_4_models +
    llama_1_models +
    llama_2_models +
    gemma_1_models +
    gemma_2_models +
    gemma_3_models +
    deepseek_models +
    smollm_models +
    phi_models +
    mistral_1_models +
    mistral_2_models +
    glm_models +
    nemotron_models +
    gpt_oss_models +
    lfm_models +
    exaone_models +
    olmo_models +
    command_models +
    kimi_models +
    []
)

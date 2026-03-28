from enum import Enum

class llm(Enum):
    MISTRAL = "codestral:latest"
    GEMMA = "gemma3n:latest"
    LLAMA = "llama3.1:latest"
    QWEN = "qwen2.5-coder:latest"
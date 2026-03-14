from enum import Enum

class llm(Enum):
    
    GEMINI = "gemini-3-flash-preview"
    GEMMA = "gemma3n:latest"
    LLAMA = "compcj/llama4-scout-ud-q2-k-xl:latest"
    DEEPSEEK = "deepseek-v3.2:cloud"
from enum import Enum

class llm(Enum):
    
    GEMINI = "gemini-3-flash-preview"
    DEEPSEEK = "deepseek-v3.2:cloud"
    GPT = "gpt-oss-safeguard:latest"
    LLAMA = "compcj/llama4-scout-ud-q2-k-xl:latest"
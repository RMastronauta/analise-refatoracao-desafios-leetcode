from enum import Enum

class TipoCodigo(Enum):
    BASELINE = "baseline"
    REFATORADO = "refatorado"
    REFATORADO_SIMPLIFICADO = "refatorado_simplificado"
    BASELINE_SIMPLIFICADO = "baseline_simplificado"
    REFATORADO_ORIGEM_SIMPLIFICADO = "refatorado_origem_simplificado"
    REFATORADO_SIMPLIFICADO_ORIGEM_SIMPLIFICADO = "refatorado_simplificado_origem_simplificado"

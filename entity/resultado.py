class Resultado:
    def __init__(self, id_desafio, id_modelo, tipo, codigo_fonte, linguagem, id_resultado_origem = None):
        self.id_desafio = id_desafio
        self.id_modelo = id_modelo
        self.tipo = tipo
        self.codigo_fonte = codigo_fonte
        self.linguagem = linguagem
        self.id_resultado_origem = id_resultado_origem
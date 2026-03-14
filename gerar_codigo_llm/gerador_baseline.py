import os
import sys
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if root_path not in sys.path:
    sys.path.append(root_path)

from entity.resultado import Resultado
from enums.lingagem import Linguagem
from enums.tipo_codigo import TipoCodigo
from gerar_codigo_llm.gerador_codigo_llm import gerador_codigo_llm
from repository.repository import Repository

class Gerador_Baseline:
    def __init__(self):
        self.llm_request = Repository()
        self.gerador_codigo_llm = gerador_codigo_llm()
        self.resultados_processados = list[Resultado]()
        
    def processar_desafios(self):
        try:
            desafios = self.llm_request.select_into_table(table_name= "desafios", campos=["id_desafio", "enunciado AS descricao"], size=2)
            modelos = self.llm_request.select_into_table(table_name = "modelos", campos=["id_modelo", "nome_modelo"], size=4)

            for desafio in desafios:
                prompt_python = self.gerador_codigo_llm.GetPrompt(desafio['descricao'], TipoCodigo.BASELINE, Linguagem.PYTHON.value)
                prompt_java = self.gerador_codigo_llm.GetPrompt(desafio['descricao'], TipoCodigo.BASELINE, Linguagem.JAVA.value)
                for modelo in modelos:

                    modelo_processado_python = self.gerador_codigo_llm.ModeloJaProcessado(desafio['id_desafio'], modelo['id_modelo'], TipoCodigo.BASELINE.value, Linguagem.PYTHON.value)
                    modelo_processado_java = self.gerador_codigo_llm.ModeloJaProcessado(desafio['id_desafio'], modelo['id_modelo'], TipoCodigo.BASELINE.value, Linguagem.JAVA.value)
                    if(modelo_processado_python and modelo_processado_java):
                        print(f"Desafio {desafio['id_desafio']} já processado com {modelo['nome_modelo']} para o tipo de código {TipoCodigo.BASELINE.value}. Pulando...")
                        continue

                    try:
                        if not modelo_processado_python:
                            print(f"Processando Desafio {desafio['id_desafio']} com {modelo['nome_modelo']}, para a linguagem {Linguagem.PYTHON.value}...")
                            codigo_Python_gerado = self.gerador_codigo_llm.solicitar_codigo_llm(modelo['nome_modelo'], prompt_python, Linguagem.PYTHON.value)
                            novo_resultado = Resultado(
                                id_desafio=desafio['id_desafio'],
                                id_modelo=modelo['id_modelo'],
                                tipo=TipoCodigo.BASELINE.value,
                                codigo_fonte=codigo_Python_gerado,
                                linguagem=Linguagem.PYTHON.value
                            )
                            self.resultados_processados.append(novo_resultado)
                        if not modelo_processado_java:
                            print(f"Processando Desafio {desafio['id_desafio']} com {modelo['nome_modelo']}, para a linguagem {Linguagem.JAVA.value}...")
                            codigo_Java_gerado = self.gerador_codigo_llm.solicitar_codigo_llm(modelo['nome_modelo'], prompt_java, Linguagem.JAVA.value)
                            novo_resultado_java = Resultado(
                                id_desafio=desafio['id_desafio'],
                                id_modelo=modelo['id_modelo'],
                                tipo=TipoCodigo.BASELINE.value,
                                codigo_fonte=codigo_Java_gerado,
                                linguagem=Linguagem.JAVA.value
                            )
                            self.resultados_processados.append(novo_resultado_java)
                        
                    except Exception as e:
                        print(f"Falha crítica após retentativas no desafio {desafio['id_desafio']}: {e}")
            # Inserir os resultados processados no banco de dados
            if self.resultados_processados:
                self.llm_request.insert_resultados(self.resultados_processados)

        except Exception as e:
            print(f"Erro ao processar desafios: {e}")
        finally:
            self.llm_request.close_db_connection()
                    
    

if __name__ == "__main__":
    gerador = Gerador_Baseline()
    gerador.processar_desafios()
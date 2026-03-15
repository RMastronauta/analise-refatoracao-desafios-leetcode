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
import json

class Gerador_Baseline:
    def __init__(self):
        self.llm_request = Repository()
        self.gerador_codigo_llm = gerador_codigo_llm()
        self.resultados_processados = list[Resultado]()
        self.nome_arquivo_json = "resultado_baseline.json"
        
    def processar_desafios(self):
        try:
            desafios = self.llm_request.select_into_table(table_name="desafios", campos=["id_desafio", "enunciado AS descricao"], size=2)
            modelos = self.llm_request.select_into_table(table_name="modelos", campos=["id_modelo", "nome_modelo"], size=4)

            for desafio in desafios:
                prompt_python = self.gerador_codigo_llm.GetPrompt(desafio['descricao'], TipoCodigo.BASELINE, Linguagem.PYTHON.value)
                prompt_java = self.gerador_codigo_llm.GetPrompt(desafio['descricao'], TipoCodigo.BASELINE, Linguagem.JAVA.value)
                
                for modelo in modelos:
                    modelo_processado_python = self.gerador_codigo_llm.ModeloJaProcessado(desafio['id_desafio'], modelo['id_modelo'], TipoCodigo.BASELINE.value, Linguagem.PYTHON.value)
                    modelo_processado_java = self.gerador_codigo_llm.ModeloJaProcessado(desafio['id_desafio'], modelo['id_modelo'], TipoCodigo.BASELINE.value, Linguagem.JAVA.value)
                    
                    if modelo_processado_python and modelo_processado_java:
                        print(f"Desafio {desafio['id_desafio']} já processado. Pulando...")
                        continue

                    try:
                        resultados_acumulados = []
                        # Processamento Python
                        if not modelo_processado_python:
                            print(f"Processando {modelo['nome_modelo']} (Python)...")
                            codigo_py = self.gerador_codigo_llm.solicitar_codigo_llm(modelo['nome_modelo'], prompt_python, Linguagem.PYTHON.value)
                            resultados_acumulados.append(Resultado(
                                id_desafio=desafio['id_desafio'],
                                id_modelo=modelo['id_modelo'],
                                tipo=TipoCodigo.BASELINE.value,
                                codigo_fonte=codigo_py,
                                linguagem=Linguagem.PYTHON.value
                            ))

                        # Processamento Java
                        if not modelo_processado_java:
                            print(f"Processando {modelo['nome_modelo']} (Java)...")
                            codigo_java = self.gerador_codigo_llm.solicitar_codigo_llm(modelo['nome_modelo'], prompt_java, Linguagem.JAVA.value)
                            resultados_acumulados.append(Resultado(
                                id_desafio=desafio['id_desafio'],
                                id_modelo=modelo['id_modelo'],
                                tipo=TipoCodigo.BASELINE.value,
                                codigo_fonte=codigo_java,
                                linguagem=Linguagem.JAVA.value
                            ))

                        self.gerador_codigo_llm.escrever_resultados_em_json(resultados_acumulados, self.nome_arquivo_json)

                    except Exception as e:
                        print(f"Falha no modelo {modelo['nome_modelo']}: {e}")

            # Após processar todos os desafios e modelos, ler os resultados acumulados do arquivo JSON para garantir que a variável esteja definida
            self.gerador_codigo_llm.ler_resultados_processados_do_arquivo(self.nome_arquivo_json)
            
            # Persistência no Banco
            if self.resultados_processados:
                self.llm_request.insert_resultados(self.resultados_processados)
                print(f"Sucesso! {len(self.resultados_processados)} resultados inseridos.")

        except Exception as e:
            print(f"Erro geral: {e}")
        finally:
            self.llm_request.close_db_connection()
    

if __name__ == "__main__":
    gerador = Gerador_Baseline()
    gerador.processar_desafios()
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
            desafios = self.llm_request.select_into_table(table_name="desafios", campos=["id_desafio", "enunciado AS descricao"], size=1)
            modelos = self.llm_request.select_into_table(table_name="modelos", campos=["id_modelo", "nome_modelo"], size=4)

            for desafio in desafios:
                prompt_python = self.gerador_codigo_llm.GetPrompt(desafio['descricao'], TipoCodigo.BASELINE, Linguagem.PYTHON.value)
                prompt_java = self.gerador_codigo_llm.GetPrompt(desafio['descricao'], TipoCodigo.BASELINE, Linguagem.JAVA.value)
                
                for modelo in modelos:
                    if modelo['nome_modelo'] == "GEMINI":
                        print(f"Pulando modelo {modelo['nome_modelo']} para o desafio {desafio['id_desafio']}...")
                        continue
                    modelo_processado_python = self.gerador_codigo_llm.ModeloJaProcessado(desafio['id_desafio'], modelo['id_modelo'], TipoCodigo.BASELINE.value, Linguagem.PYTHON.value)
                    modelo_processado_java = self.gerador_codigo_llm.ModeloJaProcessado(desafio['id_desafio'], modelo['id_modelo'], TipoCodigo.BASELINE.value, Linguagem.JAVA.value)
                    
                    if modelo_processado_python and modelo_processado_java:
                        print(f"Desafio {desafio['id_desafio']} já processado. Pulando...")
                        continue

                    resultados_acumulados = self.gerador_codigo_llm.ler_resultados_processados_do_arquivo(self.nome_arquivo_json) or []
                    modelo_processado_python_Json = any(r.id_desafio == desafio['id_desafio'] and r.id_modelo == modelo['id_modelo'] and r.tipo == TipoCodigo.BASELINE.value and r.linguagem == Linguagem.PYTHON.value for r in resultados_acumulados)
                    modelo_processado_java_Json = any(r.id_desafio == desafio['id_desafio'] and r.id_modelo == modelo['id_modelo'] and r.tipo == TipoCodigo.BASELINE.value and r.linguagem == Linguagem.JAVA.value for r in resultados_acumulados)
                    if(modelo_processado_python_Json and modelo_processado_java_Json):
                        print(f"Desafio {desafio['id_desafio']} já processado para o modelo {modelo['nome_modelo']} no arquivo JSON. Pulando...")
                        continue
                    # Processamento Python
                    if not modelo_processado_python:
                        try:
                            #verifica se o modelo já processou o desafio para a linguagem Python, caso contrário, processa e salva no arquivo JSON
                            if modelo_processado_python_Json:
                                print(f"Desafio {desafio['id_desafio']} já processado para o modelo {modelo['nome_modelo']} (Python) no arquivo JSON. Pulando...")
                            else:
                                print(f"Processando {modelo['nome_modelo']} (Python)... Para o desafio {desafio['id_desafio']}...")
                                codigo_py = self.gerador_codigo_llm.solicitar_codigo_llm(modelo['nome_modelo'], prompt_python, Linguagem.PYTHON.value)
                                resultados_acumulados.append(Resultado(
                                    id_desafio=desafio['id_desafio'],
                                    id_modelo=modelo['id_modelo'],
                                    tipo=TipoCodigo.BASELINE.value,
                                    codigo_fonte=codigo_py,
                                    linguagem=Linguagem.PYTHON.value
                            ))
                        except Exception as e:
                            print(f"Falha no modelo {modelo['nome_modelo']} (Python): {e}")

                    # Processamento Java
                    if not modelo_processado_java:
                        try:
                            if modelo_processado_java_Json:
                                print(f"Desafio {desafio['id_desafio']} já processado para o modelo {modelo['nome_modelo']} (Java) no arquivo JSON. Pulando...")
                            else:
                                print(f"Processando {modelo['nome_modelo']} (Java)... Para o desafio {desafio['id_desafio']}...")
                                codigo_java = self.gerador_codigo_llm.solicitar_codigo_llm(modelo['nome_modelo'], prompt_java, Linguagem.JAVA.value)
                                resultados_acumulados.append(Resultado(
                                    id_desafio=desafio['id_desafio'],
                                    id_modelo=modelo['id_modelo'],
                                    tipo=TipoCodigo.BASELINE.value,
                                    codigo_fonte=codigo_java,
                                    linguagem=Linguagem.JAVA.value
                            ))
                        except Exception as e:
                            print(f"Falha no modelo {modelo['nome_modelo']} (Java): {e}")
                            
                    self.gerador_codigo_llm.escrever_resultados_em_json(caminho_arquivo = self.nome_arquivo_json, resultados_acumulados = resultados_acumulados)

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
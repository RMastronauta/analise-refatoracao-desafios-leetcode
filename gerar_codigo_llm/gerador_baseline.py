import os
import sys
import time
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
        self.nome_arquivo_prompt_json = "resultado_baseline_prompts.json"

    def executar_desafio(self, modelo_processado, id_desafio, id_modelo, prompt, nome_modelo, linguagem):
        try:
            if modelo_processado:
                print(f"Desafio {id_desafio} já processado para o modelo {nome_modelo} ({linguagem}) no arquivo JSON. Pulando...")
            else:
                print(f"Processando {nome_modelo} ({linguagem})... Para o desafio {id_desafio}...")
                codigo_py = self.gerador_codigo_llm.solicitar_codigo_llm(nome_modelo, prompt, linguagem)
                if not codigo_py:
                    raise ValueError("A IA não gerou um código válido.")
                return Resultado(
                    id_desafio=id_desafio,
                    id_modelo=id_modelo,
                    tipo=TipoCodigo.BASELINE.value,
                    codigo_fonte=codigo_py,
                    linguagem=linguagem)
        except Exception as e:
            print(f"Falha no modelo {nome_modelo} ({linguagem}): {e}")
        
    def processar_desafios(self):
        try:
            desafios = self.llm_request.select_into_table(table_name="desafios", campos=["id_desafio", "enunciado AS descricao"])
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

                    resultados_acumulados = self.gerador_codigo_llm.ler_resultados_processados_do_arquivo(self.nome_arquivo_json) or []
                    modelo_processado_python_Json = any(r.id_desafio == desafio['id_desafio'] and r.id_modelo == modelo['id_modelo'] and r.tipo == TipoCodigo.BASELINE.value and r.linguagem == Linguagem.PYTHON.value for r in resultados_acumulados)
                    modelo_processado_java_Json = any(r.id_desafio == desafio['id_desafio'] and r.id_modelo == modelo['id_modelo'] and r.tipo == TipoCodigo.BASELINE.value and r.linguagem == Linguagem.JAVA.value for r in resultados_acumulados)
                    if(modelo_processado_python_Json and modelo_processado_java_Json):
                        print(f"Desafio {desafio['id_desafio']} já processado para o modelo {modelo['nome_modelo']} no arquivo JSON. Pulando...")
                        continue
                    if modelo_processado_python or modelo_processado_python_Json:
                        print(f"Desafio {desafio['id_desafio']} já processado para o modelo {modelo['nome_modelo']} (Python). Pulando...")
                    else:
                        desafio_python = self.executar_desafio(modelo_processado = modelo_processado_python_Json, id_desafio = desafio['id_desafio'], id_modelo = modelo['id_modelo'], prompt = prompt_python, nome_modelo = modelo['nome_modelo'], linguagem = Linguagem.PYTHON.value)
                        if desafio_python:
                            resultados_acumulados.append(desafio_python)
                    if modelo_processado_java or modelo_processado_java_Json:
                        print(f"Desafio {desafio['id_desafio']} já processado para o modelo {modelo['nome_modelo']} (Java). Pulando...")
                    else:
                        desafio_java = self.executar_desafio(modelo_processado = modelo_processado_java_Json, id_desafio = desafio['id_desafio'], id_modelo = modelo['id_modelo'], prompt = prompt_java, nome_modelo = modelo['nome_modelo'], linguagem = Linguagem.JAVA.value)
                        if desafio_java:
                            resultados_acumulados.append(desafio_java)

                    self.gerador_codigo_llm.escrever_resultados_em_json(caminho_arquivo = self.nome_arquivo_json, resultados_acumulados = resultados_acumulados)

            # Após processar todos os desafios e modelos, ler os resultados acumulados do arquivo JSON para garantir que a variável esteja definida
            self.resultados_processados = self.gerador_codigo_llm.ler_resultados_processados_do_arquivo(self.nome_arquivo_json)
            
            # Persistência no Banco
            if self.resultados_processados:
                self.llm_request.insert_resultados(self.resultados_processados)

        except Exception as e:
            print(f"Erro geral: {e}")
        finally:
            self.llm_request.close_db_connection()


if __name__ == "__main__":
    gerador = Gerador_Baseline()
    gerador.processar_desafios()
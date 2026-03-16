import json
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

class Gerador_Refatorado:
    def __init__(self):
        self.repository = Repository()
        self.gerador_codigo_llm = gerador_codigo_llm()
        self.resultados_processados = list[Resultado]()
        self.nome_arquivo_json = "resultado_refatorado.json"
        
    def processar_refatoracao(self):
        try:
            resultados = self.repository.select_into_table(table_name= "resultados", campos=["id_desafio", "id_modelo", "codigo_fonte"], data={'tipo': TipoCodigo.BASELINE.value}, size=5)
            modelos = self.repository.select_into_table(table_name = "modelos", campos=["id_modelo", "nome_modelo"])
            for resultado in resultados:
                modelo = next((m for m in modelos if m['id_modelo'] == resultado['id_modelo']), None)
                python_processado = self.gerador_codigo_llm.ModeloJaProcessado(resultado['id_desafio'], resultado['id_modelo'], TipoCodigo.REFATORADO.value, Linguagem.PYTHON.value)
                java_processado = self.gerador_codigo_llm.ModeloJaProcessado(resultado['id_desafio'], resultado['id_modelo'], TipoCodigo.REFATORADO.value, Linguagem.JAVA.value)
                if(python_processado and java_processado):
                    print(f"Desafio {resultado['id_desafio']} já processado com {modelo['nome_modelo']} para o tipo de código {TipoCodigo.REFATORADO.value}. Pulando...")
                    continue

                print(f"Processando Desafio {resultado['id_desafio']} com {modelo['nome_modelo']}...")
                
                prompt_python = self.gerador_codigo_llm.GetPrompt(resultado['codigo_fonte'], TipoCodigo.REFATORADO, Linguagem.PYTHON.value)
                prompt_java = self.gerador_codigo_llm.GetPrompt(resultado['codigo_fonte'], TipoCodigo.REFATORADO, Linguagem.JAVA.value)

                try:
                    resultados_acumulados = self.gerador_codigo_llm.ler_resultados_processados_do_arquivo(self.nome_arquivo_json) or []
                    modelo_processado_python_Json = any(r.id_desafio == resultado['id_desafio'] and r.id_modelo == modelo['id_modelo'] and r.tipo == TipoCodigo.REFATORADO.value and r.linguagem == Linguagem.PYTHON.value for r in resultados_acumulados)
                    modelo_processado_java_Json = any(r.id_desafio == resultado['id_desafio'] and r.id_modelo == modelo['id_modelo'] and r.tipo == TipoCodigo.REFATORADO.value and r.linguagem == Linguagem.JAVA.value for r in resultados_acumulados)
                    if(modelo_processado_python_Json and modelo_processado_java_Json):
                        print(f"Desafio {resultado['id_desafio']} já processado para o modelo {modelo['nome_modelo']} no arquivo JSON. Pulando...")
                        continue
                    if not python_processado:
                        if modelo_processado_python_Json:
                            print(f"Desafio {resultado['id_desafio']} já processado para o modelo {modelo['nome_modelo']} (Python) no arquivo JSON. Pulando...")
                        else:
                            print(f"Processando Desafio {resultado['id_desafio']} com {modelo['nome_modelo']}, para a linguagem {Linguagem.PYTHON.value}...")
                            codigo_Python_gerado = self.gerador_codigo_llm.solicitar_codigo_llm(modelo['nome_modelo'], prompt_python, Linguagem.PYTHON.value)
                            resultados_acumulados.append(Resultado(
                                id_desafio=resultado['id_desafio'],
                                id_modelo=modelo['id_modelo'],
                                tipo=TipoCodigo.REFATORADO.value,
                                codigo_fonte=codigo_Python_gerado,
                                linguagem=Linguagem.PYTHON.value
                        ))
                    if not java_processado:
                        if modelo_processado_java_Json:
                            print(f"Desafio {resultado['id_desafio']} já processado para o modelo {modelo['nome_modelo']} (Java) no arquivo JSON. Pulando...")
                        else:
                            print(f"Processando Desafio {resultado['id_desafio']} com {modelo['nome_modelo']}, para a linguagem {Linguagem.JAVA.value}...")
                            codigo_Java_gerado = self.gerador_codigo_llm.solicitar_codigo_llm(modelo['nome_modelo'], prompt_java, Linguagem.JAVA.value)
                            resultados_acumulados.append(Resultado(
                                id_desafio=resultado['id_desafio'],
                                id_modelo=modelo['id_modelo'],
                            tipo=TipoCodigo.REFATORADO.value,
                            codigo_fonte=codigo_Java_gerado,
                            linguagem=Linguagem.JAVA.value
                        ))
                    self.gerador_codigo_llm.escrever_resultados_em_json(resultados_acumulados, self.nome_arquivo_json)
                    
                except Exception as e:
                    print(f"Falha crítica após retentativas no desafio {resultado['id_desafio']} para o tipo de código {TipoCodigo.REFATORADO.value}: {e}")
            
            # Após processar todos os desafios e modelos, ler os resultados acumulados do arquivo JSON para garantir que a variável esteja definida
            self.gerador_codigo_llm.ler_resultados_processados_do_arquivo(self.nome_arquivo_json)
            
            # Persistência no Banco
            if self.resultados_processados:
                self.repository.insert_resultados(self.resultados_processados)
                print(f"Sucesso! {len(self.resultados_processados)} resultados inseridos.")
        except Exception as e:
            print(f"Erro ao processar desafios: {e}")
        finally:
            self.repository.close_db_connection()
                    

if __name__ == "__main__":
    gerador = Gerador_Refatorado()
    gerador.processar_refatoracao()
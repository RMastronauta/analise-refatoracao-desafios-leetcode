import os
import sys
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if root_path not in sys.path:
    sys.path.append(root_path)

from enums.tipo_codigo import TipoCodigo
from gerar_codigo_llm.gerador_codigo_llm import gerador_codigo_llm
from repository.repository import Repository

class Gerador_Baseline:
    def __init__(self):
        self.llm_request = Repository()
        self.gerador_codigo_llm = gerador_codigo_llm()
        
    def processar_desafios(self):
        try:
            desafios = self.llm_request.select_into_table(table_name= "desafios", campos=["id_desafio", "enunciado AS descricao"], size=1)
            modelos = self.llm_request.select_into_table(table_name = "modelos", campos=["id_modelo", "nome_modelo"], size=4)

            for desafio in desafios:
                for modelo in modelos:

                    if(self.gerador_codigo_llm.ModeloJaProcessado(desafio['id_desafio'], modelo['id_modelo'], TipoCodigo.BASELINE.value)):
                        print(f"Desafio {desafio['id_desafio']} já processado com {modelo['nome_modelo']} para o tipo de código {TipoCodigo.BASELINE.value}. Pulando...")
                        continue

                    print(f"Processando Desafio {desafio['id_desafio']} com {modelo['nome_modelo']}...")
                    
                    prompt = self.gerador_codigo_llm.GetPrompt(desafio['descricao'], TipoCodigo.BASELINE)
                    
                    try:
                        codigo_gerado = self.gerador_codigo_llm.solicitar_codigo_llm(modelo['nome_modelo'], prompt)

                        novo_resultado = {
                            'id_desafio': desafio['id_desafio'],
                            'id_modelo': modelo['id_modelo'],
                            'tipo': TipoCodigo.BASELINE.value,
                            'codigo_fonte': codigo_gerado
                        }
                        self.llm_request.insert_into_table('resultados', novo_resultado)
                        
                    except Exception as e:
                        print(f"Falha crítica após retentativas no desafio {desafio['id_desafio']}: {e}")
        except Exception as e:
            print(f"Erro ao processar desafios: {e}")
        finally:
            self.llm_request.close_db_connection()
                    

if __name__ == "__main__":
    gerador = Gerador_Baseline()
    gerador.processar_desafios()
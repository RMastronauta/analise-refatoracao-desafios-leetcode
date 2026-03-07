import os
import sys
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if root_path not in sys.path:
    sys.path.append(root_path)

from enums.tipo_codigo import TipoCodigo
from gerar_codigo_llm.gerador_codigo_llm import gerador_codigo_llm
from repository.repository import Repository

class Gerador_Refatorado:
    def __init__(self):
        self.repository = Repository()
        self.gerador_codigo_llm = gerador_codigo_llm()
        
    def processar_refatoracao(self):
        try:
            resultados = self.repository.select_into_table(table_name= "resultados", campos=["id_desafio", "id_modelo", "codigo_fonte"], data={'tipo': TipoCodigo.BASELINE.value}, size=5)

            for resultado in resultados:
                modelo = self.repository.select_into_table(table_name = "modelos", campos=["id_modelo", "nome_modelo"], data={'id_modelo': resultado['id_modelo']}, size=1)[0]
                
                if(self.gerador_codigo_llm.ModeloJaProcessado(resultado['id_desafio'], modelo['id_modelo'], TipoCodigo.REFATORADO.value)):
                    print(f"Desafio {resultado['id_desafio']} já processado com {modelo['nome_modelo']} para o tipo de código {TipoCodigo.REFATORADO.value}. Pulando...")
                    continue

                print(f"Processando Desafio {resultado['id_desafio']} com {modelo['nome_modelo']}...")
                
                prompt = self.gerador_codigo_llm.GetPrompt(resultado['codigo_fonte'], TipoCodigo.REFATORADO)
                
                try:
                    codigo_gerado = self.gerador_codigo_llm.solicitar_codigo_llm(modelo['nome_modelo'], prompt)

                    novo_resultado = {
                        'id_desafio': resultado['id_desafio'],
                        'id_modelo': modelo['id_modelo'],
                        'tipo': TipoCodigo.REFATORADO.value,
                        'codigo_fonte': codigo_gerado
                    }
                    self.repository.insert_into_table('resultados', novo_resultado)
                    
                except Exception as e:
                    print(f"Falha crítica após retentativas no desafio {resultado['id_desafio']} para o tipo de código {TipoCodigo.REFATORADO.value}: {e}")
        except Exception as e:
            print(f"Erro ao processar desafios: {e}")
        finally:
            self.repository.close_db_connection()
                    

if __name__ == "__main__":
    gerador = Gerador_Refatorado()
    gerador.processar_refatoracao()
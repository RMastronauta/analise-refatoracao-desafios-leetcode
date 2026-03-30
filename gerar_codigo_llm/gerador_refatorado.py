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
    def __init__(self, tipocodigo: TipoCodigo):
        self.repository = Repository()
        self.gerador_codigo_llm = gerador_codigo_llm()
        self.resultados_processados: list[Resultado]
        self.nome_arquivo_json = f"resultado_{tipocodigo.value}.json"
        self.nome_arquivo_prompt_json = f"resultado_{tipocodigo.value}_prompts.json"
        self.tipo_codigo = tipocodigo
    
    def executar_refatoracao(self, prompt, id_desafio, id_modelo, nome_modelo, linguagem, id_resultado):
        try:
            print(f"Processando Desafio {id_desafio} com {nome_modelo}, para a linguagem {linguagem}... Para o resultado de id {id_resultado}...")
            codigo_Java_gerado = self.gerador_codigo_llm.solicitar_codigo_llm(nome_modelo, prompt, linguagem)
            if not codigo_Java_gerado:
                raise ValueError("A IA não gerou um código válido.")
            return Resultado(
                id_desafio=id_desafio,
                id_modelo=id_modelo,
                tipo=self.tipo_codigo.value,
                codigo_fonte=codigo_Java_gerado,
                linguagem=linguagem)
        except Exception as e:
            print(f"Falha no modelo {nome_modelo} ({linguagem}): {e}")
            raise

    def processar_refatoracao(self):
        try:
            #resultados = self.repository.select_into_table(table_name= "resultados", campos=["id_resultado", "id_desafio", "id_modelo", "codigo_fonte", "linguagem"], filter="id_resultado not in (1801, 1802, 1803, 1804) and tipo = 'baseline' and codigo_fonte is not null")
            resultados = self.repository.getResultadosBaselineNaoExecutados(self.tipo_codigo.value, 10000)
            modelos = self.repository.select_into_table(table_name = "modelos", campos=["id_modelo", "nome_modelo"])
            self.resultados_processados = self.gerador_codigo_llm.ler_resultados_processados_do_arquivo(self.nome_arquivo_json) or list[Resultado]()
            count_arquivo = 1
            for resultado in resultados:
                modelo = next((m for m in modelos if m['id_modelo'] == resultado['id_modelo']), None)
                # pega o enum de modelos pelo nome do modelo    

                modelo_ja_processaor = self.gerador_codigo_llm.ModeloJaProcessado(resultado['id_desafio'], resultado['id_modelo'], self.tipo_codigo.value, resultado['linguagem'])
                
                if(modelo_ja_processaor):
                    print(f"Desafio {resultado['id_desafio']} já processado com {modelo['nome_modelo']} para a linguagem {resultado['linguagem']}. Pulando...")
                    continue
                
                prompt = self.gerador_codigo_llm.GetPrompt(resultado['codigo_fonte'], self.tipo_codigo, resultado['linguagem'])
                # print(f"Prompt gerado para o desafio {resultado['id_desafio']} com o modelo {modelo['nome_modelo']} para a linguagem {resultado['linguagem']}: {prompt}")
                # self.gerador_codigo_llm.escrever_prompt_em_json(self.nome_arquivo_prompt_json, prompt)
                # continue
                try:
                    modelo_processado = any(r.id_desafio == resultado['id_desafio'] and r.id_modelo == modelo['id_modelo'] and r.tipo == self.tipo_codigo.value and r.linguagem == resultado['linguagem'] for r in self.resultados_processados)
                    if(modelo_processado):
                        print(f"Desafio {resultado['id_desafio']} já processado para o modelo {modelo['nome_modelo']} ({resultado['linguagem']}) no arquivo JSON. Pulando...")
                        continue

                    resultado_gerado = self.executar_refatoracao(prompt, resultado['id_desafio'], resultado['id_modelo'], modelo['nome_modelo'], resultado['linguagem'], resultado['id_resultado'])
                    self.resultados_processados.append(resultado_gerado)
                    self.gerador_codigo_llm.escrever_resultados_em_json(self.nome_arquivo_json, self.resultados_processados)

                    if len(self.resultados_processados) >= 100:
                        self.repository.insert_resultados(self.resultados_processados)
                        self.resultados_processados = list[Resultado]()
                        count_arquivo = count_arquivo + 1
                        self.nome_arquivo_json = f"resultado_refatorado{count_arquivo}.json"
                    
                except Exception as e:
                    print(f"Falha crítica após retentativas no desafio {resultado['id_desafio']} para o tipo de código {self.tipo_codigo.value}: {e}")
            
            # Persistência no Banco
            if self.resultados_processados:
                self.repository.insert_resultados(self.resultados_processados)
        except Exception as e:
            print(f"Erro ao processar desafios: {e}")
        finally:
            self.repository.close_db_connection()
                    

if __name__ == "__main__":
    gerador = Gerador_Refatorado(TipoCodigo.REFATORADO)
    gerador.processar_refatoracao()
    gerador = Gerador_Refatorado(TipoCodigo.REFATORADO_SIMPLIFICADO)
    gerador.processar_refatoracao()
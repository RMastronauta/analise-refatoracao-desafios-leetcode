import os
import sys
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if root_path not in sys.path:
    sys.path.append(root_path)
from gerar_codigo_llm.llm_request import LLMRequester
from repository.repository import close_db_connection, insert_into_table, select_into_table


def validar_codigo_python(codigo):
    """Verifica se a resposta realmente parece um código funcional"""
    indicadores = ['def ', 'class ', 'import ', 'return ', ' = ']
    # Se não houver nenhum desses termos, a IA provavelmente enviou apenas texto
    return any(term in codigo for term in indicadores)

def extrair_codigo(texto):
    """Limpa o Markdown e retorna apenas o conteúdo do bloco de código"""
    if "```python" in texto:
        return texto.split("```python")[1].split("```")[0].strip()
    elif "```" in texto:
        return texto.split("```")[1].split("```")[0].strip()
    return texto.strip()

@retry(
    stop=stop_after_attempt(5), 
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type(Exception)
)
def solicitar_codigo_llm(modelo_nome, prompt_corpo):
    """
    Tenta gerar o código. Se a validação falhar, levanta exceção 
    para o @retry tentar novamente (até 5 vezes com espera exponencial).
    """
    codigo_bruto = ""
    if "Gemini" == modelo_nome:
        return ""
        id_tecnico = "gemini-3-flash-preview"
    elif "deepseek" == modelo_nome:
        id_tecnico = "deepseek-v3.2:cloud"
    elif "GPT" == modelo_nome:
        id_tecnico = "gpt-oss-safeguard:latest"
    elif "LLAMA" == modelo_nome:
        id_tecnico = "compcj/llama4-scout-ud-q2-k-xl:latest"
    else:
        id_tecnico = modelo_nome # fallback
    
    llm_request =LLMRequester() 
    # 1. Roteamento por Modelo
    if "gemini" in modelo_nome:
        codigo_bruto = llm_request.request_gemini(id_tecnico, prompt_corpo)
    else: # GPT, LLAMA e GROQ
        codigo_bruto = llm_request.request_llama(id_tecnico, prompt_corpo)

    # 2. Extração e Limpeza
    codigo_limpo = extrair_codigo(codigo_bruto)
    print(f"[{modelo_nome}] Código bruto:\n{codigo_bruto}\n")
    # 3. Defensiva: Validação de Conteúdo
    if not validar_codigo_python(codigo_limpo) or len(codigo_limpo) < 20:
        print(f"[{modelo_nome}] Falha na validação. Tentando novamente...")
        raise ValueError("A IA não gerou um código Python válido.")

    return codigo_limpo

def processar_desafios():

    # 1. Busca os desafios e os modelos
    desafios = select_into_table(table_name= "desafios", campos=["id_desafio", "enunciado AS descricao"], size=1)
    modelos = select_into_table(table_name = "modelos", campos=["id_modelo", "nome_modelo"], size=4)

    for desafio in desafios:
        for modelo in modelos:
            print(f"Processando Desafio {desafio['id_desafio']} com {modelo['nome_modelo']}...")
            
            prompt = (
                "Você é um engenheiro de software sênior. "
                "Resolva o desafio do LeetCode abaixo estritamente em Python 3. "
                "Retorne APENAS o código fonte dentro de um bloco de código Markdown. "
                "O código deve ser autoexevutavel, sem dependências externas, e conter a função principal de solução. "
                "Não inclua explicações, exemplos de uso ou comentários fora do código.\n\n"
                f"DESAFIO: {desafio['descricao']}"
            )
            
            try:
                codigo_gerado = solicitar_codigo_llm(modelo['nome_modelo'], prompt)

                novo_resultado = {
                    'id_desafio': desafio['id_desafio'],
                    'id_modelo': modelo['id_modelo'],
                    'tipo': 'baseline',
                    'codigo_fonte': codigo_gerado
                }
                insert_into_table('resultados', novo_resultado)
                
            except Exception as e:
                print(f"Falha crítica após retentativas no desafio {desafio['id_desafio']}: {e}")
                

if __name__ == "__main__":
    processar_desafios()
    close_db_connection()
import os
import sys
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from openai import OpenAI
from google import genai as google_genai
from dotenv import load_dotenv

root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if root_path not in sys.path:
    sys.path.append(root_path)
from repository.repository import close_db_connection, insert_into_table, select_into_table

load_dotenv()

# Configurações de Conexão
client_google = google_genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
client_openai = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
client_groq = OpenAI(api_key=os.getenv('GROQ_API_KEY'), base_url="https://api.groq.com/openai/v1")

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
    if "Gemini" in modelo_nome:
        id_tecnico = "gemini-3-flash-preview"
    elif "Gemma" in modelo_nome:
        id_tecnico = "gemma-2-9b-it" # ou gemma-7b
    elif "GPT" in modelo_nome:
        id_tecnico = "gpt-3.5-turbo"
    elif "LLAMA" in modelo_nome:
        id_tecnico = "llama-3.1-70b-versatile"
    else:
        id_tecnico = modelo_nome # fallback

    # 1. Roteamento por Modelo
    if "Gemini" in modelo_nome or "Gemma" in modelo_nome:
        response = client_google.models.generate_content(
            model=id_tecnico,
            contents=prompt_corpo,
        )
        codigo_bruto = response.text
        
    elif "GPT" in modelo_nome:
        response = client_openai.chat.completions.create(
            model=id_tecnico,
            messages=[{"role": "user", "content": prompt_corpo}]
        )
        codigo_bruto = response.choices[0].message.content

    elif "LLAMA" in modelo_nome:
        # Exemplo via Groq/OpenRouter/Ollama
        response = client_groq.chat.completions.create(
            model=id_tecnico,
            messages=[{"role": "user", "content": prompt_corpo}]
        )
        codigo_bruto = response.choices[0].message.content

    # 2. Extração e Limpeza
    codigo_limpo = extrair_codigo(codigo_bruto)

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
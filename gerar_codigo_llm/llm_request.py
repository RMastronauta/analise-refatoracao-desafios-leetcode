import os
from google.genai import types
from google import genai
from dotenv import load_dotenv
from ollama import Client


load_dotenv()

# Configurações de Conexão
client_google = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))


class LLMRequester():
    def __init__(self):
        self.client = Client(host='http://localhost:11434', timeout=600)

    def request_llama(self, llm_model, prompt):
        try:
            options = {
                'temperature': 0,
                }
            response = self.client.chat(
                model=llm_model,
                messages=[{"role": "user", "content": prompt}],
                options = options
            )
            message = response.get('message', {})
            
            conteudo = message.get('content', '').strip()
            
            if not conteudo:
                conteudo = message.get('thinking', '').strip()

            return conteudo
        except Exception as e:
            print(f"Erro crítico no Ollama Proxy ({llm_model}): {e}")
            raise
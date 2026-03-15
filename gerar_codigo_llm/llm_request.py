import os
from google.genai import types
from ollama import chat
from google import genai
from dotenv import load_dotenv


load_dotenv()

# Configurações de Conexão
client_google = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))


class LLMRequester():
    def request_llama(self, llm_model, prompt):
        response = chat(
            model=llm_model,
            messages=[{"role": "user", "content": prompt}],
            options={'temperature': 0}
        )
        conteudo = response.get('message', {}).get('content', '')
        if not conteudo or conteudo.strip() == "":
            conteudo = response.get('message', {}).get('thinking', '')
        return conteudo


    def request_gemini(self,llm_model, prompt):
        response = client_google.models.generate_content(
                model=llm_model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0,
                )
            )
        return response.text
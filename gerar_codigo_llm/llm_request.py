import os
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
            messages=[{"role": "user", "content": prompt}]
        )
        print(f"Resposta bruta do modelo {llm_model}:\n{response}\n")
        return response['message']['content']


    def request_gemini(self,llm_model, prompt):
        response = client_google.models.generate_content(
                model=llm_model,
                contents=prompt,
            )
        return response.text
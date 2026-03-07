import os
import sys
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if root_path not in sys.path:
    sys.path.append(root_path)
from repository.repository import Repository
from enums.llm import llm 
from enums.tipo_codigo import TipoCodigo
from gerar_codigo_llm.llm_request import LLMRequester


class gerador_codigo_llm:

    def __init__(self):
        self.llm_request = LLMRequester()
        self.repostitory = Repository()

    def validar_codigo_python(self, codigo):
        """Verifica se a resposta realmente parece um código funcional"""
        indicadores = ['def ', 'class ', 'import ', 'return ', ' = ']
        # Se não houver nenhum desses termos, a IA provavelmente enviou apenas texto
        return any(term in codigo for term in indicadores)

    def extrair_codigo(self, texto):
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
    def solicitar_codigo_llm(self, modelo_nome, prompt_corpo):
        """
        Tenta gerar o código. Se a validação falhar, levanta exceção 
        para o @retry tentar novamente (até 5 vezes com espera exponencial).
        """
        codigo_bruto = ""
        id_tecnico = llm[modelo_nome.upper()].value

        llm_request =LLMRequester() 

        if llm.GEMINI.value in id_tecnico:
            codigo_bruto = llm_request.request_gemini(id_tecnico, prompt_corpo)
        else:
            codigo_bruto = llm_request.request_llama(id_tecnico, prompt_corpo)

        # 2. Extração e Limpeza
        codigo_limpo = self.extrair_codigo(codigo_bruto)
        print(f"[{modelo_nome}] Código bruto:\n{codigo_bruto}\n")
        
        # 3. Defensiva: Validação de Conteúdo
        if not self.validar_codigo_python(codigo_limpo) or len(codigo_limpo) < 20:
            print(f"[{modelo_nome}] Falha na validação. Tentando novamente...")
            raise ValueError("A IA não gerou um código Python válido.")

        return codigo_limpo

    def ModeloJaProcessado(self, id_desafio, id_modelo, tipo_codigo):
        """Verifica se já existe um resultado para esse desafio e modelo"""
        resultados = self.repostitory.select_into_table(
            table_name='resultados', 
            campos=['codigo_fonte'], 
            data={'id_desafio': id_desafio, 'id_modelo': id_modelo, 'tipo': tipo_codigo},
            size=1
        )
        return len(resultados) > 0 and resultados[0]['codigo_fonte'] is not None and self.validar_codigo_python(resultados[0]['codigo_fonte'])

    def GetPrompt(self, descricao, tipo_codigo):
        """Gera o prompt específico para o tipo de código solicitado"""
        if tipo_codigo == TipoCodigo.BASELINE:
            return (
                "Você é um programador Python especialista em resolver desafios de algoritmos e"
                "estruturas de dados. Resolva o seguinte desafio de programação:\n\n"
                f"DESAFIO: {descricao} \n\n"
                "Instruções para a saída:\n"
                "Forneça uma solução completa em Python.\n"
                "Não inclua explicações, comentários introdutórios ou texto adicional.\n"
                "Sua resposta deve conter APENAS o código-fonte Python e nada mais.\n"
            )
        elif tipo_codigo == TipoCodigo.REFATORADO:
            return (
                "Você é um engenheiro de software sênior especializado em clean code, padrões de projeto e refatoração de software. "
                "Analise o código Python abaixo, que é uma solução para um desafio de algoritmos. "
                "Seu objetivo é refatorar este código para melhorar sua qualidade. \n"
                F"Código para refatorar: \n {descricao}\n\n"
                "Instruções para a saída:\n"
                "Forneça uma solução completa em Python.\n"
                "Não inclua explicações, comentários introdutórios ou texto adicional.\n"
                "Sua resposta deve conter APENAS o código-fonte Python e nada mais.\n"
            )


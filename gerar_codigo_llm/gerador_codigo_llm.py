import json
import os
import re
import sys
from entity.resultado import Resultado
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if root_path not in sys.path:
    sys.path.append(root_path)
from enums.lingagem import Linguagem
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
    def validar_codigo_java(self, codigo):
        """Verifica se a resposta realmente parece um código Java funcional"""
        indicadores = [
            'public class ', 'private ', 'protected ', 
            'static void main', 'import java.', 
            'System.out.print', 'new ', ';', '{'
        ]
        return any(term in codigo for term in indicadores)

    def extrair_codigo_java(self, texto):
        """Extrai o código Java ignorando explicações antes ou depois do bloco principal."""
        if "```java" in texto:
            return texto.split("```java")[1].split("```")[0].strip()
        elif "```" in texto:
            return texto.split("```")[1].split("```")[0].strip()
        

        padrao_inicio = re.search(r'(import\s+|public\s+class\s+|class\s+)', texto)
        
        if padrao_inicio:
            codigo_parcial = texto[padrao_inicio.start():].strip()
            return codigo_parcial
            
        return texto.strip()
    # @retry(
    #     stop=stop_after_attempt(1),
    #     wait=wait_exponential(multiplier=2, min=4, max=20),
    #     retry=retry_if_exception_type(Exception),
    #     before_sleep=lambda retry_state: print(f"Aguardando próxima tentativa... (Tentativa {retry_state.attempt_number})")
    # )
    def solicitar_codigo_llm(self, modelo_nome, prompt_corpo, linguagem):
        """
        Tenta gerar o código. Se a validação falhar, levanta exceção 
        para o @retry tentar novamente (até 5 vezes com espera exponencial).
        """
        try: 
            codigo_bruto = ""
            id_tecnico = llm[modelo_nome.upper()].value
            codigo_bruto = self.llm_request.request_llama(id_tecnico, prompt_corpo)

            # 2. Extração e Limpeza
            if Linguagem.PYTHON.value in linguagem:
                codigo_limpo = self.extrair_codigo(codigo_bruto)
            elif Linguagem.JAVA.value in linguagem:
                codigo_limpo = self.extrair_codigo_java(codigo_bruto)
            
            # 3. Defensiva: Validação de Conteúdo
            if Linguagem.PYTHON.value in linguagem:
                if not self.validar_codigo_python(codigo_limpo) or len(codigo_limpo) < 20:
                    print(f"[{modelo_nome}] Falha na validação. Tentando novamente...")
                    raise ValueError("A IA não gerou um código Python válido.")
            elif Linguagem.JAVA.value in linguagem:
                if not self.validar_codigo_java(codigo_limpo) or len(codigo_limpo) < 20:
                    print(f"[{modelo_nome}] Falha na validação. Tentando novamente...")
                    raise ValueError("A IA não gerou um código Java válido.")

            return codigo_limpo
        except Exception as e:
            print(f"Erro ao solicitar código do modelo {modelo_nome}: {e}")
            raise

    def ModeloJaProcessado(self, id_desafio, id_modelo, tipo_codigo, linguagem):
        """Verifica se já existe um resultado para esse desafio e modelo"""
        resultados = self.repostitory.select_into_table(
            table_name='resultados', 
            campos=['codigo_fonte'], 
            data={'id_desafio': id_desafio, 'id_modelo': id_modelo, 'tipo': tipo_codigo, 'linguagem': linguagem},
            size=1
        )
        return len(resultados) > 0 and resultados[0]['codigo_fonte'] is not None and self.validar_codigo_python(resultados[0]['codigo_fonte'])

    def GetPrompt(self, descricao, tipo_codigo, linguagem):
        """Gera o prompt específico para o tipo de código solicitado"""
        if tipo_codigo == TipoCodigo.BASELINE:
            return (
                f"Você é um programador {linguagem} especialista em resolver desafios de algoritmos e "
                f"estruturas de dados. Resolva o seguinte desafio de programação:\n\n"
                f"DESAFIO: {descricao} \n\n"
                "Instruções para a saída:\n"
                f"Forneça uma solução completa em {linguagem}.\n"
                "Não inclua explicações, comentários introdutórios ou texto adicional.\n"
                f"Sua resposta deve conter APENAS o código-fonte {linguagem} e nada mais.\n"
            )
        elif tipo_codigo == TipoCodigo.REFATORADO_SIMPLIFICADO:
            return (
                " Como um especialista em engenharia de software, sua tarefa é refatorar o código fornecido abaixo para garantir que ele seja funcionalmente correto e siga as melhores práticas de Clean Code. \n"
                " Diretrizes de Refatoração (Baseadas em MSR 2025): \n"
                " * Identifique e importe todas as dependências externas necessárias antes da definição da classe/função. \n"
                " * Não utilize funções aninhadas; todos os métodos auxiliares devem ser de nível superior ou membros da classe. \n"
                " * Remova comentários desnecessários, códigos de teste ou redundâncias. \n"
                " * Garanta que não existam erros de sintaxe ou semântica. \n\n"
                " Código para Refatoração:"
                f" \n {descricao} \n\n"
                " Instruções para a saída: \n" 
                f" Forneça apenas a implementação refatorada em {linguagem} dentro de um bloco de código.\n"
                f" O código não pode conter erros de sintaxe ou semântica e deve ser funcionalmente correto. \n"
            )
        elif tipo_codigo == TipoCodigo.REFATORADO:
            return (
                "Aqui está um trecho de código original (baseline) desenvolvido para um sistema a solução de um desafio do LeetCode. Sua tarefa é fornecer uma solução de código superior a versão original. \n\n"
                " Objetivos de Qualidade:\n"
                " * Redução de Complexidade: Otimize a lógica para alcançar a menor Complexidade Ciclomática e Complexidade Cognitiva possíveis. \n"
                " * Manutenibilidade: Melhore o Índice de Manutenibilidade (MI) através de uma estrutura mais concisa e elegante. \n"
                " * Segurança e Robustez: Incorpore tratamento de erros adequado para evitar falhas em tempo de execução e garantir a segurança do código. \n"
                " * Modernização: Utilize recursos modernos da linguagem {linguagem} para simplificar a implementação, visando reduzir o número de linhas de código (LOC) sem perder a clareza. \n"
                " Código Original (Baseline):"
                f" \n {descricao} \n\n"
                " Instruções para a saída: \n"
                f" 1. Forneça apenas a implementação refatorada em {linguagem} dentro de um bloco de código. \n"
                f" 2. Certifique-se de que o código gerado seja funcionalmente correto, seguindo as melhores práticas de desenvolvimento e seja significativamente melhor em termos de qualidade em comparação com o código original. \n"
                f" 3. O código não pode conter erros de sintaxe ou semântica e deve ser funcionalmente correto, seguindo as melhores práticas de desenvolvimento."
            )
    def escrever_resultados_em_json(self, caminho_arquivo, resultados_acumulados):
        try:
            with open(caminho_arquivo, 'w') as f:
                dados_para_salvar = [r.__dict__ for r in resultados_acumulados]
                json.dump(dados_para_salvar, f, indent=4)
        except Exception as e:
            print(f"Erro ao escrever resultados no arquivo JSON: {e}")
    
    def escrever_prompt_em_json(self, caminho_arquivo, prompt):
        try:
            dados = []
            if os.path.exists(caminho_arquivo):
                with open(caminho_arquivo, 'r', encoding='utf-8') as f:
                    try:
                        dados = json.load(f)
                        if not isinstance(dados, list):
                            dados = []
                    except json.JSONDecodeError:
                        dados = []

            dados.append(prompt)

            with open(caminho_arquivo, 'w', encoding='utf-8') as f:
                json.dump(dados, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Erro ao escrever prompts no arquivo JSON: {e}")

    def ler_resultados_processados_do_arquivo(self, caminho_arquivo):
        if not os.path.exists(caminho_arquivo):
            print(f"Aviso: Arquivo {caminho_arquivo} não encontrado.")
            return
        resultados_processados = list[Resultado]()
        with open(caminho_arquivo, 'r') as f:
            try:
                dados = json.load(f)
                if isinstance(dados, list):
                    for item in dados:
                        resultado = Resultado(
                            id_desafio=item['id_desafio'],
                            id_modelo=item['id_modelo'],
                            tipo=item['tipo'],
                            codigo_fonte=item['codigo_fonte'],
                            linguagem=item['linguagem']
                        )
                        resultados_processados.append(resultado)
            except json.JSONDecodeError:
                print(f"Erro: O arquivo {caminho_arquivo} está corrompido ou vazio.")
        return resultados_processados


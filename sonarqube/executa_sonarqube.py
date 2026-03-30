import os
import sys
import subprocess
import time
from dotenv import load_dotenv
import requests
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if root_path not in sys.path:
    sys.path.append(root_path)
from enums.lingagem import Linguagem
from gerar_codigo_llm.llm_request import LLMRequester
from repository.repository import Repository


class executa_sonarqube:
    def __init__(self):
        self.repository = Repository()
        self.llm_request = LLMRequester()
        load_dotenv()
        self.scan_config = {
        'project_key': os.getenv('PROJECT_KEY'),
        'sonar_url': os.getenv('SONAR_URL'),
        'sonar_token': os.getenv('SONAR_TOKEN'),
        'executable': os.getenv('SONAR_SCANNER_PATH')
        }

    def run_sonar_scanner(self, file_path):
        command = [
        self.scan_config['executable'],
        f"-Dsonar.projectKey={self.scan_config['project_key']}",
        f"-Dsonar.sources={file_path}",
        f"-Dsonar.host.url={self.scan_config['sonar_url']}",
        f"-Dsonar.login={self.scan_config['sonar_token']}",
        "-Dsonar.python.version=3"
        ]
        subprocess.run(command, check=True)

    def get_sonar_metrics(self):
        # Endpoint da API para buscar medidas específicas
        metrics = "code_smells,sqale_index,complexity,duplicated_lines_density,ncloc"
        url = f"{self.scan_config['sonar_url']}/api/measures/component?component={self.scan_config['project_key']}&metricKeys={metrics}"
        response = requests.get(url, auth=(self.scan_config['sonar_token'], ""))
        return response.json()

    def salvar_metricas(self, id_resultado, metricas):
        # O dicionário deve ser uma estrutura única de chave: valor
        metricas_db = {
            'code_smells': int(metricas.get('code_smells', 0)),
            'divida_tecnica': int(metricas.get('sqale_index', 0)),
            'complexidade_ciclomatica': int(metricas.get('complexity', 0)),
            'duplicacao_percentual': float(metricas.get('duplicated_lines_density', 0)),
            'loc': int(metricas.get('ncloc', 0))
        }
        self.repository.update_table(table_name='resultados', data=metricas_db, conditions={'id_resultado': id_resultado})

    def wait_for_sonar_task(self, timeout=60):
        task_file = ".scannerwork/report-task.txt"
        start_time = time.time()
        
        # 1. Aguarda o arquivo aparecer
        while not os.path.exists(task_file):
            if time.time() - start_time > 20:
                print("  [!] Erro: report-task.txt não gerado.")
                return False
            time.sleep(0.5)

        # 2. Extrai a URL com limpeza rigorosa
        task_url = ""
        with open(task_file, 'r') as f:
            for line in f:
                if 'ceTaskUrl=' in line:
                    # O strip() remove \n, \r e espaços invisíveis que causam o erro 400
                    task_url = line.split('ceTaskUrl=')[1].strip()
                    break

        if not task_url:
            print("  [!] URL da tarefa não encontrada no arquivo.")
            return False

        # 3. Polling
        print(f"  [*] Checando status em: {task_url}")
        while True:
            if time.time() - start_time > timeout:
                print("  [!] Timeout!")
                return False

            try:
                # Importante: O Sonar pede o token no campo de 'username' e nada no 'password'
                response = requests.get(task_url, auth=(self.scan_config['sonar_token'], ""))
                
                if response.status_code == 200:
                    task_data = response.json().get('task', {})
                    status = task_data.get('status')
                    
                    if status == 'SUCCESS':
                        return True
                    elif status in ['FAILED', 'CANCELED']:
                        print(f"  [!] Falha no Sonar: {status}")
                        return False
                else:
                    print(f"  [!] Erro API {response.status_code}: {response.text}")
                    return False
                
                time.sleep(2)
            except Exception as e:
                print(f"  [!] Erro de conexão: {e}")
                return False
    
    def process_sonar(self):
        resultados = self.repository.select_into_table(
            table_name="resultados", 
            campos=["id_resultado", "codigo_fonte", "linguagem"], 
            data={'loc': 0},
            size = 10000
        )

        for resultado in resultados:
            task_file = ".scannerwork/report-task.txt"
            if os.path.exists(task_file):
                os.remove(task_file)
            # Define extensão correta
            ext = ".py" if "python" in resultado['linguagem'].lower() else ".java"
            file_path = f"temp_code_{resultado['id_resultado']}{ext}"

            try:
                # Salva arquivo
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(resultado['codigo_fonte'])
                
                # Executa Scanner
                print(f"Iniciando Scan ID: {resultado['id_resultado']}")
                self.run_sonar_scanner(file_path)

                # SUBSTITUIÇÃO DO SLEEP: Aguarda o servidor processar de verdade
                if self.wait_for_sonar_task(timeout=60):
                    metrics_raw = self.get_sonar_metrics()
                    
                    if 'component' in metrics_raw:
                        metricas_limpas = {m['metric']: m['value'] for m in metrics_raw['component']['measures']}
                        self.salvar_metricas(resultado['id_resultado'], metricas_limpas)
                        print(f"Sucesso: {resultado['id_resultado']}")
                else:
                    print(f"  [!] Falha ao obter métricas para ID {resultado['id_resultado']}")
            except Exception as e:
                print(f"Erro no registro {resultado['id_resultado']}: {e}")
            
            finally:
                if os.path.exists(file_path):
                    os.remove(file_path)

if __name__ == "__main__":
    sonarqube_processor = executa_sonarqube()
    sonarqube_processor.process_sonar()
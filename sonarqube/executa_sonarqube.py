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
    
    def process_sonar(self):
        resultados = self.repository.select_into_table(table_name= "resultados", campos=["id_resultado", "codigo_fonte", "linguagem"], data={'loc': 0})
        for resultado in resultados:
            if resultado['linguagem'] in Linguagem.PYTHON.value:
                file_path = f"temp_code_{resultado['id_resultado']}.py"
            elif resultado['linguagem'] in Linguagem.JAVA.value:
                file_path = f"temp_code_{resultado['id_resultado']}.java"

            with open(file_path, 'w') as f:
                f.write(resultado['codigo_fonte'])
            
            self.run_sonar_scanner(file_path)
            time.sleep(5)
            metrics = self.get_sonar_metrics()
            metricas_limpas = {m['metric']: m['value'] for m in metrics['component']['measures']}
            print(f"Métricas para resultado {resultado['id_resultado']}: {metricas_limpas}")
            self.salvar_metricas(resultado['id_resultado'], metricas_limpas)
            os.remove(file_path)

if __name__ == "__main__":

    sonarqube_processor = executa_sonarqube()
    sonarqube_processor.process_sonar()
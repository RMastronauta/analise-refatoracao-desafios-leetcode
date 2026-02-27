import requests

def get_request(url, headers=None, params=None):
        """Faz uma requisição GET e retorna o JSON ou None em caso de erro."""
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise f"Erro na requisição GET: {e}"
def post_request(url, headers=None, json=None):
        """Faz uma requisição POST e retorna o JSON ou None em caso de erro."""
        try:
            response = requests.post(url, headers=headers, json=json)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise f"Erro na requisição POST: {e}"
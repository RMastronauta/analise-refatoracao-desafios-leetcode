import os
import time
import requests
import mysql.connector
from datetime import datetime
from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env
load_dotenv()

# --- Configurações do Banco de Dados via Variáveis de Ambiente ---
db_config = {
    'host': os.getenv('DB_HOST'),
    'port': int(os.getenv('DB_PORT')),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME'),
}

API_URL = "https://leetcode.com/api/problems/all/"
HEADERS = {"User-Agent": "Mozilla/5.0"}

def get_problems_by_difficulty():
    """Busca todos os problemas e filtra 100 de cada dificuldade."""
    print("Conectando ao LeetCode via API REST...")
    try:
        response = requests.get(API_URL, headers=HEADERS)
        if response.status_code != 200:
            print(f"Erro ao acessar API: {response.status_code}")
            return []
        
        all_problems = response.json()['stat_status_pairs']
        
        easy, medium, hard = [], [], []
        
        for p in all_problems:
            if p['paid_only']: continue
            
            level = p['difficulty']['level']
            data = {
                'title': p['stat']['question__title'],
                'slug': p['stat']['question__title_slug'],
                'level': {1: 'Easy', 2: 'Medium', 3: 'Hard'}[level]
            }
            
            if level == 1 and len(easy) < 100: easy.append(data)
            elif level == 2 and len(medium) < 100: medium.append(data)
            elif level == 3 and len(hard) < 100: hard.append(data)
            
            if len(easy) == 100 and len(medium) == 100 and len(hard) == 100:
                break
                
        return easy + medium + hard
    except Exception as e:
        print(f"Erro na requisição: {e}")
        return []

def get_description(title_slug):
    """Busca o enunciado via GraphQL."""
    url = "https://leetcode.com/graphql"
    query = {
        "query": "query questionContent($titleSlug: String!) { question(titleSlug: $titleSlug) { content } }",
        "variables": {"titleSlug": title_slug}
    }
    try:
        r = requests.post(url, json=query, headers=HEADERS)
        content = r.json()['data']['question']['content']
        return content if content else "Sem enunciado disponível"
    except:
        return "Erro ao carregar enunciado"

def save_to_db(problems):
    """Insere os problemas coletados no MySQL."""
    conn = None
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        
        # O id_desafio será preenchido automaticamente pelo AUTO_INCREMENT do MySQL
        sql = "INSERT INTO desafios (titulo, enunciado, nivel) VALUES (%s, %s, %s)"

        print(f"Iniciando gravação de {len(problems)} desafios no banco: {db_config['database']}")
        for i, p in enumerate(problems, 1):
            print(f"[{i}/300] Processando: {p['title']}")
            enunciado = get_description(p['slug'])
            
            cursor.execute(sql, (p['title'], enunciado, p['level']))
            
            if i % 10 == 0:
                conn.commit()
            
            time.sleep(0.6) # Evita bloqueio do LeetCode
            
        conn.commit()
        print("\n✅ Carga finalizada com sucesso!")

    except mysql.connector.Error as err:
        print(f"❌ Erro no MySQL: {err}")
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == "__main__":
    lista_desafios = get_problems_by_difficulty()
    
    if len(lista_desafios) > 0:
        save_to_db(lista_desafios)
    else:
        print("Falha ao obter lista do LeetCode.")
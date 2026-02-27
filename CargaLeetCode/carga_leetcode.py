import os
import sys
import time


root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if root_path not in sys.path:
    sys.path.append(root_path)
from service.request_service import get_request, post_request
from repository.repository import close_db_connection, insert_into_table


API_URL = "https://leetcode.com/api/problems/all/"
HEADERS = {"User-Agent": "Mozilla/5.0"}

def get_problems_by_difficulty():
    print("Conectando ao LeetCode via API REST...")
    try:
        response = get_request(API_URL, headers=HEADERS)
        
        all_problems = response['stat_status_pairs']
        
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
        print(e)
        return []

def get_description(title_slug):
    """Busca o enunciado via GraphQL."""
    url = "https://leetcode.com/graphql"
    query = {
        "query": "query questionContent($titleSlug: String!) { question(titleSlug: $titleSlug) { content } }",
        "variables": {"titleSlug": title_slug}
    }
    try:
        r = post_request(url, json=query, headers=HEADERS)
        content = r['data']['question']['content']
        return content if content else "Sem enunciado disponível"
    except:
        return "Erro ao carregar enunciado"

def save_to_problems(problems):
    try:
        for i, p in enumerate(problems, 1):
            print(f"[{i}/{len(problems)}] Processando: {p['title']}")
            
            enunciado = get_description(p['slug']) 
            novo_desafio = {
                'titulo': p['title'], 
                'enunciado': enunciado, 
                'nivel': p['level']
            }
            insert_into_table('desafios', novo_desafio)
            time.sleep(0.6) 

    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
    finally:
        close_db_connection()

if __name__ == "__main__":
    lista_desafios = get_problems_by_difficulty()
    
    if len(lista_desafios) > 0:
        save_to_problems(lista_desafios)
    else:
        print("Falha ao obter lista do LeetCode.")
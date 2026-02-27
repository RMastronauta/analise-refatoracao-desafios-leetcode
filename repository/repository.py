import os
import time
import mysql.connector
from dotenv import load_dotenv

# Carrega antes de definir o db_config
load_dotenv()

db_config = {
    'host': os.getenv('DB_HOST'),
    'port': int(os.getenv('DB_PORT')),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD') or '',
    'database': os.getenv('DB_NAME'),
}

conn = None

def get_connection():
    global conn
    # Verifica se a conexão existe e se ainda está ativa
    if conn is None or not conn.is_connected():
        try:
            conn = mysql.connector.connect(**db_config)
        except mysql.connector.Error as err:
            print(f"Erro ao conectar: {err}")
            raise err
    return conn

def close_db_connection():
    global conn
    try:
        # Verifica se a conexão existe e está ativa
        if conn and conn.is_connected():
            conn.close()

        conn = None 
        
    except mysql.connector.Error as err:
        print(f"❌ Erro ao fechar a conexão: {err}")

def insert_into_table(table_name, data):
    connection = get_connection()
    cursor = connection.cursor()
    
    try:
        columns = ", ".join(data.keys())
        placeholders = ", ".join(["%s"] * len(data))
        values = tuple(data.values())

        sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
        
        cursor.execute(sql, values)
        connection.commit()
        print(f"✅ Inserido na tabela '{table_name}'")
        
    except mysql.connector.Error as err:
        print(f"❌ Erro ao inserir: {err}")
        connection.rollback()
    finally:
        cursor.close()
            

def select_into_table(table_name, campos=None, data=None, size = 300):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        filters = ""
        values = ()  # ✅ Inicializa values para evitar o erro se data for None
        
        if data is not None:
            # Transforma as chaves em "coluna1 = %s, coluna2 = %s"
            # Nota: usei AND caso você tenha mais de um filtro no futuro
            where_clause = " AND ".join([f"{k} = %s" for k in data.keys()])
            values = tuple(data.values())
            filters = f"WHERE {where_clause}"
            
        if campos:
            sql = f"SELECT {', '.join(campos)} FROM {table_name} {filters} LIMIT {size}"
        else:
            sql = f"SELECT * FROM {table_name} {filters} LIMIT {size}"
        
        # Agora values sempre existe, mesmo que seja uma tupla vazia ()
        cursor.execute(sql, values)
        result = cursor.fetchall()
        return result
        
    except mysql.connector.Error as err:
        print(f"❌ Erro ao selecionar: {err}")
        return []
    finally:
        cursor.close()
            
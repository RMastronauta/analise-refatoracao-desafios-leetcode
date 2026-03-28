import os
import mysql.connector
from dotenv import load_dotenv

from entity.resultado import Resultado


class Repository():
    def __init__(self):
        load_dotenv()
        self.db_config = {
        'host': os.getenv('DB_HOST'),
        'port': int(os.getenv('DB_PORT')),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD') or '',
        'database': os.getenv('DB_NAME'),
        }
        self.conn = None

    def get_connection(self):
        # Verifica se a conexão existe e se ainda está ativa
        if self.conn is None or not self.conn.is_connected():
            try:
                self.conn = mysql.connector.connect(**self.db_config)
            except mysql.connector.Error as err:
                print(f"Erro ao conectar: {err}")
                raise err

    def close_db_connection(self):
        try:
            # Verifica se a conexão existe e está ativa
            if self.conn and self.conn.is_connected():
                self.conn.close()

            self.conn = None
            
        except mysql.connector.Error as err:
            print(f"❌ Erro ao fechar a conexão: {err}")

    def insert_into_table(self, table_name, data):
        self.get_connection()
        cursor = self.conn.cursor()
        
        try:
            columns = ", ".join(data.keys())
            placeholders = ", ".join(["%s"] * len(data))
            values = tuple(data.values())

            sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
            
            cursor.execute(sql, values)
            self.conn.commit()
            print(f"✅ Inserido na tabela '{table_name}'")
            
        except mysql.connector.Error as err:
            print(f"❌ Erro ao inserir: {err}")
            self.conn.rollback()
        finally:
            cursor.close()
                

    def select_into_table(self, table_name, campos=None, data=None, filter=None, size = 100000):
        self.get_connection()
        cursor = self.conn.cursor(dictionary=True)
        
        try:
            filters = ""
            values = ()  # ✅ Inicializa values para evitar o erro se data for None
            
            if data is not None:
                where_clause = " AND ".join([f"{k} = %s" for k in data.keys()])
                values = tuple(data.values())
                filters = f"WHERE {where_clause}"
            
            if  filters == "" and filter is not None:
                filters = f"WHERE {filter}"

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
    
    def getResultadosBaselineNaoExecutados(self, tipo, size):
        self.get_connection()
        cursor = self.conn.cursor(dictionary=True)
        
        try:
            sql = ("SELECT BASELINE.id_resultado, BASELINE.id_desafio, BASELINE.id_modelo, BASELINE.codigo_fonte, BASELINE.linguagem FROM tcc_refatoracao_llm.resultados AS BASELINE "
                    "LEFT JOIN tcc_refatoracao_llm.resultados AS REFATORADO "
                    f"ON (REFATORADO.TIPO = '{tipo}' "
                        "AND REFATORADO.id_desafio = BASELINE.id_desafio "
                        "AND REFATORADO.id_modelo = BASELINE.id_modelo "
                        "AND REFATORADO.linguagem = BASELINE.linguagem) "
                    "WHERE BASELINE.tipo = 'baseline' "
                    "AND BASELINE.codigo_fonte is not null "
                    f"AND REFATORADO.id_resultado is null LIMIT {size}")
            
            # Agora values sempre existe, mesmo que seja uma tupla vazia ()
            cursor.execute(sql)
            result = cursor.fetchall()
            return result
            
        except mysql.connector.Error as err:
            print(f"❌ Erro ao selecionar: {err}")
            return []
        finally:
            cursor.close()

    def update_table(self, table_name, data, conditions):
        self.get_connection()
        cursor = self.conn.cursor()
        
        try:
            set_clause = ", ".join([f"{k} = %s" for k in data.keys()])
            where_clause = " AND ".join([f"{k} = %s" for k in conditions.keys()])
            
            values = tuple(data.values()) + tuple(conditions.values())
            
            sql = f"UPDATE {table_name} SET {set_clause} WHERE {where_clause}"
            cursor.execute(sql, values)
            self.conn.commit()
            print(f"✅ Atualizado na tabela '{table_name}'")
            
        except mysql.connector.Error as err:
            print(f"❌ Erro ao atualizar: {err}")
            self.conn.rollback()
        finally:
            cursor.close()

    def insert_resultados(self, resultados: list[Resultado]):
        self.get_connection()
        cursor = self.conn.cursor()
        
        try:
            quantidade_inserida = 0
            for resultado in resultados:
                # Verifica se já existe um resultado para esse desafio, modelo, tipo, linguagem e com o código_fonte não nulo nem vazio
                sql = "SELECT id_resultado FROM resultados WHERE id_desafio = %s AND id_modelo = %s AND tipo = %s AND linguagem = %s AND codigo_fonte IS NOT NULL AND codigo_fonte != ''"
                values = (resultado.id_desafio, resultado.id_modelo, resultado.tipo, resultado.linguagem)
                cursor.execute(sql, values) 
                existing = cursor.fetchone()
                if existing:
                    continue
                quantidade_inserida += 1
                sql = f"INSERT INTO resultados (id_desafio, id_modelo, tipo, codigo_fonte, linguagem) VALUES (%s, %s, %s, %s, %s)"
                values = (resultado.id_desafio, resultado.id_modelo, resultado.tipo, resultado.codigo_fonte, resultado.linguagem)
                cursor.execute(sql, values)

            
            self.conn.commit()
            print(f"✅ Inseridos {quantidade_inserida} resultados na tabela 'resultados'")
            
        except mysql.connector.Error as err:
            print(f"❌ Erro ao inserir resultados: {err}")
            self.conn.rollback()
        finally:
            cursor.close()


    def insert_resultado(self, resultado: Resultado):
        self.get_connection()
        cursor = self.conn.cursor()
        
        try:
            # Verifica se já existe um resultado para esse desafio, modelo, tipo, linguagem e com o código_fonte não nulo nem vazio
            sql = "SELECT id_resultado FROM resultados WHERE id_desafio = %s AND id_modelo = %s AND tipo = %s AND linguagem = %s AND codigo_fonte IS NOT NULL AND codigo_fonte != ''"
            values = (resultado.id_desafio, resultado.id_modelo, resultado.tipo, resultado.linguagem)
            cursor.execute(sql, values) 
            existing = cursor.fetchone()
            if existing:
                return
            
            sql = f"INSERT INTO resultados (id_desafio, id_modelo, tipo, codigo_fonte, linguagem) VALUES (%s, %s, %s, %s, %s)"
            values = (resultado.id_desafio, resultado.id_modelo, resultado.tipo, resultado.codigo_fonte, resultado.linguagem)
            cursor.execute(sql, values)

            
            self.conn.commit()
            print(f"✅ Resultado {resultado.id_desafio} para o tipo {resultado.linguagem}")
            
        except mysql.connector.Error as err:
            print(f"❌ Erro ao inserir resultados: {err}")
            self.conn.rollback()
        finally:
            cursor.close()
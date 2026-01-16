import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv


class DatabaseConnection:
    def __init__(self):
        load_dotenv()
        self.connection = None
        self.cursor = None
        self.connect()

    def connect(self):
        try:
            self.connection = mysql.connector.connect(
                host=os.getenv('DB_HOST', 'localhost'),
                port=os.getenv('DB_PORT', '3306'),
                database=os.getenv('DB_NAME', 'gestion_inventario'),
                user=os.getenv('DB_USER', 'root'),
                password=os.getenv('DB_PASSWORD', '')
            )
            if self.connection.is_connected():
                self.cursor = self.connection.cursor(dictionary=True)
                print("✅ Conexión exitosa a MariaDB")
        except Error as e:
            print(f"❌ Error en conexión: {e}")
            raise

    def execute_query(self, query, params=None):
        try:
            if self.cursor is None or self.connection is None:
                print("❌ No hay conexión a la base de datos")
                return False
            self.cursor.execute(query, params or ())
            self.connection.commit()
            return True
        except Error as e:
            print(f"❌ Error en consulta: {e}")
            return False

    def fetch_all(self, query, params=None):
        try:
            if self.cursor is None:
                print("❌ No hay conexión a la base de datos")
                return []
            self.cursor.execute(query, params or ())
            return self.cursor.fetchall()
        except Error as e:
            print(f"❌ Error al recuperar datos: {e}")
            return []

    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.connection and self.connection.is_connected():
            self.connection.close()

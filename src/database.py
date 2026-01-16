from mysql.connector import Error, pooling
import os
from dotenv import load_dotenv
import logging
from datetime import datetime
from typing import Optional

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='database.log'
)
logger = logging.getLogger('DatabaseConnection')


class DatabaseConnection:
    """
    Clase para gestionar la conexión y operaciones con la base de datos MariaDB/MySQL
    Utiliza pool de conexiones para mejor rendimiento y manejo de errores robusto
    """

    _instance = None
    _pool: Optional[pooling.MySQLConnectionPool] = None

    def __new__(cls):
        """Implementación de patrón Singleton para la conexión"""
        if cls._instance is None:
            cls._instance = super(DatabaseConnection, cls).__new__(cls)
            cls._instance._initialize_connection_pool()
        return cls._instance

    def _initialize_connection_pool(self):
        """Inicializa el pool de conexiones a la base de datos"""
        try:
            # Cargar variables de entorno
            load_dotenv()

            # Configuración del pool de conexiones
            db_config = {
                "host": os.getenv('DB_HOST', 'localhost'),
                "port": int(os.getenv('DB_PORT', '3306')),
                "database": os.getenv('DB_NAME', 'gestion_inventario'),
                "user": os.getenv('DB_USER', 'root'),
                "password": os.getenv('DB_PASSWORD', ''),
                "pool_name": "inventory_pool",
                "pool_size": 5,
                "pool_reset_session": True,
                "autocommit": True,
                "charset": 'utf8mb4',
                "collation": 'utf8mb4_unicode_ci'
            }

            # Crear pool de conexiones
            self._pool = pooling.MySQLConnectionPool(**db_config)
            logger.info("✅ Pool de conexiones creado exitosamente")
            print("✅ Pool de conexiones a base de datos inicializado")

        except Error as e:
            logger.error(f"❌ Error al crear pool de conexiones: {e}")
            print(f"❌ Error crítico al inicializar la base de datos: {e}")
            raise ConnectionError(
                f"No se pudo establecer conexión con la base de datos: {e}")
        except Exception as e:
            logger.error(f"❌ Error inesperado al inicializar pool: {e}")
            print(f"❌ Error crítico en configuración de base de datos: {e}")
            raise

    def _get_connection(self):
        """Obtiene una conexión del pool"""
        try:
            if self._pool is None:
                raise ConnectionError(
                    "El pool de conexiones no ha sido inicializado")
            connection = self._pool.get_connection()
            logger.debug("Obtenida conexión del pool")
            return connection
        except Error as e:
            logger.error(f"❌ Error al obtener conexión del pool: {e}")
            raise ConnectionError(
                f"No se pudo obtener una conexión de la base de datos: {e}")

    def execute_query(self, query, params=None):
        """
        Ejecuta una consulta de modificación (INSERT, UPDATE, DELETE)

        Args:
            query (str): Consulta SQL a ejecutar
            params (tuple, optional): Parámetros para la consulta

        Returns:
            bool: True si la consulta se ejecutó exitosamente, False en caso contrario
        """
        connection = None
        cursor = None
        try:
            connection = self._get_connection()
            cursor = connection.cursor(dictionary=True)

            start_time = datetime.now()
            cursor.execute(query, params or ())
            affected_rows = cursor.rowcount
            execution_time = (datetime.now() - start_time).total_seconds()

            logger.info(
                f"✅ Consulta ejecutada exitosamente: {query[:50]}... | Filas afectadas: {affected_rows} | Tiempo: {execution_time:.4f}s")

            return True

        except Error as e:
            logger.error(
                f"❌ Error en consulta: {e} | Query: {query} | Params: {params}")
            print(f"❌ Error en base de datos: {e}")
            return False
        finally:
            if cursor:
                cursor.close()
            if connection and connection.is_connected():
                connection.close()
                logger.debug("Conexión devuelta al pool")

    def fetch_all(self, query, params=None):
        """
        Ejecuta una consulta de selección y devuelve todos los resultados

        Args:
            query (str): Consulta SQL SELECT
            params (tuple, optional): Parámetros para la consulta

        Returns:
            list: Lista de diccionarios con los resultados
        """
        connection = None
        cursor = None
        try:
            connection = self._get_connection()
            cursor = connection.cursor(dictionary=True)

            start_time = datetime.now()
            cursor.execute(query, params or ())
            results = cursor.fetchall()
            execution_time = (datetime.now() - start_time).total_seconds()

            logger.info(
                f"✅ Consulta SELECT ejecutada: {query[:50]}... | Resultados: {len(results)} | Tiempo: {execution_time:.4f}s")

            return results

        except Error as e:
            logger.error(
                f"❌ Error en consulta SELECT: {e} | Query: {query} | Params: {params}")
            print(f"❌ Error en base de datos al recuperar datos: {e}")
            return []
        finally:
            if cursor:
                cursor.close()
            if connection and connection.is_connected():
                connection.close()
                logger.debug("Conexión devuelta al pool")

    def fetch_one(self, query, params=None):
        """
        Ejecuta una consulta de selección y devuelve un solo resultado

        Args:
            query (str): Consulta SQL SELECT
            params (tuple, optional): Parámetros para la consulta

        Returns:
            dict: Diccionario con el resultado o None si no hay resultados
        """
        connection = None
        cursor = None
        try:
            connection = self._get_connection()
            cursor = connection.cursor(dictionary=True)

            cursor.execute(query, params or ())
            result = cursor.fetchone()

            logger.debug(f"✅ Consulta fetch_one ejecutada: {query[:50]}...")

            return result

        except Error as e:
            logger.error(
                f"❌ Error en consulta fetch_one: {e} | Query: {query} | Params: {params}")
            print(f"❌ Error en base de datos al recuperar un registro: {e}")
            return None
        finally:
            if cursor:
                cursor.close()
            if connection and connection.is_connected():
                connection.close()
                logger.debug("Conexión devuelta al pool")

    def get_last_insert_id(self):
        """
        Obtiene el último ID insertado en la base de datos

        Returns:
            int: Último ID insertado
        """
        query = "SELECT LAST_INSERT_ID() as last_id"
        result = self.fetch_one(query)
        return result['last_id'] if result and 'last_id' in result else None

    def get_connection_status(self):
        """Verifica el estado de la conexión a la base de datos"""
        try:
            connection = self._get_connection()
            if connection.is_connected():
                db_info = connection.get_server_info()
                cursor = connection.cursor()
                cursor.execute("SELECT DATABASE();")
                record = cursor.fetchone()

                status = {
                    "status": "connected",
                    "server_version": db_info,
                    "database": record[0] if record else "Unknown",
                    "connection_id": connection.connection_id
                }

                cursor.close()
                connection.close()
                return status
            return {"status": "disconnected"}
        except Error as e:
            logger.error(f"❌ Error al verificar estado de conexión: {e}")
            return {"status": "error", "message": str(e)}

    def close_all_connections(self):
        """Cierra todas las conexiones del pool (para limpieza final)"""
        try:
            if self._pool:
                # Obtener conexiones activas y cerrarlas
                pool_size = self._pool._pool_size if self._pool._pool_size is not None else 5
                for _ in range(pool_size):
                    try:
                        conn = self._pool.get_connection()
                        if conn.is_connected():
                            conn.close()
                    except Exception:
                        pass

                logger.info(
                    "✅ Todas las conexiones del pool han sido cerradas")
                print("✅ Conexiones a base de datos cerradas correctamente")
        except Exception as e:
            logger.error(f"❌ Error al cerrar conexiones: {e}")

    def execute_transaction(self, queries, params_list=None):
        """
        Ejecuta múltiples consultas en una transacción

        Args:
            queries (list): Lista de consultas SQL
            params_list (list, optional): Lista de parámetros para cada consulta

        Returns:
            bool: True si todas las consultas se ejecutaron exitosamente
        """
        connection = None
        cursor = None
        try:
            connection = self._get_connection()
            connection.autocommit = False # type: ignore[attr-defined]
            cursor = connection.cursor(dictionary=True)

            for i, query in enumerate(queries):
                params = params_list[i] if params_list and i < len(
                    params_list) else None
                cursor.execute(query, params or ())

            connection.commit()
            logger.info(
                f"✅ Transacción ejecutada exitosamente con {len(queries)} consultas")
            return True

        except Error as e:
            if connection:
                connection.rollback()
            logger.error(f"❌ Error en transacción, rollback ejecutado: {e}")
            print(f"❌ Error en transacción de base de datos: {e}")
            return False
        finally:
            if cursor:
                cursor.close()
            if connection and connection.is_connected():
                connection.autocommit = True # type: ignore[attr-defined] # Restaurar autocommit
                connection.close()
                logger.debug(
                    "Conexión devuelta al pool después de transacción")

    def backup_database(self, backup_dir='backups'):
        """
        Crea un backup de la base de datos (requiere permisos adecuados)

        Args:
            backup_dir (str): Directorio para guardar el backup

        Returns:
            str: Ruta del archivo de backup creado o None si falla
        """
        try:
            # Crear directorio si no existe
            os.makedirs(backup_dir, exist_ok=True)

            # Generar nombre de archivo con timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(
                backup_dir, f"backup_inventario_{timestamp}.sql")

            # Obtener configuración de conexión
            db_config = {
                "host": os.getenv('DB_HOST', 'localhost'),
                "port": os.getenv('DB_PORT', '3306'),
                "database": os.getenv('DB_NAME', 'gestion_inventario'),
                "user": os.getenv('DB_USER', 'root'),
                "password": os.getenv('DB_PASSWORD', '')
            }

            # Construir comando mysqldump (requiere que mysqldump esté en PATH)
            password_flag = f"-p{db_config['password']}" if db_config['password'] else ""
            command = (
                f"mysqldump -h {db_config['host']} -P {db_config['port']} "
                f"-u {db_config['user']} {password_flag} "
                f"{db_config['database']} > {backup_file}"
            )

            # Ejecutar comando
            import subprocess
            result = subprocess.run(
                command, shell=True, capture_output=True, text=True)

            if result.returncode == 0:
                logger.info(f"✅ Backup creado exitosamente: {backup_file}")
                return backup_file
            else:
                logger.error(f"❌ Error al crear backup: {result.stderr}")
                return None

        except Exception as e:
            logger.error(f"❌ Error inesperado al crear backup: {e}")
            return None

    def __del__(self):
        """Método destructor para limpieza de recursos"""
        try:
            self.close_all_connections()
        except Exception:
            pass

# Función helper para inicialización rápida


def init_database():
    """Inicializa y verifica la conexión a la base de datos"""
    try:
        db = DatabaseConnection()
        status = db.get_connection_status()

        if status.get('status') == 'connected':
            print(f"   🗄️  Base de datos: {status.get('database')}")
            print(f"   🗄️  Base de datos: {status.get('database')}")
            print(f"   🖥️  Versión servidor: {status.get('server_version')}")
            print(f"   🔗  ID de conexión: {status.get('connection_id')}")
            return True
        else:
            print("❌ No se pudo conectar a la base de datos")
            return False

    except Exception as e:
        print(f"❌ Error al inicializar base de datos: {e}")
        return False


# Bloque de ejecución para pruebas directas
if __name__ == "__main__":
    print("🔍 Probando conexión a base de datos...")
    db = None
    success = init_database()

    if success:
        # Realizar consulta de prueba
        db = DatabaseConnection()
        test_query = "SELECT COUNT(*) as total FROM productos"
        result = db.fetch_one(test_query)

        if result:
            print(
                f"✅ Prueba exitosa: Hay {result['total']} productos en la base de datos")
        else:
            print("❌ No se pudieron recuperar datos de prueba")
    else:
        print("❌ La conexión a la base de datos falló")

    # Cerrar conexiones
    if db is not None:
        db.close_all_connections()
    print("👋 Conexiones cerradas")
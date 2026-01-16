import mysql.connector
from mysql.connector import Error


def probar_conexion():
    try:
        conexion = mysql.connector.connect(
            host='localhost',
            port=3308,  # <--- Agregamos esta línea
            database='gestion_inventario',
            user='root',
            password=''
        )

        if conexion.is_connected():
            print("✅ Conexión exitosa a MariaDB")
            cursor = conexion.cursor()

            # Consultar alertas críticas
            cursor.execute(
                "SELECT nombre, cantidad, nivel_alerta FROM vista_alertas_stock")
            alertas = cursor.fetchall()

            print("\n🚨 ALERTAS ACTIVAS:")
            for nombre, cantidad, nivel_alerta in alertas:
                print(f"- {nombre}: {cantidad} unidades ({nivel_alerta})")

            cursor.close()
            conexion.close()
            return True

    except Error as e:
        print(f"❌ Error en conexión: {e}")
        return False


# Ejecutar prueba
if __name__ == "__main__":
    probar_conexion()

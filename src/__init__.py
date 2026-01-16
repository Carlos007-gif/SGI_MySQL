"""
Sistema de Gestión de Inventario - Paquete Principal
Permite importar componentes directamente desde el paquete src
"""
from datetime import datetime
import logging
import platform
import sys
import mysql.connector
from .database import DatabaseConnection
from .gui import InventoryApp
from .utils import DataUtils, safe_int_conversion

__version__ = "1.1.0"
__author__ = "Carlos Daniel Martínez Reynoso"
__email__ = "carlosdaniel.martinezr@uanl.edu.mx"
__description__ = "Sistema de gestión de inventario para materiales de fotocopiado"
__license__ = "MIT"
__copyright__ = f"Copyright © 2024-{datetime.now().year} {__author__}"

# Función auxiliar para obtener información del sistema


def get_system_info():
    """Devuelve información del sistema para debugging"""
    return {
        "python_version": sys.version,
        "platform": platform.platform(),
        "processor": platform.processor(),
        "mysql_connector_version": mysql.connector.__version__,
        "application_version": __version__,
        "application_name": "Sistema de Gestión de Inventario",
        "developer": __author__,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }


# Inicializar logging para el paquete
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('system.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('SGI')

# Módulos exportados públicamente
__all__ = [
    "DatabaseConnection",
    "InventoryApp",
    "DataUtils",
    "safe_int_conversion",
    "get_system_info",
    "__version__",
    "__author__",
    "__email__"
]

# Mensaje de inicialización
logger.info(f"🚀 Sistema de Gestión de Inventario v{__version__} iniciado")
logger.info(f"👤 Desarrollado por: {__author__}")
logger.info(f"📧 Contacto: {__email__}")

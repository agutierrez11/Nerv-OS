import logging
import json
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler

class JsonFormatter(logging.Formatter):
    """
    Formateador para logs estructurados en JSON.
    Ideal para analisis posterior y observabilidad.
    """
    def format(self, record):
        log_record = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "funcName": record.funcName,
            "line": record.lineno
        }
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_record)

def setup_logger(name="nerv_os", log_file="logs/nerv_os.log"):
    """
    Configura un logger con rotacion de archivos y salida en JSON.
    """
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Handler para consola (Ultra-visible para el usuario)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG) # Forzar DEBUG en consola para ver todo
    console_formatter = logging.Formatter('\033[92m%(asctime)s\033[0m - \033[94m%(name)s\033[0m - \033[93m%(levelname)s\033[0m - %(message)s')
    console_handler.setFormatter(console_formatter)
    
    # Limpiar handlers previos si existen para evitar duplicados al recargar Streamlit
    if logger.hasHandlers():
        logger.handlers.clear()

    # Handler para archivo (JSON estructurado)
    file_handler = RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(JsonFormatter())

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    logger.info("="*50)
    logger.info("🚀 NERV OS ENGINE - SISTEMA OPERATIVO")
    logger.info("="*50)

    return logger

# Logger global
logger = setup_logger()

import time
import functools
import logging
import random
from typing import Callable, Any

logger = logging.getLogger("nerv_resilience")

def retry_with_backoff(retries: int = 3, backoff_in_seconds: int = 1):
    """
    Decorador para implementar Retry con Exponential Backoff.
    Especialmente util para APIs de LLMs y buscadores que sufren de Rate Limits.
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            x = 0
            while True:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if x == retries:
                        logger.error(f"Fallo critico tras {retries} reintentos en {func.__name__}: {e}")
                        raise
                    
                    # Logica de backoff exponencial con jitter para evitar colisiones
                    sleep = (backoff_in_seconds * 2 ** x + random.uniform(0, 1))
                    logger.warning(f"Error en {func.__name__} ({e}). Reintentando en {sleep:.2f}s... (Intento {x+1}/{retries})")
                    time.sleep(sleep)
                    x += 1
        return wrapper
    return decorator

class CircuitBreaker:
    """
    Implementacion simple de Circuit Breaker para evitar saturar APIs caidas.
    """
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failures = 0
        self.last_failure_time = 0
        self.state = "CLOSED" # CLOSED, OPEN, HALF-OPEN

    def call(self, func: Callable, *args, **kwargs):
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF-OPEN"
                logger.info("Circuit Breaker en estado HALF-OPEN. Probando recuperacion...")
            else:
                logger.error(f"Circuit Breaker esta OPEN. Saltando llamada a {func.__name__}")
                raise Exception(f"Circuit Breaker is OPEN for {func.__name__}")

        try:
            result = func(*args, **kwargs)
            if self.state == "HALF-OPEN":
                logger.info("Circuit Breaker vuelto a cerrar (CLOSED).")
                self.state = "CLOSED"
                self.failures = 0
            return result
        except Exception as e:
            self.failures += 1
            self.last_failure_time = time.time()
            if self.failures >= self.failure_threshold:
                self.state = "OPEN"
                logger.critical(f"Circuit Breaker se ha ABIERTO (OPEN) tras {self.failures} fallos.")
            raise e

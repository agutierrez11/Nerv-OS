import os
import time
from groq import Groq
import groq

class GroqRotator:
    """Manejador de API Keys de Groq con rotación automática anti-RateLimit."""
    
    def __init__(self, log_callback=None):
        self.log_callback = log_callback
        
        # Buscar todas las llaves en las variables de entorno
        self.keys = []
        if os.getenv("GROQ_API_KEY"): self.keys.append(os.getenv("GROQ_API_KEY"))
        if os.getenv("GROQ_API_KEY_2"): self.keys.append(os.getenv("GROQ_API_KEY_2"))
        if os.getenv("GROQ_API_KEY_3"): self.keys.append(os.getenv("GROQ_API_KEY_3"))
        
        # Fallback de seguridad si el usuario dijo tenerlas pero no están numeradas
        if not self.keys:
            raise ValueError("No se encontraron GROQ_API_KEYs en el archivo .env")
            
        self.current_index = 0
        self.client = Groq(api_key=self.keys[self.current_index])
        
    def _rotate_key(self):
        """Cambia a la siguiente llave en el arsenal."""
        self.current_index = (self.current_index + 1) % len(self.keys)
        self.client = Groq(api_key=self.keys[self.current_index])
        if self.log_callback:
            self.log_callback(f"⚠️ [ROTACIÓN ACTIVADA] Cambiando a API Key #{self.current_index + 1}")

    def create_completion(self, model, messages, temperature=0.7, max_retries=3):
        """Envuelve la llamada a Groq con manejo de errores y rotación."""
        attempts = 0
        while attempts < max_retries:
            try:
                # Intentamos la llamada con la llave actual
                response = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature
                )
                return response
            except groq.RateLimitError as e:
                attempts += 1
                if self.log_callback:
                    self.log_callback(f"⛔ Rate Limit con Key #{self.current_index + 1}. Intentando rotación...")
                
                # Si tenemos más de una llave, rotamos inmediatamente
                if len(self.keys) > 1:
                    self._rotate_key()
                else:
                    # Si solo hay 1 llave, hacemos un backoff (esperamos)
                    time.sleep(2)
            except Exception as e:
                # Cualquier otro error, lo lanzamos
                raise e
                
        # Si agotamos los intentos
        raise Exception(f"Fallo crítico: Rate Limits excedidos tras {max_retries} intentos con rotación.")

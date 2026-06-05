import os
import time
from openai import OpenAI
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

class HermesClient:
    """Manejador de API de Nous Research (Hermes)."""
    
    def __init__(self, log_callback=None):
        self.log_callback = log_callback
        self.api_key = os.getenv("HERMES_API_KEY")
        
        if not self.api_key:
            raise ValueError("No se encontró HERMES_API_KEY en el archivo .env")
            
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://inference-api.nousresearch.com/v1"
        )
        
    def create_completion(self, model, messages, temperature=0.7, max_retries=3):
        """Envuelve la llamada a la API de Nous con manejo de errores."""
        attempts = 0
        while attempts < max_retries:
            try:
                response = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature
                )
                return response
            except Exception as e:
                attempts += 1
                if self.log_callback:
                    self.log_callback(f"⚠️ Error con Hermes (Intento {attempts}/{max_retries}): {str(e)[:100]}")
                
                if attempts < max_retries:
                    time.sleep(2)
                else:
                    raise e

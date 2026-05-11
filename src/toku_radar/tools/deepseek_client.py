import os
import time
from openai import OpenAI
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

class DeepSeekClient:
    """Manejador de API de DeepSeek."""
    
    def __init__(self, log_callback=None):
        self.log_callback = log_callback
        self.api_key = os.getenv("DEEPSEEK_API_KEY")
        
        if not self.api_key:
            raise ValueError("No se encontró DEEPSEEK_API_KEY en el archivo .env")
            
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://api.deepseek.com"
        )
        
    def create_completion(self, model, messages, temperature=0.7, max_retries=3):
        """Envuelve la llamada a DeepSeek con manejo de errores."""
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
                    self.log_callback(f"⚠️ Error con DeepSeek (Intento {attempts}/{max_retries}): {str(e)[:100]}")
                
                if attempts < max_retries:
                    time.sleep(2)
                else:
                    raise e

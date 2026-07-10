import os
import time
import requests
import json
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

class MockMessage:
    def __init__(self, content):
        self.content = content

class MockChoice:
    def __init__(self, content):
        self.message = MockMessage(content)

class MockResponse:
    def __init__(self, content):
        self.choices = [MockChoice(content)]

class ClaudeClient:
    """Manejador de API de Anthropic Claude."""
    
    def __init__(self, log_callback=None):
        self.log_callback = log_callback
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            # Load API key from environment
            pass
            
    def create_completion(self, model, messages, temperature=0.3, max_retries=3):
        """Convierte los mensajes de OpenAI a Anthropic, llama a la API y devuelve un MockResponse compatible."""
        
        system_instruction = ""
        anthropic_messages = []
        
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            
            if role == "system":
                system_instruction += content + "\n"
            elif role == "user":
                anthropic_messages.append({"role": "user", "content": content})
            elif role == "assistant":
                anthropic_messages.append({"role": "assistant", "content": content})
                
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        payload = {
            "model": model,
            "max_tokens": 4000,
            "messages": anthropic_messages,
            "temperature": temperature
        }
        
        if system_instruction:
            payload["system"] = system_instruction.strip()
            
        attempts = 0
        while attempts < max_retries:
            try:
                response = requests.post(url, headers=headers, json=payload, timeout=45)
                if response.status_code == 200:
                    res_data = response.json()
                    try:
                        text_out = res_data["content"][0]["text"]
                        return MockResponse(text_out)
                    except (KeyError, IndexError) as e_parse:
                        raise ValueError(f"No se pudo parsear la respuesta de Claude: {res_data}. Error: {e_parse}")
                else:
                    raise ValueError(f"Error API Claude Status {response.status_code}: {response.text}")
            except Exception as e:
                attempts += 1
                if self.log_callback:
                    self.log_callback(f"⚠️ Error con Claude (Intento {attempts}/{max_retries}): {str(e)[:100]}")
                
                if attempts < max_retries:
                    time.sleep(2)
                else:
                    raise e

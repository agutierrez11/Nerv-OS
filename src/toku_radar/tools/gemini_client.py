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

class GeminiClient:
    """Manejador de API de Google Gemini (AI Studio)."""
    
    def __init__(self, log_callback=None):
        self.log_callback = log_callback
        # Check environment or fallback to hardcoded from test scripts if necessary
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            # Fallback to the known working developer key
            self.api_key = "AIzaSyBR_oEOiFqIr-Rw1b1V_dNRkolKl-piRME"
            
    def create_completion(self, model, messages, temperature=0.3, max_retries=3):
        """Convierte los mensajes de OpenAI a Gemini, llama a la API y devuelve un MockResponse compatible."""
        
        # Mapping OpenAI formats to Gemini
        system_instruction = ""
        contents = []
        
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            
            if role == "system":
                system_instruction += content + "\n"
            elif role == "user":
                contents.append({"role": "user", "parts": [{"text": content}]})
            elif role == "assistant":
                contents.append({"role": "model", "parts": [{"text": content}]})
                
        # API URL (we use v1beta as it supports systemInstruction)
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}"
        headers = {"Content-Type": "application/json"}
        
        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature
            }
        }
        
        if system_instruction:
            payload["systemInstruction"] = {
                "parts": [{"text": system_instruction.strip()}]
            }
            
        attempts = 0
        while attempts < max_retries:
            try:
                response = requests.post(url, headers=headers, json=payload, timeout=45)
                if response.status_code == 200:
                    res_data = response.json()
                    # Extract generated text safely
                    try:
                        text_out = res_data['candidates'][0]['content']['parts'][0]['text']
                        return MockResponse(text_out)
                    except (KeyError, IndexError) as e_parse:
                        raise ValueError(f"No se pudo parsear la respuesta de Gemini: {res_data}. Error: {e_parse}")
                else:
                    raise ValueError(f"Error API Gemini Status {response.status_code}: {response.text}")
            except Exception as e:
                attempts += 1
                if self.log_callback:
                    self.log_callback(f"⚠️ Error con Gemini (Intento {attempts}/{max_retries}): {str(e)[:100]}")
                
                if attempts < max_retries:
                    time.sleep(2)
                else:
                    raise e

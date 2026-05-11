import os
import httpx
from dotenv import load_dotenv
from pathlib import Path

# Cargar .env
BASE_DIR = Path(__file__).parent.parent.parent.parent
load_dotenv(BASE_DIR.parent / ".env")

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not url or not key:
    print("❌ Error: SUPABASE_URL o SUPABASE_SERVICE_ROLE_KEY no encontrados.")
    exit(1)

def test_rest_api():
    print(f"Probando API REST: {url}/rest/v1/")
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}"
    }
    
    try:
        # Intentar leer de la tabla 'todos' que vimos en tu ejemplo
        response = httpx.get(f"{url}/rest/v1/todos", headers=headers)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print("✅ Conexión exitosa a la tabla 'todos'.")
            print(f"Data: {response.json()}")
        else:
            print(f"⚠️ Error: {response.text}")
            
        # Intentar ver la versión de la DB o algo genérico
        response = httpx.get(f"{url}/rest/v1/", headers=headers)
        if response.status_code == 200:
            print("✅ API REST expuesta correctamente.")
            
    except Exception as e:
        print(f"❌ Error de conexión: {e}")

if __name__ == "__main__":
    test_rest_api()

import os
import httpx
from dotenv import load_dotenv
from pathlib import Path

# Cargar .env
BASE_DIR = Path(__file__).parent.parent.parent.parent
load_dotenv(BASE_DIR.parent / ".env")

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

def inspect_tables():
    tables = ["empresas_v3", "knowledge_base", "logs_busquedas"]
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}"
    }
    
    for table in tables:
        print(f"\n--- Analizando tabla: {table} ---")
        try:
            # Pedir 1 registro para ver la estructura
            response = httpx.get(f"{url}/rest/v1/{table}?limit=1", headers=headers)
            if response.status_code == 200:
                data = response.json()
                if data:
                    print(f"Columnas detectadas: {list(data[0].keys())}")
                else:
                    print("Tabla vacia, no se pueden detectar columnas por datos.")
            else:
                print(f"Error {response.status_code}: {response.text}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    inspect_tables()

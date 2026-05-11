import os
import httpx
import json
from dotenv import load_dotenv
from pathlib import Path

# Cargar .env con ruta absoluta
ENV_PATH = Path(r"C:\Users\Antonio\.gemini\antigravity\scratch\.env")
load_dotenv(ENV_PATH)

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

def get_sample_data():
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}"
    }
    try:
        response = httpx.get(f"{url}/rest/v1/empresas_v3?limit=1", headers=headers)
        if response.status_code == 200:
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"Error: {response.status_code}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    get_sample_data()

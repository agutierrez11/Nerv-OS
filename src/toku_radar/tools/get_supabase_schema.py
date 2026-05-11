import os
import httpx
from dotenv import load_dotenv
from pathlib import Path

# Cargar .env
BASE_DIR = Path(__file__).parent.parent.parent.parent
load_dotenv(BASE_DIR.parent / ".env")

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

def get_db_schema():
    print(f"Consultando esquema OpenAPI en: {url}")
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}"
    }
    
    try:
        # El endpoint raíz /rest/v1/ suele devolver el esquema OpenAPI si está habilitado
        response = httpx.get(f"{url}/rest/v1/", headers=headers)
        if response.status_code == 200:
            schema = response.json()
            print("Conexion exitosa. Listando definiciones encontradas:")
            if "definitions" in schema:
                for table_name in schema["definitions"].keys():
                    print(f"- Tabla detectada: {table_name}")
            else:
                print("No se encontraron definiciones de tablas en el esquema.")
        else:
            print(f"Error (Status {response.status_code}): {response.text}")
            
    except Exception as e:
        print(f"Error de conexion: {e}")

if __name__ == "__main__":
    get_db_schema()

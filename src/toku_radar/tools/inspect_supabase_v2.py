import os
from supabase import create_client, Client
from dotenv import load_dotenv
from pathlib import Path

# Cargar .env
BASE_DIR = Path(__file__).parent.parent.parent.parent
load_dotenv(BASE_DIR.parent / ".env")

url = os.getenv("SUPABASE_URL")
# Usar SERVICE_ROLE_KEY para inspección total
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not url or not key:
    print("❌ Error: SUPABASE_URL o SUPABASE_SERVICE_ROLE_KEY no encontrados.")
    exit(1)

supabase: Client = create_client(url, key)

def inspect_db():
    print(f"🔍 Inspeccionando Supabase con Service Role: {url}")
    try:
        # Intentar obtener la lista de tablas a través de SQL directo si es posible
        # O simplemente probando tablas comunes
        print("\n--- Buscando tablas ---")
        
        # Intentar listar tablas ejecutando una consulta SQL simple (si hay permisos)
        # Como no tenemos acceso directo a ejecutar SQL arbitrario vía SDK sin una función RPC,
        # probaremos las tablas que mencionaste o comunes.
        
        tables_to_check = ["todos", "profiles", "users", "dossiers", "companies"]
        for table in tables_to_check:
            try:
                res = supabase.table(table).select("count", count="exact").limit(1).execute()
                print(f"✅ Tabla encontrada: '{table}' (Filas: {res.count})")
            except Exception as e:
                if "relation" in str(e) and "does not exist" in str(e):
                    print(f"ℹ️ La tabla '{table}' no existe.")
                else:
                    print(f"⚠️ Error al consultar '{table}': {e}")
    except Exception as e:
        print(f"❌ Error crítico: {e}")

if __name__ == "__main__":
    inspect_db()

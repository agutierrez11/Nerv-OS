import os
from supabase import create_client, Client
from dotenv import load_dotenv
from pathlib import Path

# Cargar .env
BASE_DIR = Path(__file__).parent.parent.parent.parent
load_dotenv(BASE_DIR.parent / ".env")

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

if not url or not key:
    print("❌ Error: SUPABASE_URL o SUPABASE_KEY no encontrados.")
    exit(1)

supabase: Client = create_client(url, key)

def inspect_db():
    print(f"🔍 Inspeccionando Supabase: {url}")
    try:
        # Intentar listar tablas a través de una consulta RPC o consultando una tabla común
        # Nota: Con la Anon Key, solo podemos ver lo que el RLS permite.
        # Pero podemos intentar listar tablas del esquema public si hay permisos.
        
        # Intentamos una consulta genérica para ver qué responde
        response = supabase.table("dossiers").select("*").limit(1).execute()
        print("✅ Tabla 'dossiers' encontrada.")
        print(response.data)
    except Exception as e:
        if "relation \"public.dossiers\" does not exist" in str(e):
            print("ℹ️ La tabla 'dossiers' no existe aún.")
        else:
            print(f"⚠️ Error al consultar 'dossiers': {e}")

    try:
        # Consultar perfiles o tablas de sistema si es posible
        print("\n--- Intentando listar tablas existentes ---")
        # En Supabase, a veces podemos usar rpc si hay funciones definidas
        # Pero por ahora, probaremos nombres comunes
        common_tables = ["users", "profiles", "logs", "companies", "leads", "tasks"]
        for table in common_tables:
            try:
                supabase.table(table).select("count", count="exact").limit(1).execute()
                print(f"✅ Tabla encontrada: '{table}'")
            except Exception:
                pass
    except Exception as e:
        print(f"❌ Error crítico: {e}")

if __name__ == "__main__":
    inspect_db()

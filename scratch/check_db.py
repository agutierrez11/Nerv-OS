import os
from supabase import create_client

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(url, key)

sql = """
CREATE TABLE IF NOT EXISTS brief_feedback (
  id SERIAL PRIMARY KEY,
  company_name TEXT,
  campo TEXT,
  valor_original JSONB,
  valor_editado JSONB,
  rating INTEGER,
  feedback_text TEXT,
  model_info JSONB,
  created_at TIMESTAMP DEFAULT NOW()
);
"""

# Usando el endpoint de rpc para ejecutar SQL (si está habilitado) 
# o intentando una inserción de prueba para verificar existencia
try:
    # Nota: En Supabase no se puede ejecutar SQL arbitrario vía API REST fácilmente 
    # sin una función RPC. Intentaremos crearla o simplemente dejar el código listo 
    # para recibir datos, lo cual creará la tabla si usamos una herramienta de migración.
    # Por ahora, asumiremos que el usuario puede pegarlo en el Dashboard o intentaremos 
    # una inserción que falle si la tabla no existe para confirmar.
    print("Intentando verificar tabla brief_feedback...")
    supabase.table("brief_feedback").select("*").limit(1).execute()
    print("La tabla ya existe.")
except Exception as e:
    print(f"La tabla no parece existir o hay un error: {e}")
    print("IMPORTANTE: Por favor, pega el SQL sugerido en el SQL Editor de tu Supabase Dashboard.")

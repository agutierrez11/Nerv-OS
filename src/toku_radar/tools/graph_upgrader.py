import os
import re
from pathlib import Path
from dotenv import load_dotenv
from groq import Groq

# Configuración de rutas
BASE_DIR = Path(__file__).parent.parent.parent.parent
OUTPUT_DIR = BASE_DIR / "output"
load_dotenv(BASE_DIR.parent / ".env")

# Intentar cargar una de las llaves disponibles
api_key = os.getenv("GROQ_API_KEY") or os.getenv("GROQ_API_KEY_1") or os.getenv("GROQ_API_KEY_2")
if not api_key:
    raise Exception("No se encontró GROQ_API_KEY en el .env")

client = Groq(api_key=api_key)

def upgrade_file(file_path):
    print(f"Refinando formato para Cosma: {file_path.name}")
    content = file_path.read_text(encoding="utf-8")
    
    # Extraer metadatos con IA rápida
    prompt = f"""
    Analiza el siguiente dossier de ventas y extrae:
    1. Empresa (Nombre limpio)
    2. Sector (Elegir uno de: Retail, Fintech, Ecommerce, Logística, Salud)
    3. 3-5 Tags técnicos (Dolores o Tecnologías)
    
    DOSSIER:
    {content[:1500]}
    
    Responde ÚNICAMENTE en este formato YAML EXACTO (sin texto antes ni después):
    ---
    title: "Nombre de la Empresa"
    type: "Sector"
    tags: ["Tag1", "Tag2"]
    id: "{file_path.stem.lower()}"
    ---
    """
    
    try:
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )
        yaml_metadata = completion.choices[0].message.content.strip()
        
        # Limpiar cualquier residuo de texto que no sea YAML
        if "---" in yaml_metadata:
            parts = yaml_metadata.split("---")
            if len(parts) >= 3:
                yaml_metadata = "---" + parts[1] + "---"

        # Quitar cualquier texto antes del YAML en el contenido original si ya lo tiene, o simplemente usar el nuevo
        # En este caso, buscaremos el contenido REAL del dossier (después del título #)
        main_content_match = re.search(r'(# .*)', content, re.DOTALL)
        main_content = main_content_match.group(1) if main_content_match else content
        
        # Inyectar Wikilinks básicos
        common_entities = ["CFO", "CEO", "Finanzas", "Pagos", "Ecommerce", "Retail", "México", "LATAM", "DISC", "ROI"]
        for entity in common_entities:
            main_content = re.sub(rf'\b{entity}\b', f'[[{entity}]]', main_content)
            
        # Unir YAML y contenido - YAML DEBE ESTAR EN LINEA 1
        final_output = f"{yaml_metadata}\n\n{main_content}"
        file_path.write_text(final_output, encoding="utf-8")
        return True
    except Exception as e:
        print(f"Error procesando {file_path.name}: {e}")
        return False

def run_upgrade():
    files = list(OUTPUT_DIR.glob("*.md"))
    success_count = 0
    for f in files:
        if f.name.startswith("NERV") or f.name.startswith("knowledge"): continue
        if upgrade_file(f):
            success_count += 1
    
    # Crear Master Index
    master_index = "# 🕸️ NERV MASTER KNOWLEDGE GRAPH\n\n"
    master_index += "## 🏢 EMPRESAS INVESTIGADAS\n"
    for f in files:
        if f.name.startswith("NERV") or f.name.startswith("knowledge"): continue
        master_index += f"- [[{f.stem}]]\n"
    
    (OUTPUT_DIR / "NERV_MASTER_GRAPH.md").write_text(master_index, encoding="utf-8")
    print(f"✅ Proceso completado. {success_count} archivos actualizados.")

if __name__ == "__main__":
    run_upgrade()

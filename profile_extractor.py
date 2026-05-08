import sys
import os
import json
from groq import Groq
from dotenv import load_dotenv

# 1. Rutas Dinámicas (Portabilidad total)
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(PROJECT_ROOT, "src"))

from toku_radar.tools.search import SerperSearch
from toku_radar.tools.firecrawl_tool import FirecrawlTool

# Cargar .env de forma dinámica
load_dotenv() # Busca el .env en la carpeta actual

class CLevelExtractor:
    def __init__(self):
        self.searcher = SerperSearch()
        self.firecrawl = FirecrawlTool()
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    def extract_identity(self, name, company, role_description="CFO / Director"):
        print(f"--- Iniciando Prospección Forense: {name} ({company}) ---")
        
        # Búsqueda Multi-Fuente
        queries = {
            "linkedin": f'site:linkedin.com/in/ "{name}" "{company}"',
            "favikon": f'site:favikon.com "{name}" ranking',
            "evidence": f'"{name}" "{company}" entrevista declaracion reto 2024'
        }
        
        raw_data = ""
        for key, q in queries.items():
            raw_data += f"\n--- {key.upper()} ---\n{self.searcher._query(q)}"

        # 2. Prompter con Filtro de Alucinación e Industry Fallback
        prompt = f"""
        Eres un Analista Forense. Tu misión es modelar la identidad de {name}.
        
        Si no hay suficiente información cruda, utiliza el 'Perfil Promedio de Industria' para el cargo: {role_description}.
        
        ESTRUCTURA REQUERIDA (JSON):
        {{
          "c_level_identity": {{
            "name": "{name}",
            "favikon_rank": "Ranking o 'Promedio Industria'",
            "authority_topics": ["Tema 1", "Tema 2"],
            "crystal_disc": "Perfil DISC detectado o promedio (D, I, S, C)",
            "evidence_justification": "Cita textual o fuente que justifica este perfil"
          }},
          "decision_filters": {{
            "primary_motivator": "Motivador principal",
            "primary_fear": "Miedo principal",
            "evidence_quotes": {{
                "motivator_source": "Cita o link de evidencia",
                "fear_source": "Cita o link de evidencia"
            }},
            "decision_speed": "Rápida/Lenta"
          }}
        }}
        
        DATOS CRUDOS:
        {raw_data}
        
        Responde SOLO con el JSON.
        """
        
        resp = self.client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        return json.loads(resp.choices[0].message.content)

if __name__ == "__main__":
    extractor = CLevelExtractor()
    try:
        # Prueba con un perfil real para ver las "Evidence Quotes"
        identity = extractor.extract_identity("Adolfo Babatz", "Clip", "CEO / Fintech Founder")
        print("\n[ IDENTIDAD MAESTRA CON FILTRO DE ALUCINACIÓN ]")
        print(json.dumps(identity, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"Error: {e}")

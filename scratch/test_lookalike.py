import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Configurar paths
CURRENT_DIR = Path(__file__).parent.absolute()
PROJECT_ROOT = CURRENT_DIR.parent
sys.path.append(str(PROJECT_ROOT))
sys.path.append(str(PROJECT_ROOT / "src"))

load_dotenv()

from core.lookalike_engine import LookalikeCrew

def test_vector_direct():
    print("\n--- TEST VECTOR 1: Lookalike Directo (Base: Clip) ---")
    try:
        from core.lookalike_engine import ICPExtractorAgent, _llm_call
        print("Testing ICPExtractorAgent raw LLM call:")
        extractor = ICPExtractorAgent()
        prompt = f"""Analiza esta empresa y extrae su perfil ICP (Ideal Customer Profile).
Empresa: Clip
Sector declarado: Fintech
Contexto adicional: 

Devuelve SOLO un JSON con este esquema:
```json
{{
  "sector": "...",
  "tamaño": "startup|pyme|midmarket|enterprise",
  "señales_clave": ["señal1", "señal2"],
  "queries_busqueda": ["query para Serper 1", "query para Serper 2"],
  "palabras_clave_negativas": ["evitar1", "evitar2"]
}}
```"""
        raw_resp = _llm_call(
            "Eres un experto en GTM y análisis de ICP. Responde SOLO en JSON válido.",
            prompt
        )
        print(f"Raw Response: {raw_resp}")
        
        crew = LookalikeCrew(
            mode="direct",
            empresa_base="Clip",
            sector="Fintech",
            pitch="Terminales de pago y cobros recurrentes",
            max_results=5
        )
        print("Ejecutando enjambre de lookalikes directo...")
        results = crew.run()
        print("Resultados Obtenidos:")
        for idx, r in enumerate(results):
            print(f"{idx+1}. {r.get('empresa')} (Fit Score: {r.get('score')})")
            print(f"   Razón: {r.get('razon')}")
            print(f"   DM Sugerido: {r.get('decision_maker_sugerido')}")
    except Exception as e:
        print(f"Error: {e}")

def test_vector_competitor():
    print("\n--- TEST VECTOR 2: Interceptación de Competidores (Base: Swan) ---")
    try:
        crew = LookalikeCrew(
            mode="competitor",
            competitor_url="https://gtmagent.getswan.com",
            max_results=5
        )
        print("Ejecutando interceptación de competidor...")
        results = crew.run()
        print("Resultados Obtenidos:")
        for idx, r in enumerate(results):
            print(f"{idx+1}. {r.get('empresa')} (Fit Score: {r.get('score')})")
            print(f"   Razón: {r.get('razon')}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_vector_direct()
    test_vector_competitor()

import sys
import os
from pathlib import Path

# Agregar el path del proyecto
CURRENT_DIR = Path(__file__).parent.absolute()
PROJECT_ROOT = CURRENT_DIR.parent
sys.path.append(str(PROJECT_ROOT))
sys.path.append(str(PROJECT_ROOT / "src"))

from src.toku_radar.crew import NervCrew
from core.logger import logger

def test():
    print("--- INICIANDO PRUEBA TECNICA DE NERV OS ---")
    try:
        # Probamos con datos de ejemplo para el LAB
        crew = NervCrew(
            empresa="Walmart Mexico",
            sector="Retail",
            pitch="SaaS de Conciliacion Bancaria",
            vendedor="FintechPro",
            url_cliente="https://www.walmartmexico.com"
        )
        
        print("Lanzando kickoff...")
        resultado = crew.kickoff()
        
        print("\nPRUEBA EXITOSA!")
        print("-" * 30)
        print(resultado[:500] + "...")
        print("-" * 30)
        
    except Exception as e:
        print(f"\nERROR DETECTADO: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test()

import sys
import os
import re
from pathlib import Path
from dotenv import load_dotenv

# --- CONFIGURACIÓN DE RUTAS PARA NERV OS ---
ROOT_DIR = Path(__file__).parent.absolute()
SRC_DIR = ROOT_DIR / "src"

# Inyectar rutas en sys.path para que los agentes se encuentren entre sí
for path in [str(ROOT_DIR), str(SRC_DIR)]:
    if path not in sys.path:
        sys.path.insert(0, path)

# Ahora podemos importar los módulos de toku_radar con seguridad
try:
    from toku_radar.crew import TokuCrew
except ImportError:
    # Fallback por si acaso
    from src.toku_radar.crew import TokuCrew

load_dotenv(dotenv_path=str(ROOT_DIR / ".env"))

class TokuDossierEngine:
    def __init__(self):
        """Orquestador compatible con la arquitectura NERV Swarm."""
        pass

    def generate_dossier(self, empresa: str, sector: str, pitch: str, contexto_crm: str = "") -> str:
        """Genera el dossier usando la Swarm Intelligence de TokuCrew."""
        print(f"\n[NERV OS] Desplegando enjambre de agentes para: {empresa}")
        
        # Iniciar la tripulación (Crew)
        crew = TokuCrew(empresa, sector, pitch, prior_knowledge=contexto_crm, log_callback=print)
        
        # Ejecutar el Kickoff del Enjambre
        dossier_final = crew.kickoff()
        
        return dossier_final

    def safe_filename(self, empresa: str) -> str:
        """Limpia el nombre de la empresa para guardarlo como archivo."""
        return re.sub(r'[^\w\-]', '_', empresa).strip('_')

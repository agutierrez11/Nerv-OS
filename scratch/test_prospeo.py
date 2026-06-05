import sys
from pathlib import Path

# Configurar rutas
ROOT_DIR = Path(__file__).parent.parent.absolute()
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import os
import requests
from dotenv import load_dotenv
load_dotenv()

from src.toku_radar.tools.prospeo_client import prospeo_enrich_person

def test_prospeo():
    print("Testing Prospeo Client...")
    print("API Key exists:", bool(os.getenv("PROSPEO_API_KEY")))
    
    # URL de prueba (usaremos una pública o cualquiera de prueba)
    test_url = "https://www.linkedin.com/in/williamhgates"
    
    try:
        # Probamos el método .run() que usa crew.py
        result = prospeo_enrich_person.run(test_url)
        print("Result from prospeo_enrich_person.run():", result)
    except Exception as e:
        print("Exception occurred running tool:", e)

if __name__ == "__main__":
    test_prospeo()

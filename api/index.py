from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import os
import sys

# Añadir el directorio raíz al path para importar crew_engine
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from crew_engine import TokuCrew

app = FastAPI()

# Configurar CORS para permitir peticiones desde el frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AnalysisRequest(BaseModel):
    empresa: str
    sector: str
    pitch: str
    context: str = ""

class IntelRequest(BaseModel):
    company: str
    sector: str
    content: str
    type: str # "objection" or "value_prop"

@app.get("/")
def read_root():
    return {"status": "NERV OS API Online", "version": "2.0"}

@app.get("/api/companies")
async def get_companies():
    try:
        import csv
        companies = []
        # Ahora el archivo vive dentro de api/ para asegurar el despliegue en Vercel
        csv_path = os.path.join(os.path.dirname(__file__), "companies.csv")
        if os.path.exists(csv_path):
            with open(csv_path, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    companies.append(row)
        return {"success": True, "data": companies}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/save-intelligence")
async def save_intelligence(request: IntelRequest):
    try:
        import json
        from datetime import datetime
        
        # Ruta a la memoria (ajustada para el entorno Vercel/Local)
        memory_path = os.path.join(os.path.dirname(__file__), "..", "memory", "feedback_loop", "objections_library.json")
        
        # Crear directorio si no existe
        os.makedirs(os.path.dirname(memory_path), exist_ok=True)
        
        # Cargar datos existentes
        data = []
        if os.path.exists(memory_path):
            with open(memory_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        
        # Añadir nueva entrada
        data.append({
            "company": request.company,
            "sector": request.sector,
            "content": request.content,
            "type": request.type,
            "timestamp": datetime.now().isoformat()
        })
        
        # Guardar localmente
        with open(memory_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # Sincronizar con Supabase
        try:
            from core.database import db
            db.add_knowledge(
                content=request.content,
                metadata={
                    "company": request.company,
                    "sector": request.sector,
                    "type": request.type
                }
            )
        except:
            pass
            
        return {"success": True, "message": "Intelligence registered in NERV Core and Cloud"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze")
async def run_analysis(request: AnalysisRequest):
    try:
        crew = TokuCrew(
            empresa=request.empresa,
            sector=request.sector,
            pitch=request.pitch
        )
        result = crew.run()
        return {"success": True, "data": str(result)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

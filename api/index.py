from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import os
import sys

# Añadir el directorio raíz al path para importar crew_engine
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

# Eliminamos la importación global para evitar colapsos al arrancar
# from crew_engine import TokuCrew

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

@app.get("/api/health")
def health_check():
    return {
        "status": "online",
        "keys_detected": {
            "GROQ": bool(os.getenv("GROQ_API_KEY")),
            "SERPER": bool(os.getenv("SERPER_API_KEY")),
            "SUPABASE": bool(os.getenv("SUPABASE_URL")),
            "FIRE": bool(os.getenv("FIRECRAWL_API_KEY"))
        }
    }

# BASE DE DATOS ESTRATÉGICA (HARDCODED PARA VERCEL)
COMPANIES_DATABASE = [
    {"sector": "Ecommerce", "empresa": "Under Armour", "pitch_principal": "Orquestación de Pagos + Recurrencia"},
    {"sector": "Ecommerce", "empresa": "Nike", "pitch_principal": "Orquestación de Pagos + Recurrencia"},
    {"sector": "Ecommerce", "empresa": "Adidas", "pitch_principal": "Orquestación de Pagos + Recurrencia"},
    {"sector": "Ecommerce", "empresa": "AutoZone", "pitch_principal": "Orquestación de Pagos + Recurrencia"},
    {"sector": "Ecommerce", "empresa": "InnovaSport", "pitch_principal": "Orquestación de Pagos + Recurrencia"},
    {"sector": "Ecommerce", "empresa": "Grupo Martí", "pitch_principal": "Orquestación de Pagos + Recurrencia"},
    {"sector": "Ecommerce", "empresa": "Ben&Frank", "pitch_principal": "Orquestación de Pagos + Recurrencia"},
    {"sector": "Ecommerce", "empresa": "Pandora", "pitch_principal": "Orquestación de Pagos + Recurrencia"},
    {"sector": "Ecommerce", "empresa": "Decathlon", "pitch_principal": "Orquestación de Pagos + Recurrencia"},
    {"sector": "Ecommerce", "empresa": "Samsung Electronics", "pitch_principal": "Orquestación de Pagos + Recurrencia"},
    {"sector": "Ecommerce", "empresa": "Justo", "pitch_principal": "Orquestación de Pagos + Recurrencia"},
    {"sector": "Ecommerce", "empresa": "Luuna", "pitch_principal": "Orquestación de Pagos + Recurrencia"},
    {"sector": "Ecommerce", "empresa": "Omnilife", "pitch_principal": "Orquestación de Pagos + Recurrencia"},
    {"sector": "Ecommerce", "empresa": "Platanomelon", "pitch_principal": "Orquestación de Pagos + Recurrencia"},
    {"sector": "Ecommerce", "empresa": "HoliHerb", "pitch_principal": "Orquestación de Pagos + Recurrencia"},
    {"sector": "Goods", "empresa": "Coca Cola Femsa", "pitch_principal": "Digitalización de Cobranza + BNPL"},
    {"sector": "Goods", "empresa": "Arca Continental", "pitch_principal": "Digitalización de Cobranza + BNPL"},
    {"sector": "Goods", "empresa": "Bepensa", "pitch_principal": "Digitalización de Cobranza + BNPL"},
    {"sector": "Goods", "empresa": "Danone", "pitch_principal": "Digitalización de Cobranza + BNPL"},
    {"sector": "Goods", "empresa": "Alpura", "pitch_principal": "Digitalización de Cobranza + BNPL"},
    {"sector": "Goods", "empresa": "Grupo Lala", "pitch_principal": "Digitalización de Cobranza + BNPL"},
    {"sector": "Goods", "empresa": "La Costeña", "pitch_principal": "Digitalización de Cobranza + BNPL"},
    {"sector": "Goods", "empresa": "Grupo KUO", "pitch_principal": "Digitalización de Cobranza + BNPL"},
    {"sector": "Goods", "empresa": "Kimberly Clark de Mexico", "pitch_principal": "Digitalización de Cobranza + BNPL"},
    {"sector": "Goods", "empresa": "Nestlé", "pitch_principal": "Digitalización de Cobranza + BNPL"},
    {"sector": "Goods", "empresa": "Grupo El Zorro", "pitch_principal": "Digitalización de Cobranza + BNPL"},
    {"sector": "Goods", "empresa": "Productos de Consumo Z", "pitch_principal": "Digitalización de Cobranza + BNPL"},
    {"sector": "Goods", "empresa": "Grupo Scorpion", "pitch_principal": "Digitalización de Cobranza + BNPL"},
    {"sector": "Goods", "empresa": "Comex", "pitch_principal": "Digitalización de Cobranza + BNPL"},
    {"sector": "Goods", "empresa": "3M México", "pitch_principal": "Digitalización de Cobranza + BNPL"},
    {"sector": "Health", "empresa": "Salud Digna", "pitch_principal": "Discovery de Pagos"},
    {"sector": "Health", "empresa": "Hospital Angeles", "pitch_principal": "Discovery de Pagos"},
    {"sector": "Health", "empresa": "Hospital ABC", "pitch_principal": "Discovery de Pagos"},
    {"sector": "Health", "empresa": "CHOPO", "pitch_principal": "Discovery de Pagos"},
    {"sector": "Health", "empresa": "Hospital Español", "pitch_principal": "Discovery de Pagos"},
    {"sector": "Health", "empresa": "TecSalud", "pitch_principal": "Discovery de Pagos"},
    {"sector": "Otros", "empresa": "Estafeta", "pitch_principal": "Discovery de Pagos"},
    {"sector": "Otros", "empresa": "DHL Mexico", "pitch_principal": "Discovery de Pagos"},
    {"sector": "Otros", "empresa": "FedEx Mexico", "pitch_principal": "Discovery de Pagos"},
    {"sector": "Otros", "empresa": "UPS Mexico", "pitch_principal": "Discovery de Pagos"},
    {"sector": "Otros", "empresa": "Paquetexpress", "pitch_principal": "Discovery de Pagos"}
]

@app.get("/api/companies")
async def get_companies():
    return {"success": True, "data": COMPANIES_DATABASE}

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

class FeedbackRequest(BaseModel):
    company_name: str
    campo: str
    valor_original: Any
    valor_editado: Any
    rating: int
    feedback_text: str = ""
    model_info: dict = {}

@app.post("/api/feedback")
async def save_feedback(request: FeedbackRequest):
    try:
        from core.database import db
        db.save_feedback(request.dict())
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze")
async def run_analysis(request: AnalysisRequest):
    try:
        from src.toku_radar.crew import TokuCrew
        crew = TokuCrew(
            empresa=request.empresa,
            sector=request.sector,
            pitch=request.pitch,
            prior_knowledge=request.context
        )
        result = crew.kickoff()
        return {"success": True, "data": str(result)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

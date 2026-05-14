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

@app.get("/")
def read_root():
    return {"status": "NERV OS API Online", "version": "2.0"}

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

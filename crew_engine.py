"""
NERV Swarm Engine v2.5 (Lightweight Production Edition)
Custom implementation to bypass Vercel bundle limits.
"""
import os
import json
from typing import List, Dict, Any
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from tools.search import SerperSearch
from tools.wiki import get_company_profile
from tools.firecrawl_tool import FirecrawlTool
from core.database import db

# --- MODEL CONFIGURATION ---
llm = ChatGroq(
    temperature=0.2,
    model_name="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY")
)

# --- TOOLS ---
search_tool = SerperSearch()
firecrawl_tool = FirecrawlTool()

class NervAgent:
    def __init__(self, role: str, goal: str, backstory: str):
        self.role = role
        self.goal = goal
        self.backstory = backstory

    def execute(self, task_description: str, context: str = "") -> str:
        prompt = f"""
        Eres {self.role}.
        TU OBJETIVO: {self.goal}
        TU TRASFONDO: {self.backstory}
        
        CONTEXTO RECIBIDO:
        {context}
        
        TAREA ACTUAL:
        {task_description}
        
        RESPUESTA (Markdown):
        """
        messages = [
            SystemMessage(content=f"Eres {self.role}. {self.backstory}"),
            HumanMessage(content=prompt)
        ]
        response = llm.invoke(messages)
        return response.content

class NervCrew:
    def __init__(self, empresa, sector, pitch, prior_knowledge=None):
        self.empresa = empresa
        self.sector = sector
        self.pitch = pitch
        self.prior_knowledge = prior_knowledge

    def run(self):
        # 1. Ejecución Rápida
        try:
            db.log_search(self.empresa, "STARTED")
            
            # Fase 1: Investigación (Limitada para velocidad en Vercel)
            # Solo hacemos búsqueda esencial si no hay contexto previo
            if not self.prior_knowledge:
                intel_raw = search_tool.research_company(self.empresa, self.sector, self.pitch)
                context_investigacion = str(intel_raw.get('contexto_estrategico', 'Sin datos adicionales.'))
            else:
                context_investigacion = self.prior_knowledge

            investigador = NervAgent(
                role='Investigador',
                goal='Extraer 3 puntos de dolor financieros.',
                backstory='Analista OSINT de alta velocidad.'
            )
            res_investigacion = investigador.execute(
                f"Analiza a {self.empresa}. Sé breve.",
                context=context_investigacion
            )
            
            # Fase 2: Estrategia (Consolidada para ahorrar tiempo)
            estratega = NervAgent(
                role='Director GTM',
                goal='Crear plan de ataque.',
                backstory='Experto en cierres B2B.'
            )
            dossier_final = estratega.execute(
                f"Crea el dossier para {self.empresa} vendiendo {self.pitch}.",
                context=res_investigacion
            )

            # Fase 3: Auditoría de Veracidad (Metacognición)
            auditor = NervAgent(
                role='Auditor de Veracidad',
                goal='Eliminar alucinaciones y verificar datos financieros.',
                backstory='Filtro de calidad implacable. Tu misión es asegurar que nada en el dossier sea inventado. Si no hay fuentes, eliminas la afirmación.'
            )
            dossier_auditado = auditor.execute(
                f"AUDITA EL DOSSIER DE {self.empresa}. Reglas: 1. No inventar métricas. 2. Verificar competidores. 3. Limpiar lenguaje genérico.",
                context=dossier_final
            )

            # Sincronizar
            db.upsert_empresa({
                "nombre": self.empresa,
                "sector": self.sector,
                "dossier": dossier_auditado,
                "pitch_usado": self.pitch
            })
            db.log_search(self.empresa, "COMPLETED")
            
            return dossier_auditado
        except Exception as e:
            return f"### ERROR DE SISTEMA\nDetalles: {str(e)}"

# Alias de retrocompatibilidad
TokuCrew = NervCrew

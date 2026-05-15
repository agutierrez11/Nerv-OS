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
    model_name="llama3-70b-8192",
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

class TokuCrew:
    def __init__(self, empresa, sector, pitch, prior_knowledge=None):
        self.empresa = empresa
        self.sector = sector
        self.pitch = pitch
        self.prior_knowledge = prior_knowledge

    def run(self):
        # 1. Definir Agentes
        investigador = NervAgent(
            role='Investigador Forense de Mercado',
            goal=f'Encontrar dolores financieros en {self.empresa}',
            backstory='Experto en OSINT y análisis de mercado.'
        )
        
        psicologo = NervAgent(
            role='Psicólogo de Ventas (DISC)',
            goal=f'Definir el perfil de los decisores en {self.empresa}',
            backstory='Experto en psicología B2B y metodología DISC.'
        )
        
        estratega = NervAgent(
            role='Director de Estrategia GTM',
            goal=f'Crear el plan de ataque final para vender {self.pitch}',
            backstory='El mejor estratega de ventas del mundo.'
        )

        # 2. Ejecutar Ciclo de Inteligencia
        db.log_search(self.empresa, "STARTED")
        
        # Fase 1: Investigación
        intel_raw = search_tool.research_company(self.empresa, self.sector, self.pitch)
        context_investigacion = f"Datos Crudos: {intel_raw.get('contexto_estrategico', '')}\nConocimiento Previo: {self.prior_knowledge}"
        
        res_investigacion = investigador.execute(
            f"Analiza la situación actual de {self.empresa} en el sector {self.sector}.",
            context=context_investigacion
        )
        
        # Fase 2: Psicología
        res_psicologia = psicologo.execute(
            f"Basado en esta investigación, ¿quiénes son los decisores clave?",
            context=res_investigacion
        )
        
        # Fase 3: Estrategia Final
        dossier_final = estratega.execute(
            f"Crea el dossier final de ventas para {self.empresa} enfocado en {self.pitch}.",
            context=f"INVESTIGACIÓN: {res_investigacion}\nPSICOLOGÍA: {res_psicologia}"
        )

        # 3. Sincronizar y Retornar
        try:
            db.upsert_empresa({
                "nombre": self.empresa,
                "sector": self.sector,
                "dossier": dossier_final,
                "pitch_usado": self.pitch
            })
            db.log_search(self.empresa, "COMPLETED")
        except:
            pass

        return dossier_final

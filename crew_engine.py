"""
crew_engine.py — Orquestación Avanzada con CrewAI + Groq + DeepSeek + Galileo.
"""
import os
from crewai import Agent, Task, Crew, Process
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from langchain.tools import tool
from tools.search import SerperSearch
from tools.wiki import get_company_profile
from tools.firecrawl_tool import FirecrawlTool
from core.database import db

# --- CONFIGURACIÓN DE OBSERVABILIDAD (GALILEO) ---
from phoenix.trace.langchain import LangChainInstrumentor
LangChainInstrumentor().instrument()

# --- DEFINICIÓN DE MODELOS ---
# Groq para velocidad (Agentes de investigación y psicología)
groq_llm = ChatGroq(
    temperature=0, 
    model_name="llama3-70b-8192",
    api_key=os.getenv("GROQ_API_KEY")
)

# DeepSeek para precisión (Agente Estratega)
deepseek_llm = ChatOpenAI(
    model_name="deepseek-chat",
    openai_api_base="https://api.deepseek.com/v1",
    openai_api_key=os.getenv("DEEPSEEK_API_KEY"),
    temperature=0.2
)

# Instanciar herramientas
search_tool_instance = SerperSearch()
firecrawl_tool_instance = FirecrawlTool()

@tool("serper_search")
def serper_search_tool(query: str):
    """Busca noticias y datos estratégicos de la empresa en Google."""
    return search_tool_instance._query(query)

@tool("firecrawl_scrape")
def firecrawl_scrape_tool(url: str):
    """Scrapea un sitio web completo y lo convierte a Markdown limpio."""
    return firecrawl_tool_instance.scrape_url(url)

@tool("wikipedia_profile")
def wikipedia_tool(empresa: str):
    """Obtiene el perfil institucional básico de Wikipedia."""
    return get_company_profile(empresa)

class TokuCrew:
    def __init__(self, empresa, sector, pitch, prior_knowledge=None):
        self.empresa = empresa
        self.sector = sector
        self.pitch = pitch
        self.prior_knowledge = prior_knowledge

    def run(self):
        # 1. DEFINIR AGENTES
        investigador = Agent(
            role='Investigador Forense de Mercado',
            goal=f'Encontrar dolores financieros y operativos reales en {self.empresa} relacionados con {self.pitch}',
            backstory='Experto en inteligencia competitiva. Sabes leer entre líneas en reportes anuales y noticias.',
            tools=[serper_search_tool, wikipedia_tool, firecrawl_scrape_tool],
            llm=groq_llm,
            verbose=True,
            memory=True
        )

        psicologo = Agent(
            role='Psicólogo de Ventas (Especialista DISC)',
            goal=f'Identificar a los decisores clave en {self.empresa} y definir su perfil psicológico Crystal/DISC',
            backstory='Experto en psicología aplicada a ventas B2B. Predices el comportamiento basado en huella digital.',
            tools=[serper_search_tool],
            llm=groq_llm,
            verbose=True
        )

        estratega = Agent(
            role='Director de Estrategia GTM (Gemelo Digital)',
            goal=f'Sintetizar el dossier final y el plan de ataque para {self.empresa} basado en {self.prior_knowledge or "sin contexto previo"}',
            backstory='El cerebro detrás de cierres millonarios. Conviertes datos técnicos en argumentos de venta irresistibles.',
            llm=deepseek_llm, # DeepSeek para la precisión final
            verbose=True
        )

        # 2. DEFINIR TAREAS
        tarea_investigacion = Task(
            description=f'Investiga a fondo {self.empresa}. Encuentra noticias de 2024-2025 sobre sus sistemas de pago y cobranza.',
            expected_output='Reporte detallado de fricciones operativas.',
            agent=investigador
        )

        tarea_psicologica = Task(
            description=f'Identifica decisores clave de {self.empresa} y define su perfil DISC.',
            expected_output='Perfil de decisores con metodología DISC.',
            agent=psicologo
        )

        tarea_dossier = Task(
            description=f'Crea el dossier final usando la investigación y el perfil psicológico. Contexto adicional: {self.prior_knowledge}',
            expected_output='Dossier final en formato Markdown estructurado.',
            agent=estratega,
            context=[tarea_investigacion, tarea_psicologica]
        )

        # 3. FORMAR EL ENJAMBRE
        crew = Crew(
            agents=[investigador, psicologo, estratega],
            tasks=[tarea_investigacion, tarea_psicologica, tarea_dossier],
            process=Process.sequential,
            verbose=True
        )

        db.log_search(self.empresa, "STARTED")
        result = crew.kickoff()
        
        # Sincronizar con Supabase (Datos estructurados simplificados)
        try:
            db.upsert_empresa({
                "nombre": self.empresa,
                "sector": self.sector,
                "dossier": str(result),
                "pitch_usado": self.pitch
            })
            db.log_search(self.empresa, "COMPLETED")
        except:
            pass

        return result

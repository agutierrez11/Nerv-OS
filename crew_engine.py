"""
crew_engine.py — Orquestación REAL con CrewAI.
Agentes autónomos con acceso a herramientas de búsqueda y scraping.
"""
import os
from crewai import Agent, Task, Crew, Process
from langchain.tools import tool
from tools.search import SerperSearch
from tools.wiki import get_company_profile
from tools.firecrawl_tool import FirecrawlTool

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
    def __init__(self, empresa, sector, pitch):
        self.empresa = empresa
        self.sector = sector
        self.pitch = pitch

    def run(self):
        # 1. DEFINIR AGENTES
        investigador = Agent(
            role='Investigador Forense de Mercado',
            goal=f'Encontrar dolores financieros y operativos reales en {self.empresa} relacionados con {self.pitch}',
            backstory='Eres un experto en inteligencia competitiva con 15 años de experiencia en Fintech México. Sabes leer entre líneas en reportes anuales y noticias.',
            tools=[serper_search_tool, wikipedia_tool, firecrawl_scrape_tool],
            verbose=True,
            allow_delegation=False,
            memory=True
        )

        psicologo = Agent(
            role='Psicólogo de Ventas (Especialista DISC)',
            goal=f'Identificar a los decisores clave en {self.empresa} y definir su perfil psicológico Crystal/DISC',
            backstory='Eres un experto en psicología aplicada a ventas B2B. Tu especialidad es predecir cómo hablarle a un CFO vs un Director de eCommerce basado en su huella digital.',
            tools=[serper_search_tool],
            verbose=True,
            allow_delegation=True
        )

        estratega = Agent(
            role='Director de Estrategia GTM',
            goal=f'Sintetizar el dossier final y el plan de ataque para {self.empresa}',
            backstory='Eres el cerebro detrás de los cierres más grandes en Toku. Sabes convertir datos técnicos en argumentos de venta irresistibles.',
            verbose=True,
            allow_delegation=False
        )

        # 2. DEFINIR TAREAS
        tarea_investigacion = Task(
            description=f'Investiga a fondo {self.empresa}. Encuentra noticias de 2024-2025 sobre sus sistemas de pago, problemas de cobranza o expansiones.',
            expected_output='Un reporte detallado de fricciones operativas y datos financieros.',
            agent=investigador
        )

        tarea_psicologica = Task(
            description=f'Busca en LinkedIn los nombres de los decisores de {self.empresa} (CFO, Head of Payments). Define su perfil DISC y 2 tips de comunicación.',
            expected_output='Perfil de decisores con metodología DISC y links de LinkedIn.',
            agent=psicologo
        )

        tarea_dossier = Task(
            description=f'Crea el dossier final de prospección para {self.empresa} usando la investigación y el perfil psicológico. Incluye el Abogado del Diablo.',
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

        return crew.kickoff()

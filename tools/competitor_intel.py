"""
competitor_intel.py — Extrae nombres de clientes desde páginas de competidores.
Estrategia: Firecrawl scrape → LLM extrae nombres de empresa del Markdown.
"""
import os
import re
import json
from typing import List
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from tools.firecrawl_tool import FirecrawlTool

llm = ChatGroq(
    temperature=0.0,
    model_name="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY")
)

firecrawl = FirecrawlTool()

# Páginas típicas donde los competidores muestran sus clientes
CANDIDATE_PATHS = [
    "/customers",
    "/customer-stories",
    "/case-studies",
    "/success-stories",
    "/clients",
    "/clientes",
    "/casos-de-exito",
    "/about",
    "/who-we-serve",
]


def _clean_url(base: str) -> str:
    """Normaliza la URL base (sin trailing slash, sin path)."""
    base = base.strip().rstrip("/")
    if not base.startswith("http"):
        base = "https://" + base
    # Remover paths existentes para quedarnos solo con el dominio
    from urllib.parse import urlparse
    parsed = urlparse(base)
    return f"{parsed.scheme}://{parsed.netloc}"


def _extract_companies_from_markdown(markdown_text: str, source_url: str) -> List[str]:
    """Usa LLM para extraer nombres de empresas desde contenido Markdown."""
    if not markdown_text or len(markdown_text) < 50:
        return []

    # Truncar si es muy largo
    content = markdown_text[:4000]

    prompt = f"""El siguiente contenido proviene de la página de clientes/casos de uso de un competidor ({source_url}).

Extrae TODOS los nombres de empresas clientes que se mencionan. 
- Solo nombres de empresas reales (no personas, no categorías genéricas)
- Si no hay empresas mencionadas, devuelve lista vacía

Contenido:
{content}

Devuelve SOLO un JSON:
```json
["Empresa A", "Empresa B", "Empresa C"]
```"""

    try:
        resp = llm.invoke([
            SystemMessage(content="Eres un extractor de entidades. Responde SOLO en JSON válido."),
            HumanMessage(content=prompt)
        ])
        raw = resp.content

        # Extraer JSON del response
        match = re.search(r"```json\s*([\s\S]+?)\s*```", raw)
        if match:
            return json.loads(match.group(1))
        return json.loads(raw)
    except Exception:
        # Fallback: buscar patrones de empresa por regex básico
        # Busca palabras con mayúsculas consecutivas (nombres propios)
        found = re.findall(r'\b([A-Z][a-zA-Z]+(?: [A-Z][a-zA-Z]+){0,3})\b', markdown_text)
        # Filtrar stopwords comunes
        stopwords = {"The", "Our", "Your", "How", "When", "What", "With", "For", "And", "Learn", "More"}
        return list(set(w for w in found if w not in stopwords))[:20]


class CompetitorIntelTool:
    """
    Scraping de páginas de competidores para extraer sus clientes actuales.
    
    Uso:
        tool = CompetitorIntelTool()
        empresas = tool.extract_clients("https://gtmagent.getswan.com")
        # → ["HubSpot", "Salesforce", ...]
    """

    def extract_clients(self, competitor_url: str, max_pages: int = 4) -> List[str]:
        """
        Escanea las páginas candidatas del competidor y retorna lista de clientes únicos.
        """
        base = _clean_url(competitor_url)
        all_companies = []
        pages_scraped = 0

        for path in CANDIDATE_PATHS:
            if pages_scraped >= max_pages:
                break

            url = f"{base}{path}"
            content = firecrawl.scrape_url(url)

            # Si Firecrawl no pudo scraperlo (404 / error)
            if not content or content.startswith("[ERROR") or content.startswith("[Exception"):
                continue

            pages_scraped += 1
            companies = _extract_companies_from_markdown(content, url)
            all_companies.extend(companies)

        # Si no encontramos nada con paths específicos, intentar la raíz
        if not all_companies:
            content = firecrawl.scrape_url(base)
            if content and not content.startswith("["):
                all_companies = _extract_companies_from_markdown(content, base)

        # Deduplicar y limpiar
        seen = set()
        unique = []
        for c in all_companies:
            c_clean = c.strip()
            if c_clean and c_clean.lower() not in seen and len(c_clean) > 2:
                seen.add(c_clean.lower())
                unique.append(c_clean)

        return unique

    def quick_preview(self, competitor_url: str) -> dict:
        """
        Versión rápida: solo scrape la home + /customers.
        Útil para previsualizar antes de un análisis completo.
        """
        base = _clean_url(competitor_url)
        results = {}

        for path in ["", "/customers", "/case-studies"]:
            url = f"{base}{path}" if path else base
            content = firecrawl.scrape_url(url)
            if content and not content.startswith("["):
                companies = _extract_companies_from_markdown(content, url)
                if companies:
                    results[path or "/"] = companies

        return results

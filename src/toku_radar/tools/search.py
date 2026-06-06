"""
search.py — Serper wrapper con soporte multi-regional y descubrimiento de URLs.
Diseñado para mantenerse en el free tier (2500/mes).
41 empresas × 4 queries = 164 queries por batch completo.
"""
import requests
import os
import time


# Mapeo de países a códigos Serper (gl = país, hl = idioma)
PAIS_CODES = {
    "méxico":     {"gl": "mx", "hl": "es", "nombre": "México"},
    "mexico":     {"gl": "mx", "hl": "es", "nombre": "México"},
    "brasil":     {"gl": "br", "hl": "pt", "nombre": "Brasil"},
    "brazil":     {"gl": "br", "hl": "pt", "nombre": "Brasil"},
    "colombia":   {"gl": "co", "hl": "es", "nombre": "Colombia"},
    "chile":      {"gl": "cl", "hl": "es", "nombre": "Chile"},
    "perú":       {"gl": "pe", "hl": "es", "nombre": "Perú"},
    "peru":       {"gl": "pe", "hl": "es", "nombre": "Perú"},
    "argentina":  {"gl": "ar", "hl": "es", "nombre": "Argentina"},
    "ecuador":    {"gl": "ec", "hl": "es", "nombre": "Ecuador"},
    "costa rica": {"gl": "cr", "hl": "es", "nombre": "Costa Rica"},
}


def get_pais_codes(pais: str) -> dict:
    """Retorna los códigos gl/hl para el país dado, con fallback a México."""
    return PAIS_CODES.get(pais.lower().strip(), {"gl": "mx", "hl": "es", "nombre": pais.capitalize()})


class SerperSearch:
    def __init__(self):
        self.api_key = os.getenv("SERPER_API_KEY")
        self.url = "https://google.serper.dev/search"

    def _query(self, q: str, gl: str = "mx", hl: str = "es") -> str:
        """Realiza una consulta a Serper y retorna los snippets como texto."""
        if not self.api_key:
            return "[ERROR: SERPER_API_KEY no encontrada en .env]"
        try:
            resp = requests.post(
                self.url,
                headers={"X-API-KEY": self.api_key, "Content-Type": "application/json"},
                json={"q": q, "gl": gl, "hl": hl, "num": 5},
                timeout=10,
            )
            results = resp.json()
            snippets = []
            for item in results.get("organic", [])[:5]:
                title = item.get("title", "")
                snippet = item.get("snippet", "")
                link = item.get("link", "")
                snippets.append(f"- {title}: {snippet} ({link})")
            return "\n".join(snippets) if snippets else "Sin resultados."
        except Exception as e:
            return f"[Error Serper: {e}]"

    def search_links(self, q: str, gl: str = "mx", hl: str = "es", num: int = 5) -> list[dict]:
        """
        Realiza una búsqueda y retorna los resultados con título, snippet y URL completa.
        Útil para resolver nombres de empresa a URLs reales y para descubrir subpáginas.
        """
        if not self.api_key:
            return []
        try:
            resp = requests.post(
                self.url,
                headers={"X-API-KEY": self.api_key, "Content-Type": "application/json"},
                json={"q": q, "gl": gl, "hl": hl, "num": num},
                timeout=10,
            )
            results = resp.json()
            return [
                {
                    "title": item.get("title", ""),
                    "snippet": item.get("snippet", ""),
                    "link": item.get("link", ""),
                }
                for item in results.get("organic", [])[:num]
            ]
        except Exception as e:
            return []

    def research_company(self, empresa: str, sector: str, pitch: str, url: str = "", pais: str = "México", gl: str = "mx", hl: str = "es") -> dict:
        """
        4 queries por empresa para asegurar inteligencia real.
        Ajusta el idioma y la geolocalización según el país destino.
        """
        time.sleep(1)

        # Determinar el nombre localized del país para las queries
        codes = get_pais_codes(pais)
        gl = gl or codes["gl"]
        hl = hl or codes["hl"]
        nombre_pais = codes["nombre"]

        # Si hay URL, la usamos para anclar la búsqueda
        site_filter = f"site:{url.replace('https://', '').replace('http://', '').split('/')[0]}" if url else ""

        # Query 1: Información General y Estrategia
        q1 = f'"{empresa}" {nombre_pais} estrategia negocio 2024 2025'
        if url:
            q1 += f' OR "{url}"'

        # Query 2: Dolor Operativo / Pagos
        if hl == "pt":
            q2 = f'"{empresa}" problemas pagamentos cobranças {nombre_pais} OR "reclamações" pagamentos'
        else:
            q2 = f'"{empresa}" problemas pagos cobranza {nombre_pais} OR "quejas" pagos'
        if site_filter:
            q2 = f'{site_filter} "pagos" OR "cobros" OR "contacto" OR "pricing"'

        # Query 3: LinkedIn / C-Levels
        if hl == "pt":
            q3 = f'site:linkedin.com/in/ "{empresa}" (CFO OR "Diretor" OR "Pagamentos" OR "Financeiro") {nombre_pais}'
        else:
            q3 = f'site:linkedin.com/in/ "{empresa}" (CFO OR "Director" OR "Pagos" OR "Finanzas") {nombre_pais}'

        # Query 4: Noticias Recientes
        q4 = f'"{empresa}" noticias 2024 2025 {nombre_pais}'

        return {
            "contexto_estrategico": self._query(q1, gl=gl, hl=hl),
            "dolor_operativo": self._query(q2, gl=gl, hl=hl),
            "linkedin_discovery": self._query(q3, gl=gl, hl=hl),
            "favikon_intel": self._query(q4, gl=gl, hl=hl),
        }


class TavilySearch:
    def __init__(self):
        self.api_key = os.getenv("TAVILY_API_KEY")
        self.url = "https://api.tavily.com/search"

    def query(self, q: str) -> str:
        """
        Realiza una consulta de alta fidelidad a Tavily para obtener respuestas optimizadas para RAG.
        Devuelve el resumen de la respuesta (answer) y las 3 fuentes más relevantes.
        """
        if not self.api_key:
            return "[ERROR: TAVILY_API_KEY no encontrada en .env]"
        try:
            payload = {
                "api_key": self.api_key,
                "query": q,
                "search_depth": "advanced",
                "include_answer": True
            }
            resp = requests.post(self.url, json=payload, timeout=20)
            if resp.status_code == 200:
                data = resp.json()
                answer = data.get("answer", "")
                results = []
                for item in data.get("results", [])[:3]:
                    title = item.get("title", "")
                    snippet = item.get("snippet", "")
                    url = item.get("url", "")
                    results.append(f"- {title}: {snippet} ({url})")
                
                output = ""
                if answer:
                    output += f"Resumen Inteligente de Tavily:\n{answer}\n\n"
                if results:
                    output += "Fuentes clave:\n" + "\n".join(results)
                
                return output if output else "Sin resultados."
            else:
                return f"[Error de Tavily API (Status {resp.status_code}): {resp.text}]"
        except Exception as e:
            return f"[Excepción en Tavily Search: {e}]"

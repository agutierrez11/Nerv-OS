"""
search.py — Serper wrapper con 2 queries estratégicos por empresa.
Diseñado para mantenerse en el free tier (2500/mes).
41 empresas × 2 queries = 82 queries por batch completo.
"""
import requests
import os
import time


class SerperSearch:
    def __init__(self):
        self.api_key = os.getenv("SERPER_API_KEY")
        self.url = "https://google.serper.dev/search"

    def _query(self, q: str) -> str:
        if not self.api_key:
            return "[ERROR: SERPER_API_KEY no encontrada en .env]"
        try:
            resp = requests.post(
                self.url,
                headers={"X-API-KEY": self.api_key, "Content-Type": "application/json"},
                json={"q": q, "gl": "mx", "hl": "es", "num": 5},
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

    def research_company(self, empresa: str, sector: str, pitch: str, url: str = "") -> dict:
        """
        4 queries por empresa para asegurar inteligencia real.
        """
        time.sleep(1)
        
        # Si hay URL, la usamos para anclar la búsqueda
        site_filter = f"site:{url.replace('https://', '').replace('http://', '').split('/')[0]}" if url else ""
        
        # Query 1: Información General y Estrategia (Más flexible)
        q1 = f'"{empresa}" México estrategia negocio 2024 2025'
        if url: q1 += f' OR "{url}"'
        
        # Query 2: Dolor Operativo / Pagos (Foco en el problema)
        q2 = f'"{empresa}" problemas pagos cobranza México OR "quejas" pagos'
        if site_filter: q2 = f'{site_filter} "pagos" OR "cobros" OR "contacto"'
        
        # Query 3: LinkedIn / C-Levels
        q3 = f'site:linkedin.com/in/ "{empresa}" (CFO OR "Director" OR "Pagos" OR "Finanzas") México'
        
        # Query 4: Noticias Recientes
        q4 = f'"{empresa}" noticias 2024 2025 México'

        return {
            "contexto_estrategico": self._query(q1),
            "dolor_operativo": self._query(q2),
            "linkedin_discovery": self._query(q3),
            "favikon_intel": self._query(q4),
        }

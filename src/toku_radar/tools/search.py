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

    def research_company(self, empresa: str, sector: str, pitch: str) -> dict:
        """
        3 queries por empresa.
        Query 1: Contexto estratégico.
        Query 2: Dolor operativo.
        Query 3: LinkedIn Discovery (C-Levels).
        """
        time.sleep(1)
        q1 = f'"{empresa}" México noticias estrategia pagos cobros 2024 2025'
        q2 = f'"{empresa}" {sector} cobranza pagos digitales desafío operativo México'
        q3 = f'site:linkedin.com/in/ "{empresa}" (CFO OR "Director de Finanzas" OR "Head of Payments" OR "Director de Pagos" OR eCommerce) México'
        q4 = f'site:favikon.com "{empresa}" OR "ranking LinkedIn" México'

        return {
            "contexto_estrategico": self._query(q1),
            "dolor_operativo": self._query(q2),
            "linkedin_discovery": self._query(q3),
            "favikon_intel": self._query(q4),
        }

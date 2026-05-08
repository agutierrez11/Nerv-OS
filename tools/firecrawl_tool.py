"""
firecrawl_tool.py — Wrapper para Firecrawl API.
Permite scrapear URLs y convertirlas a Markdown limpio para grounding.
"""
import os
import requests
import time

class FirecrawlTool:
    def __init__(self):
        self.api_key = os.getenv("FIRECRAWL_API_KEY")
        self.base_url = "https://api.firecrawl.dev/v0"

    def scrape_url(self, url: str) -> str:
        """Scrapea una URL y devuelve el contenido en Markdown."""
        if not self.api_key:
            return "[ERROR: FIRECRAWL_API_KEY no encontrada]"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "url": url,
            "pageOptions": {
                "onlyMainContent": True
            }
        }
        
        try:
            # Endpoint de scrape
            response = requests.post(f"{self.base_url}/scrape", headers=headers, json=payload, timeout=20)
            data = response.json()
            
            if data.get("success"):
                return data.get("data", {}).get("markdown", "Sin contenido Markdown.")
            else:
                return f"[Error Firecrawl: {data.get('error', 'Unknown')}]"
        except Exception as e:
            return f"[Exception Firecrawl: {e}]"

    def search_and_scrape(self, query: str) -> str:
        """Realiza una búsqueda y scrapea el mejor resultado (Deep Search)."""
        # Firecrawl también tiene un endpoint de search/crawl que es muy potente
        # Por ahora mantendremos Serper para búsqueda y Firecrawl para scraping profundo de la web oficial.
        pass

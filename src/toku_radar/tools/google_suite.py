import os
import requests
from core.logger import logger
from core.resilience import retry_with_backoff

class GoogleSuiteTool:
    """
    Wrapper profesional para la Suite de Google de Scrape.do.
    Proporciona acceso a Search, Maps, News y Trends con una sola estructura.
    """
    def __init__(self):
        self.token = os.getenv("SCRAPE_DO_TOKEN")
        self.base_url = "https://api.scrape.do/plugin/google"

    @retry_with_backoff(retries=3)
    def _call_api(self, endpoint: str, query: str, params: dict = None) -> dict:
        if not self.token:
            logger.error("SCRAPE_DO_TOKEN no configurado.")
            return {"error": "Token missing"}
        
        url = f"{self.base_url}/{endpoint}"
        final_params = {"token": self.token, "q": query}
        if params:
            final_params.update(params)
            
        try:
            response = requests.get(url, params=final_params, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error en Google Suite ({endpoint}): {e}")
            return {"error": str(e)}

    def search_news(self, query: str):
        """Busca noticias frescas con links directos."""
        return self._call_api("news", query)

    def analyze_local_sentiment(self, company_name: str, city: str = "Mexico City"):
        """
        Analiza Google Maps para encontrar reseñas y problemas operativos
        reportados por clientes reales.
        """
        query = f"{company_name} {city}"
        return self._call_api("maps/search", query)

    def get_trends(self, keyword: str):
        """Obtiene datos de interes y tendencias."""
        return self._call_api("trends", keyword)

# Instancia global
google_suite = GoogleSuiteTool()

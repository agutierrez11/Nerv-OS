"""
resilient_scraper.py — Scraper resiliente con cascada automática.
Intenta usar Firecrawl primero y conmuta a Anakin.io en caso de fallos, bloqueos
de Cloudflare o contenidos vacíos/insuficientes.
"""
import os
import time
import requests
from core.logger import logger
from toku_radar.tools.firecrawl_tool import FirecrawlTool

class ResilientScraper:
    def __init__(self):
        self.firecrawl = FirecrawlTool()
        self.anakin_api_key = os.getenv("ANAKIN_API_KEY")
        self.anakin_url = "https://api.anakin.io/v1/url-scraper"

    def scrape_url(self, url: str) -> str:
        """Intenta Firecrawl y conmuta a Anakin.io si es bloqueado o devuelve < 400 chars."""
        logger.info(f"Iniciando raspado resiliente para: {url}")
        
        # 1. Intentar con Firecrawl
        firecrawl_res = ""
        try:
            firecrawl_res = self.firecrawl.scrape_url(url)
        except Exception as e:
            logger.warning(f"Error imprevisto al llamar a Firecrawl: {e}")
            firecrawl_res = f"[Exception Firecrawl: {e}]"

        # Validar si el resultado de Firecrawl es exitoso y suficiente
        is_error = "[error" in firecrawl_res.lower() or "[exception" in firecrawl_res.lower()
        is_insufficient = len(firecrawl_res.strip()) < 400

        if not is_error and not is_insufficient:
            logger.info(f"Raspado de Firecrawl completado con éxito ({len(firecrawl_res)} caracteres).")
            return firecrawl_res

        # 2. Conmutar a Anakin.io (Fallback)
        reason = "error" if is_error else f"contenido insuficiente ({len(firecrawl_res)} chars)"
        logger.warning(f"Firecrawl falló o dio {reason}. Conmutando a Anakin.io...")

        if not self.anakin_api_key:
            logger.error("No se puede conmutar a Anakin.io porque ANAKIN_API_KEY no está configurada.")
            return firecrawl_res  # Retornamos lo que Firecrawl haya dado

        headers = {
            "X-API-Key": self.anakin_api_key,
            "Content-Type": "application/json"
        }
        payload = {
            "url": url
        }

        try:
            logger.info("Enviando trabajo de raspado a Anakin.io...")
            response = requests.post(self.anakin_url, headers=headers, json=payload, timeout=25)
            
            if response.status_code not in (200, 202):
                logger.error(f"Error al enviar trabajo a Anakin.io ({response.status_code}): {response.text}")
                return firecrawl_res

            res_json = response.json()
            job_id = res_json.get("jobId")
            if not job_id:
                logger.error("Anakin.io no devolvió jobId en la respuesta.")
                return firecrawl_res

            logger.info(f"Trabajo de Anakin.io recibido (Job ID: {job_id}). Polling para estado...")
            
            # Polling con límite de 15 intentos (~30s)
            for i in range(15):
                time.sleep(2)
                status_url = f"{self.anakin_url}/{job_id}"
                status_resp = requests.get(status_url, headers={"X-API-Key": self.anakin_api_key}, timeout=10)
                
                if status_resp.status_code == 200:
                    status_json = status_resp.json()
                    status = status_json.get("status")
                    logger.debug(f"Intento de polling #{i+1}: status = {status}")
                    
                    if status == "completed":
                        content = status_json.get("content", "")
                        logger.info(f"¡Raspado de Anakin.io completado exitosamente! ({len(content)} caracteres).")
                        return content
                    elif status == "failed":
                        err_msg = status_json.get("error", "Error desconocido")
                        logger.error(f"El trabajo de Anakin.io falló en el servidor: {err_msg}")
                        break
                else:
                    logger.error(f"Error de API de Anakin al consultar estado ({status_resp.status_code}): {status_resp.text}")
            
            logger.error("Se alcanzó el límite de tiempo esperando el trabajo de Anakin.io.")
            return firecrawl_res

        except Exception as e:
            logger.error(f"Excepción ocurrida durante fallback a Anakin.io: {e}")
            return firecrawl_res

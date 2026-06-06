"""
resilient_scraper.py — Scraper resiliente con cascada automática de 3 niveles.

Cascada:
  1. Firecrawl   — Rápido, alto rendimiento, Markdown limpio.
  2. Anakin.io   — Fallback anti-bloqueo con capacidad JavaScript.
  3. Apify       — Última milla: Website Content Crawler con Playwright adaptativo,
                   anti-fingerprinting y proxies rotativos. Máxima resiliencia.
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
        self.apify_api_key = os.getenv("APIFY_API_KEY")
        self.apify_actor = "apify~website-content-crawler"

    def scrape_url(self, url: str) -> str:
        """
        Intenta Firecrawl → Anakin.io → Apify en cascada.
        Retorna el mejor contenido disponible en Markdown.
        """
        logger.info(f"Iniciando raspado resiliente para: {url}")

        # ─── NIVEL 1: Firecrawl ───────────────────────────────────────────────
        firecrawl_res = ""
        try:
            firecrawl_res = self.firecrawl.scrape_url(url)
        except Exception as e:
            logger.warning(f"Error al llamar a Firecrawl: {e}")
            firecrawl_res = f"[Exception Firecrawl: {e}]"

        is_error = "[error" in firecrawl_res.lower() or "[exception" in firecrawl_res.lower()
        is_insufficient = len(firecrawl_res.strip()) < 400

        if not is_error and not is_insufficient:
            logger.info(f"Firecrawl OK ({len(firecrawl_res)} chars).")
            return firecrawl_res

        reason = "error" if is_error else f"insuficiente ({len(firecrawl_res)} chars)"
        logger.warning(f"Firecrawl falló ({reason}). Conmutando a Anakin.io...")

        # ─── NIVEL 2: Anakin.io ──────────────────────────────────────────────
        anakin_res = self._try_anakin(url, firecrawl_res)
        if anakin_res and len(anakin_res.strip()) >= 400 and "[error" not in anakin_res.lower():
            return anakin_res

        logger.warning(f"Anakin.io también falló o fue insuficiente. Conmutando a Apify...")

        # ─── NIVEL 3: Apify Website Content Crawler ──────────────────────────
        apify_res = self._try_apify(url)
        if apify_res and len(apify_res.strip()) >= 400:
            return apify_res

        # Si todo falla, retornamos lo mejor que tenemos
        best = max([firecrawl_res, anakin_res or "", apify_res or ""], key=len)
        logger.error(f"Los 3 scrapers fallaron para {url}. Retornando la mejor respuesta disponible ({len(best)} chars).")
        return best

    # ─── Implementación Anakin.io ─────────────────────────────────────────────
    def _try_anakin(self, url: str, fallback: str) -> str:
        if not self.anakin_api_key:
            logger.error("ANAKIN_API_KEY no configurada. Saltando Anakin.io.")
            return fallback

        headers = {
            "X-API-Key": self.anakin_api_key,
            "Content-Type": "application/json"
        }
        try:
            logger.info("Enviando trabajo a Anakin.io...")
            response = requests.post(self.anakin_url, headers=headers, json={"url": url}, timeout=25)

            if response.status_code not in (200, 202):
                logger.error(f"Error Anakin.io ({response.status_code}): {response.text}")
                return fallback

            res_json = response.json()
            job_id = res_json.get("jobId")
            if not job_id:
                logger.error("Anakin.io no devolvió jobId.")
                return fallback

            logger.info(f"Anakin.io Job ID: {job_id}. Polling...")
            for i in range(15):
                time.sleep(2)
                status_url = f"{self.anakin_url}/{job_id}"
                status_resp = requests.get(status_url, headers={"X-API-Key": self.anakin_api_key}, timeout=10)

                if status_resp.status_code == 200:
                    status_json = status_resp.json()
                    status = status_json.get("status")
                    logger.debug(f"Anakin polling #{i+1}: {status}")
                    if status == "completed":
                        content = status_json.get("content", "")
                        logger.info(f"Anakin.io completado ({len(content)} chars).")
                        return content
                    elif status == "failed":
                        logger.error(f"Anakin.io falló: {status_json.get('error', '?')}")
                        break

            logger.error("Anakin.io timeout.")
            return fallback
        except Exception as e:
            logger.error(f"Excepción en Anakin.io: {e}")
            return fallback

    # ─── Implementación Apify ────────────────────────────────────────────────
    def _try_apify(self, url: str) -> str:
        """
        Usa el actor apify/website-content-crawler en modo síncrono.
        Usa Playwright adaptive para manejar SPAs y sitios con Cloudflare.
        """
        if not self.apify_api_key:
            logger.error("APIFY_API_KEY no configurada. Saltando Apify.")
            return ""

        apify_endpoint = (
            f"https://api.apify.com/v2/acts/{self.apify_actor}"
            f"/run-sync-get-dataset-items?token={self.apify_api_key}"
        )

        payload = {
            "startUrls": [{"url": url}],
            "crawlerType": "playwright:adaptive",   # Inteligente: usa JS solo cuando es necesario
            "maxCrawlPages": 1,                     # Solo la página solicitada (no crawl completo)
            "maxCrawlDepth": 0,
            "outputFormats": ["markdown"],
            "proxyConfiguration": {"useApifyProxy": True},
        }

        try:
            logger.info(f"Enviando URL a Apify Website Content Crawler: {url}")
            response = requests.post(
                apify_endpoint,
                json=payload,
                timeout=90,  # El actor síncrono puede tardar hasta 60s
            )

            if response.status_code not in (200, 201):
                logger.error(f"Apify error ({response.status_code}): {response.text[:200]}")
                return ""

            items = response.json()
            if not items or not isinstance(items, list):
                logger.error("Apify retornó respuesta vacía o inesperada.")
                return ""

            # Extraer el campo markdown o text del primer ítem
            first = items[0]
            content = first.get("markdown", "") or first.get("text", "")
            if content:
                logger.info(f"Apify Website Content Crawler exitoso ({len(content)} chars).")
            else:
                logger.warning("Apify retornó un ítem pero sin contenido markdown/text.")
            return content

        except Exception as e:
            logger.error(f"Excepción en Apify: {e}")
            return ""

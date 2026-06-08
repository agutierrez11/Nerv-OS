import yaml
import os
import sys
import time
import json
from typing import Dict, Any, List
from dotenv import load_dotenv
from pathlib import Path

# --- IMPORTACIONES NERV 2.0 ---
from core.logger import logger
from core.resilience import retry_with_backoff, CircuitBreaker
from core.database import db
from core.cache import cache

# --- CONFIGURACION DE RUTAS ---
CURRENT_DIR = Path(__file__).parent.absolute()
SRC_DIR = CURRENT_DIR.parent # src/
PROJECT_ROOT = SRC_DIR.parent # temp_nerv_os/

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from toku_radar.tools.search import SerperSearch, TavilySearch
from toku_radar.tools.resilient_scraper import ResilientScraper
from toku_radar.tools.wiki import get_company_profile
from toku_radar.tools.auditor import VeracityAuditor
from toku_radar.tools.miro_predictor import MiroPredictor
from toku_radar.tools.memory import NervMemory
from toku_radar.tools.groq_rotator import GroqRotator
from toku_radar.tools.deepseek_client import DeepSeekClient
from toku_radar.tools.hermes_client import HermesClient
from toku_radar.tools.google_suite import google_suite

# Cargar .env opcionalmente (para desarrollo local)
if os.path.exists(".env"):
    load_dotenv()
elif os.path.exists("../.env"):
    load_dotenv("../.env")

# Instancia global de Circuit Breaker para LLMs
llm_breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=30)

class Agent:
    def __init__(self, config, log_callback=None, engine="groq", constitution="", gl="mx", hl="es"):
        self.role = config['role']
        self.goal = config['goal']
        self.backstory = config['backstory']
        self.log_callback = log_callback
        self.engine = engine
        self.constitution = constitution  # Reglas universales de NERV OS
        self.gl = gl
        self.hl = hl
        
        if self.engine == "deepseek":
            self.rotator = DeepSeekClient(log_callback=self._log)
            self.model_planning = "deepseek-chat"
            self.model_final = "deepseek-chat"
        elif self.engine == "hermes":
            self.rotator = HermesClient(log_callback=self._log)
            self.model_planning = "nousresearch/hermes-4-70b"
            self.model_final = "nousresearch/hermes-4-70b"
        else:
            self.rotator = GroqRotator(log_callback=self._log)
            self.model_planning = "llama-3.3-70b-versatile"
            self.model_final = "llama-3.3-70b-versatile"
        
        self.search_tool = SerperSearch()
        self.tavily_tool = TavilySearch()
        self.firecrawl_tool = ResilientScraper()
        self.memory = NervMemory()

    def _log(self, text: str):
        if self.log_callback:
            try:
                self.log_callback(text)
            except Exception:
                try:
                    # Fallback para consolas con codificación heredada (Windows CP1252/charmap)
                    print(text.encode('ascii', errors='replace').decode('ascii'))
                except Exception:
                    pass

    def _execute_tool(self, plan_text, task_desc):
        """Lógica de decisión de herramienta avanzada (Google Suite + Fallbacks)."""
        plan_lower = plan_text.lower()
        msg = ""
        res = ""

        if "tavily" in plan_lower or "deep search" in plan_lower or "búsqueda profunda" in plan_lower:
            msg = "## Action: Tavily Deep Search"
            res = self.tavily_tool.query(task_desc)
        elif "news" in plan_lower or "noticias" in plan_lower:
            msg = "## Action: Serper Strategic News"
            res = self.search_tool._query(f"{task_desc} news 2024 2025", gl=self.gl, hl=self.hl)
        elif "maps" in plan_lower or "reseñas" in plan_lower or "sentiment" in plan_lower:
            msg = "## Action: Standard Search (Maps Disabled)"
            res = self.search_tool._query(f"{task_desc} news reviews", gl=self.gl, hl=self.hl)
        elif "noticias" in plan_lower or "news" in plan_lower:
            msg = "## Action: Google News Deep Scan"
            res = str(google_suite.search_news(task_desc))
        elif "trends" in plan_lower or "tendencias" in plan_lower:
            msg = "## Action: Google Trends Analysis"
            res = str(google_suite.get_trends(task_desc))
        elif "firecrawl" in plan_lower or "scrape" in plan_lower:
            msg = "## Action: Resilient Web Scraping"
            import re
            urls = re.findall(r'https?://[^\s<>"]+|www\.[^\s<>"]+', plan_text)
            scrape_url = next((url for url in urls), "")
            if scrape_url:
                res = self.firecrawl_tool.scrape_url(scrape_url)
            else:
                res = "Error: No se encontró una URL específica para raspar en tu pensamiento."
        elif "wiki" in plan_lower:
            msg = "## Action: Wikipedia lookup"
            res = get_company_profile(task_desc[:30])
        elif "prospeo" in plan_lower or "correo" in plan_lower or "email" in plan_lower:
            msg = "## Action: Prospeo Email Enrichment"
            import re
            urls = re.findall(r'https?://[^\s<>"]+|www\.[^\s<>"]+', plan_text)
            linkedin_url = next((url for url in urls if 'linkedin.com/in/' in url), "")
            if linkedin_url:
                from toku_radar.tools.prospeo_client import prospeo_enrich_person
                res = prospeo_enrich_person.run(linkedin_url)
            else:
                res = "Error: No se detectó una URL de LinkedIn válida en tu petición para usar Prospeo. Asegúrate de incluir la URL completa (ej. https://www.linkedin.com/in/...) al mencionar Prospeo."
        else:
            msg = "## Action: Standard Search (Serper)"
            res = self.search_tool._query(task_desc, gl=self.gl, hl=self.hl)
        
        self._log(f"  {msg}")
        return res

    @retry_with_backoff(retries=3, backoff_in_seconds=2)
    def execute(self, task_desc, context=""):
        logger.info(f"Agente {self.role} iniciando razonamiento Hermes...")
        self._log(f"\n[ AGENT: {self.role} ]")
        
        past_intelligence = self.memory.search_similar_cases(context[:100])
        
        # BUCLE DE RAZONAMIENTO ESTILO HERMES 3
        full_conversation = [
            {"role": "system", "content": f"""Eres {self.role}. {self.backstory}

{self.constitution}

REGLAS DE OPERACION:
1. Empieza con <thought> para planificar tus pasos.
2. Si necesitas datos, menciona 'USAR HERRAMIENTA' y el tipo (Maps/News/Search/Prospeo).
3. Analiza la observacion y genera el entregable final.
EXTRA: Si identificas el perfil de LinkedIn de un directivo, DEBES usar 'USAR HERRAMIENTA PROSPEO' e incluir la URL de LinkedIn en tu pensamiento para obtener su correo electrónico.
IMPORTANTE: En tu entregable final, NUNCA escribas leyendas instruccionales como 'USAR HERRAMIENTA PROSPEO' o similares. Si obtuviste el correo mediante la herramienta, ponlo directamente. Si no pudiste obtenerlo o la herramienta no está disponible, estima/calcula el correo usando el formato estándar corporativo de la empresa del cliente (ej. nombre.apellido@empresa.com, nombre@empresa.com) basándote en su nombre y dominio, y ponlo directamente.
            """},
            {"role": "user", "content": f"Tarea: {task_desc}\nContexto: {context}\nMemoria: {past_intelligence}"}
        ]

        # 1. Fase de Pensamiento y Decision
        resp = llm_breaker.call(self.rotator.create_completion,
            model=self.model_planning,
            messages=full_conversation,
            temperature=0.3
        )
        thought_process = resp.choices[0].message.content
        self._log(f"  ## Pensamiento: {thought_process[:200]}...")

        # 2. Fase de Accion (Si el pensamiento lo requiere)
        plan_lower = thought_process.lower()
        if any(kw in plan_lower for kw in ["usar", "herramienta", "buscar", "investigar", "maps", "news", "prospeo", "correo", "email"]):
            observation = self._execute_tool(thought_process, task_desc)
        else:
            observation = "La informacion actual es suficiente para el entregable."

        # 3. Sintesis Final
        full_conversation.append({"role": "assistant", "content": thought_process})
        full_conversation.append({"role": "user", "content": f"Observacion recibida: {observation}\nGenera ahora el entregable final."})

        final_resp = llm_breaker.call(self.rotator.create_completion,
            model=self.model_final,
            messages=full_conversation,
            temperature=0.2
        )
        return final_resp.choices[0].message.content

# Alias de compatibilidad para imports legacy que aún usen TokuCrew
TokuCrew = None  # se define al final del archivo

class NervCrew:
    def __init__(self, empresa, sector, pitch="Tu Solución", vendedor="", url_cliente="", prior_knowledge="", vendor_kb="", log_callback=None, pais="México"):
        self.empresa = empresa
        self.sector = sector
        self.vendedor = vendedor
        self.producto = pitch
        self.url_cliente = url_cliente
        self.prior_knowledge = prior_knowledge
        self.vendor_kb = vendor_kb  # KB genérico para cualquier vendedor (no-Toku)
        self.log_callback = log_callback
        self.base_path = os.path.dirname(__file__)
        self.memory = NervMemory()
        
        # Detección automática de país basada en url_cliente si existe
        self.pais = pais
        if url_cliente:
            url_lower = url_cliente.lower()
            if ".br" in url_lower or "/pt-br" in url_lower or "/pt" in url_lower or "/br/" in url_lower:
                self.pais = "Brasil"
            elif ".mx" in url_lower or "/mx" in url_lower:
                self.pais = "México"
            elif ".co" in url_lower or "/co" in url_lower:
                if not url_lower.endswith(".com") and not ".com/" in url_lower:
                    self.pais = "Colombia"
            elif ".cl" in url_lower or "/cl" in url_lower:
                self.pais = "Chile"
            elif ".pe" in url_lower or "/pe" in url_lower:
                self.pais = "Perú"
            elif ".ar" in url_lower or "/ar" in url_lower:
                self.pais = "Argentina"

        # Obtener gl y hl de PAIS_CODES
        from toku_radar.tools.search import get_pais_codes
        codes = get_pais_codes(self.pais)
        self.gl = codes["gl"]
        self.hl = codes["hl"]
        self.pais_nombre = codes["nombre"]
        
        with open(os.path.join(self.base_path, 'config', 'agents.yaml'), 'r', encoding='utf-8') as f:
            self.agents_config = yaml.safe_load(f)
        with open(os.path.join(self.base_path, 'config', 'tasks.yaml'), 'r', encoding='utf-8') as f:
            self.tasks_config = yaml.safe_load(f)
        
        # Cargar Constitución de NERV OS (reglas universales para todos los agentes)
        constitution_path = os.path.join(self.base_path, 'config', 'constitution.yaml')
        try:
            with open(constitution_path, 'r', encoding='utf-8') as f:
                const_data = yaml.safe_load(f)
            rules = const_data.get('rules', [])
            self.constitution = "LEYES INVIOLABLES DE NERV OS (se aplican en TODAS las respuestas):\n" + "\n".join(
                f"- [{r['id']}] {r['name']}: {r['instruction']}" for r in rules
            )
        except Exception:
            self.constitution = ""  # Graceful fallback si no existe el archivo

    def _discover_subpages(self, url: str) -> List[str]:
        """Descubre subpáginas críticas del dominio para enriquecer el scraping."""
        if not url:
            return []
        try:
            domain = url.replace("https://", "").replace("http://", "").split("?")[0]
            domain_only = domain.split("/")[0]
            
            searcher = SerperSearch()
            if self.hl == "pt":
                q = f'site:{domain_only} (pagamentos OR cobrancas OR tarifas OR preco OR checkout OR "solucoes" OR financeiro)'
            else:
                q = f'site:{domain_only} (pagos OR cobros OR precios OR tarifas OR checkout OR "soluciones" OR finanzas OR pricing)'
            
            results = searcher.search_links(q, gl=self.gl, hl=self.hl, num=6)
            subpages = []
            seen_urls = {url.lower().rstrip('/')}
            
            for item in results:
                link = item.get("link", "")
                if not link:
                    continue
                link_clean = link.lower().rstrip('/')
                if link_clean in seen_urls:
                    continue
                
                if domain_only in link_clean:
                    if any(ext in link_clean for ext in [".pdf", ".png", ".jpg", "/blog/", "/news/", "/noticias/"]):
                        continue
                    subpages.append(link)
                    seen_urls.add(link_clean)
                    if len(subpages) >= 2:
                        break
            return subpages
        except Exception as e:
            logger.error(f"Error descubriendo subpáginas para {url}: {e}")
            return []

    def kickoff(self):
        logger.info(f"Iniciando NERV OS para: {self.empresa} (Vendedor: {self.vendedor})")
        db.log_search(self.empresa, "STARTED")

        # 1. Ingesta Inicial (Con Cache y URL Directa)
        cache_key = f"research_{self.empresa}_{self.url_cliente}_{self.pais}".lower()
        cached_data = cache.get(cache_key)
        
        if cached_data:
            logger.info(f"Usando datos cacheados para {self.empresa}")
            raw_intel = cached_data
        else:
            # Si no hay URL, intentamos auto-resolverla
            if not self.url_cliente:
                searcher = SerperSearch()
                links = searcher.search_links(f"{self.empresa} sitio oficial", gl=self.gl, hl=self.hl, num=1)
                if links:
                    self.url_cliente = links[0].get("link", "")
                    logger.info(f"Auto-resolución de URL para {self.empresa}: {self.url_cliente}")
                    if self.log_callback:
                        self.log_callback(f"⚙️ *NERV OS:* URL oficial auto-detectada: {self.url_cliente}")

            searcher = SerperSearch()
            raw_intel = searcher.research_company(self.empresa, self.sector, self.producto, url=self.url_cliente, pais=self.pais, gl=self.gl, hl=self.hl)
            
            # Raspado de la web oficial del cliente
            website_markdown = ""
            if self.url_cliente:
                try:
                    logger.info(f"Raspando URL oficial de cliente: {self.url_cliente}")
                    if self.log_callback:
                        self.log_callback(f"⚙️ *NERV OS:* Raspando página principal: {self.url_cliente}")
                    scraper = ResilientScraper()
                    home_content = scraper.scrape_url(self.url_cliente)
                    website_markdown = f"# Sitio Web Oficial: {self.url_cliente}\n\n## Página Principal (Home)\n\n{home_content}\n\n"
                    
                    # Descubrir y raspar subpáginas
                    subpages = self._discover_subpages(self.url_cliente)
                    if subpages:
                        logger.info(f"Subpáginas descubiertas para scraping: {subpages}")
                        if self.log_callback:
                            self.log_callback(f"⚙️ *NERV OS:* Subpáginas detectadas: {', '.join(subpages)}")
                        for idx, subpage in enumerate(subpages, 1):
                            try:
                                if self.log_callback:
                                    self.log_callback(f"⚙️ *NERV OS:* Raspando subpágina ({idx}/2): {subpage}")
                                subpage_content = scraper.scrape_url(subpage)
                                website_markdown += f"## Subpágina {idx}: {subpage}\n\n{subpage_content}\n\n"
                            except Exception as sub_err:
                                logger.error(f"Error raspando subpágina {subpage}: {sub_err}")
                except Exception as e:
                    logger.error(f"Error en raspado de url_cliente {self.url_cliente}: {e}")
            
            # Truncar el contenido de scraping para evitar exceder la ventana de tokens de los LLMs (6k-12k TPM)
            max_chars = 12000
            if len(website_markdown) > max_chars:
                logger.info(f"Truncando website_markdown de {len(website_markdown)} a {max_chars} caracteres.")
                website_markdown = website_markdown[:max_chars] + "\n\n[... CONTENIDO TRUNCADO POR LÍMITE DE TAMAÑO ...]"

            raw_intel["website_markdown"] = website_markdown
            cache.set(cache_key, raw_intel)
        
        initial_context = f"CONTEXTO ESTRATÉGICO:\n{raw_intel['contexto_estrategico']}\n\nDOLOR OPERATIVO:\n{raw_intel['dolor_operativo']}\n\nPEOPLE:\n{raw_intel['linkedin_discovery']}"
        if raw_intel.get("website_markdown"):
            web_md = raw_intel['website_markdown']
            max_chars = 12000
            if len(web_md) > max_chars:
                web_md = web_md[:max_chars] + "\n\n[... CONTENIDO TRUNCADO POR SEGURIDAD DE LIMITES ...]"
            initial_context = f"CONTENIDO RASPADO DEL SITIO WEB OFICIAL DEL CLIENTE:\n{web_md}\n\n{initial_context}"
        
        # --- RESOLUCION DE KB DEL VENDEDOR (Dual-Layer: Toku-specific | Genérico) ---
        # Capa 1: Toku (KB integrado en código, activado automáticamente)
        is_toku = "toku" in str(self.vendedor).lower() or "toku" in str(self.producto).lower()
        if is_toku:
            # Cargar dinámicamente las 3 presentaciones de Toku desde la carpeta memory
            memory_dir = PROJECT_ROOT / "memory"
            bienes_text = ""
            ecom_text = ""
            cat_text = ""
            
            bienes_path = memory_dir / "Toku x Bienes de Consumo_raw.md"
            if bienes_path.exists():
                try:
                    bienes_text = bienes_path.read_text(encoding="utf-8").strip()
                except Exception as e:
                    logger.error(f"Error leyendo Toku x Bienes de Consumo_raw.md: {e}")
                    
            ecom_path = memory_dir / "Toku x Ecommerce_raw.md"
            if ecom_path.exists():
                try:
                    ecom_text = ecom_path.read_text(encoding="utf-8").strip()
                except Exception as e:
                    logger.error(f"Error leyendo Toku x Ecommerce_raw.md: {e}")
                    
            cat_path = memory_dir / "Toku x Venta por Catalogo_raw.md"
            if cat_path.exists():
                try:
                    cat_text = cat_path.read_text(encoding="utf-8").strip()
                except Exception as e:
                    logger.error(f"Error leyendo Toku x Venta por Catalogo_raw.md: {e}")
            
            fallback_bienes = "Digitalizar la cobranza B2B con AI Agent, portal de pago y conciliación automática en Consumo Masivo / Bienes de Consumo."
            fallback_ecom = "Unificar adquirencia, métodos, antifraude and conciliación en una sola API para E-commerce & Retail."
            fallback_cat = "Automatizar la cobranza a consultoras con domiciliación recurrente, AI Agent y portal self-service en Venta por Catálogo."
            
            # Determinar vertical principal según el sector del prospecto
            sector_lower = str(self.sector).lower()
            primary_vertical = "No determinada directamente (General/Discovery)"
            primary_content = ""
            
            if any(kw in sector_lower for kw in ["bienes", "consumo", "goods", "distribution", "distribucion", "fmcg", "alimento", "bebida"]):
                primary_vertical = "BIENES DE CONSUMO (Goods / Consumo Masivo B2B)"
                primary_content = bienes_text if bienes_text else fallback_bienes
            elif any(kw in sector_lower for kw in ["ecommerce", "e-commerce", "retail", "tienda", "online", "checkout", "comercio"]):
                primary_vertical = "ECOMMERCE & RETAIL"
                primary_content = ecom_text if ecom_text else fallback_ecom
            elif any(kw in sector_lower for kw in ["catalogo", "catalog", "venta directa", "direct selling", "consultora", "vendedora", "multinivel"]):
                primary_vertical = "VENTA POR CATÁLOGO (Direct Selling)"
                primary_content = cat_text if cat_text else fallback_cat
                
            active_kb = f"""
🧠 CONTEXTO DE FONDO DEL VENDEDOR — TOKU (INFRAESTRUCTURA DE COBROS Y PAGOS B2B/B2C):

A continuación se presenta la información comercial oficial de Toku. Como estratega, debes analizar el sector y los dolores del cliente para alinear la propuesta de valor.

==================================================
1. VERTICAL IDENTIFICADA COMO PRINCIPAL PARA ESTE PROSPECTO:
Vertical: {primary_vertical}

"""
            if primary_content:
                active_kb += f"""--- INICIO DE INFORMACIÓN DE LA VERTICAL PRINCIPAL ---
{primary_content}
--- FIN DE INFORMACIÓN DE LA VERTICAL PRINCIPAL ---
"""
            else:
                active_kb += "No se pre-identificó una vertical exclusiva. Analiza el prospecto y decide cuál de las soluciones de Toku (Bienes de Consumo, E-commerce, o Venta por Catálogo) se adapta mejor.\n"
                
            active_kb += f"""
==================================================
2. CATÁLOGO COMPLETO DE PRESENTACIONES DE TOKU PARA ANÁLISIS CRUZADO:

[PRESENTACIÓN 1: BIENES DE CONSUMO (Goods / Consumo Masivo B2B)]
{bienes_text if bienes_text else "(No se pudo cargar el archivo local)"}

[PRESENTACIÓN 2: ECOMMERCE & RETAIL]
{ecom_text if ecom_text else "(No se pudo cargar el archivo local)"}

[PRESENTACIÓN 3: VENTA POR CATÁLOGO (Direct Selling)]
{cat_text if cat_text else "(No se pudo cargar el archivo local)"}

==================================================
3. POSICIONAMIENTO CLAVE VS COMPETENCIA (Clip, Openpay, Stripe, Conekta, etc.):
- Toku orquesta y complementa, no compite necesariamente. Puede montarse sobre pasarelas existentes.
- Smart Routing / Enrutamiento Inteligente: Si falla un adquirente, cascadea a otro en milisegundos para salvar la venta.
- Reducción de comisiones de hasta el 80%: Redirige cobros recurrentes y de alto ticket a domiciliación o transferencias SPEI con comisiones fijas mínimas frente al 2.5% - 3.6% variable de pasarelas tradicionales.
- Cobranza Activa (AI Agent): Intervención automática e inmediata vía WhatsApp interactivo, SMS o llamadas robotizadas (IVR) cuando un pago es rechazado.
- Conciliación Automática en tiempo real directo al ERP (SAP, NetSuite, etc.), resolviendo el mayor dolor administrativo de finanzas.

==================================================
4. MODELO COMERCIAL Y RESPALDO:
- Modelo: Consultoría experta en pagos + Software as a Service (SaaS).
- Filosofía: Aportamos valor o no cobramos.
- Metodología: 1) Diagnóstico completo → 2) Acompañamiento en contratos bancarios → 3) Definición conjunta de KPIs.
- Respaldo e Inversores: Respaldado por Wollef Capital.
- Seguridad y Cumplimiento: Certificaciones PCI DSS Level 1 y ISO 27001.

NOTA: Este es contexto de fondo para el enjambre de agentes de NERV. Úsalo para estructurar y justificar detalladamente cada sección de la propuesta en el dossier final. NO copies ni cites este bloque textualmente en el entregable final.
"""
        # Capa 2: Vendór genérico (KB inyectado externamente por el usuario)
        elif self.vendor_kb:
            active_kb = f"""
🧠 CONTEXTO DE FONDO DEL VENDEDOR — {self.vendedor.upper()}:

{self.vendor_kb}

NOTA: Este es contexto de fondo. Úsalo para razonar y adaptar argumentos al target.
NO copies ni cites este bloque literalmente en el output.
"""
        else:
            active_kb = ""  # Sin KB específico: los agentes trabajan con la investigación pública

        if active_kb:
            initial_context = f"{active_kb}\n\n{initial_context}"
        
        # --- BLOQUE RLHF: CARGAR EXPERIENCIA PREVIA ---
        experience_context = db.get_recent_feedback(limit=2)
        if experience_context:
            logger.info("🧠 RLHF: Inyectando ejemplos de dossiers aprobados por el usuario.")
            initial_context = f"{experience_context}\n\n{initial_context}"

        if self.prior_knowledge:
            initial_context = f"{initial_context}\n\nCONTEXTO PREVIO/OBJECIONES:\n{self.prior_knowledge}"
            
        # 2. Ejecucion del Enjambre (todos los agentes reciben la Constitution)
        investigador = Agent(self.agents_config['investigador'], log_callback=self.log_callback, engine="deepseek", constitution=self.constitution, gl=self.gl, hl=self.hl)
        res_investigacion = investigador.execute(
            self.tasks_config['tarea_investigacion']['description'].format(
                empresa=self.empresa, 
                sector=self.sector,
                vendedor=self.vendedor,
                producto=self.producto,
                pais=self.pais_nombre
            ),
            context=initial_context
        )
        
        psicologo = Agent(self.agents_config['psicologo'], log_callback=self.log_callback, engine="deepseek", constitution=self.constitution, gl=self.gl, hl=self.hl)
        res_psicologia = psicologo.execute(
            self.tasks_config['tarea_psicologia']['description'].format(
                empresa=self.empresa,
                vendedor=self.vendedor,
                producto=self.producto
            ),
            context=res_investigacion
        )
        
        # Gemelo recibe: DISC profile + research + KB del vendedor (si aplica)
        gemelo_context = f"PERFIL DISC DEL DECISOR:\n{res_psicologia}\n\nINVESTIGACION DE MERCADO:\n{res_investigacion}"
        if active_kb:
            gemelo_context = f"{active_kb}\n\n{gemelo_context}"

        gemelo = Agent(self.agents_config['gemelo_digital'], log_callback=self.log_callback, engine="deepseek", constitution=self.constitution, gl=self.gl, hl=self.hl)
        res_gemelo = gemelo.execute(
            self.tasks_config['tarea_simulacion_gemelo']['description'].format(
                empresa=self.empresa,
                vendedor=self.vendedor,
                producto=self.producto
            ),
            context=gemelo_context
        )
        
        # Estratega recibe todo: investigacion + DISC + simulacion + KB del vendedor
        estratega_context = f"INVESTIGACION:\n{res_investigacion}\n\nPERFIL DISC:\n{res_psicologia}\n\nSIMULACION GEMELO:\n{res_gemelo}"
        if active_kb:
            estratega_context = f"{active_kb}\n\n{estratega_context}"

        estratega = Agent(self.agents_config['estratega'], log_callback=self.log_callback, engine="deepseek", constitution=self.constitution, gl=self.gl, hl=self.hl)
        dossier_preliminar = estratega.execute(
            self.tasks_config['tarea_dossier_final']['description'].format(
                empresa=self.empresa,
                sector=self.sector,
                vendedor=self.vendedor,
                producto=self.producto
            ),
            context=estratega_context
        )

        # Limpieza de corchetes múltiples (ej: [[[[Ecommerce]]]], [[CFO]] -> Ecommerce, CFO)
        import re
        dossier_preliminar = re.sub(r'\[{2,}([^\]\n]+)\]{2,}', r'\1', dossier_preliminar)

        # Limpieza de metadatos técnicos e internos del dossier
        dossier_preliminar = re.sub(r'(?im)^.*?razonamiento del enjambre.*$', '', dossier_preliminar)
        dossier_preliminar = re.sub(r'(?im)^.*?swarm readiness score.*$', '', dossier_preliminar)
        dossier_preliminar = re.sub(r'(?im)^.*?mirofish.*$', '', dossier_preliminar)
        dossier_preliminar = re.sub(r'(?im)^.*?para data engineers?.*$', '', dossier_preliminar)
        dossier_preliminar = re.sub(r'(?im)^.*?gtm swarm.*$', '', dossier_preliminar)
        dossier_preliminar = re.sub(r'(?im)^.*?galileo.*$', '', dossier_preliminar)
        dossier_preliminar = re.sub(r'(?im)^.*?probabilidad de .xito:?\s*\d+%.*$', '', dossier_preliminar)
        # Limpiar líneas vacías consecutivas resultantes
        dossier_preliminar = re.sub(r'\n{3,}', '\n\n', dossier_preliminar).strip()

        # --- FASE 3: ESTRUCTURACION SUPABASE ---
        if self.log_callback: self.log_callback("\n[ AGENT: Ingeniero de Datos - Sincronizando ]")
        data_engineer = Agent(self.agents_config['ingeniero_datos'], log_callback=self.log_callback, engine="deepseek")
        json_output_raw = data_engineer.execute(
            self.tasks_config['tarea_estructuracion_datos']['description'].format(
                empresa=self.empresa,
                vendedor=self.vendedor,
                producto=self.producto
            ),
            context=dossier_preliminar
        )
        
        try:
            # Extraer JSON limpio de la respuesta del agente
            if "```json" in json_output_raw:
                json_str = json_output_raw.split("```json")[-1].split("```")[0].strip()
            elif "```" in json_output_raw:
                json_str = json_output_raw.split("```")[-1].split("```")[0].strip()
            else:
                json_str = json_output_raw.strip()
                
            if json_str:
                structured_data = json.loads(json_str)
                db.upsert_empresa(structured_data)
                logger.info(f"Empresa {self.empresa} sincronizada exitosamente con Supabase (empresas_v3)")
            else:
                logger.warning(f"No se detectó JSON válido en la respuesta del ingeniero de datos.")
        except Exception as e:
            logger.error(f"Error parseando o subiendo JSON a Supabase: {e}")

        # 4. Protocolos de Veracidad
        try:
            auditor = VeracityAuditor()
            audit_res = auditor.audit_fact(dossier_preliminar, res_investigacion)
        except Exception as aud_err:
            logger.error(f"Error en Protocolo de Veracidad: {aud_err}")
            audit_res = f"Protocolo de Veracidad omitido por razones técnicas: {aud_err}"
        
        clean_output = f"""
# 🚀 NERV Intelligence Report: {self.empresa}
{dossier_preliminar}

---
## 🛡️ Protocolo de Veracidad
{audit_res}
"""
        clean_output = re.sub(r'\[{2,}([^\]\n]+)\]{2,}', r'\1', clean_output)
        clean_output = re.sub(r'(?im)^.*?razonamiento del enjambre.*$', '', clean_output)
        clean_output = re.sub(r'(?im)^.*?swarm readiness score.*$', '', clean_output)
        clean_output = re.sub(r'(?im)^.*?mirofish.*$', '', clean_output)
        clean_output = re.sub(r'(?im)^.*?para data engineers?.*$', '', clean_output)
        clean_output = re.sub(r'(?im)^.*?gtm swarm.*$', '', clean_output)
        clean_output = re.sub(r'(?im)^.*?galileo.*$', '', clean_output)
        clean_output = re.sub(r'(?im)^.*?probabilidad de .xito:?\s*\d+%.*$', '', clean_output)
        clean_output = re.sub(r'\n{3,}', '\n\n', clean_output).strip()

        db.log_search(self.empresa, "COMPLETED")
        self.memory.save_dossier(self.empresa, self.sector, clean_output)
        
        return clean_output

# Alias de retrocompatibilidad — evita romper imports que usen TokuCrew
TokuCrew = NervCrew

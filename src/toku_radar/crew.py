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

from toku_radar.tools.search import SerperSearch
from toku_radar.tools.resilient_scraper import ResilientScraper
from toku_radar.tools.wiki import get_company_profile
from toku_radar.tools.auditor import GalileoAuditor
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
    def __init__(self, config, log_callback=None, engine="groq"):
        self.role = config['role']
        self.goal = config['goal']
        self.backstory = config['backstory']
        self.log_callback = log_callback
        self.engine = engine
        
        if self.engine == "deepseek":
            self.rotator = DeepSeekClient(log_callback=self.log_callback)
            self.model_planning = "deepseek-chat"
            self.model_final = "deepseek-chat"
        elif self.engine == "hermes":
            self.rotator = HermesClient(log_callback=self.log_callback)
            self.model_planning = "nousresearch/hermes-4-70b"
            self.model_final = "nousresearch/hermes-4-70b"
        else:
            self.rotator = GroqRotator(log_callback=self.log_callback)
            self.model_planning = "llama-3.1-8b-instant"
            self.model_final = "llama-3.3-70b-versatile"
        
        self.search_tool = SerperSearch()
        self.firecrawl_tool = ResilientScraper()
        self.memory = NervMemory()

    def _execute_tool(self, plan_text, task_desc):
        """Lógica de decisión de herramienta avanzada (Google Suite + Fallbacks)."""
        plan_lower = plan_text.lower()
        msg = ""
        res = ""

        if "news" in plan_lower or "noticias" in plan_lower:
            msg = "## Action: Serper Strategic News"
            res = self.search_tool._query(f"{task_desc} news 2024 2025")
        elif "maps" in plan_lower or "reseñas" in plan_lower or "sentiment" in plan_lower:
            msg = "## Action: Standard Search (Maps Disabled)"
            res = self.search_tool._query(f"{task_desc} news reviews")
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
            res = self.search_tool._query(task_desc)
        
        if self.log_callback: self.log_callback(f"  {msg}")
        return res

    @retry_with_backoff(retries=3, backoff_in_seconds=2)
    def execute(self, task_desc, context=""):
        logger.info(f"Agente {self.role} iniciando razonamiento Hermes...")
        if self.log_callback: self.log_callback(f"\n[ AGENT: {self.role} ]")
        
        past_intelligence = self.memory.search_similar_cases(context[:100])
        
        # BUCLE DE RAZONAMIENTO ESTILO HERMES 3
        full_conversation = [
            {"role": "system", "content": f"""Eres {self.role}. {self.backstory}
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
        if self.log_callback: self.log_callback(f"  ## Pensamiento: {thought_process[:200]}...")

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
    def __init__(self, empresa, sector, pitch="Tu Solución", vendedor="", url_cliente="", prior_knowledge="", log_callback=None):
        self.empresa = empresa
        self.sector = sector
        self.vendedor = vendedor
        self.producto = pitch # Usamos pitch como el producto/solución
        self.url_cliente = url_cliente
        self.prior_knowledge = prior_knowledge
        self.log_callback = log_callback
        self.base_path = os.path.dirname(__file__)
        self.memory = NervMemory()
        
        with open(os.path.join(self.base_path, 'config', 'agents.yaml'), 'r', encoding='utf-8') as f:
            self.agents_config = yaml.safe_load(f)
        with open(os.path.join(self.base_path, 'config', 'tasks.yaml'), 'r', encoding='utf-8') as f:
            self.tasks_config = yaml.safe_load(f)

    def kickoff(self):
        logger.info(f"Iniciando NERV OS para: {self.empresa} (Vendedor: {self.vendedor})")
        db.log_search(self.empresa, "STARTED")

        # 1. Ingesta Inicial (Con Cache y URL Directa)
        cache_key = f"research_{self.empresa}_{self.url_cliente}".lower()
        cached_data = cache.get(cache_key)
        
        if cached_data:
            logger.info(f"Usando datos cacheados para {self.empresa}")
            raw_intel = cached_data
        else:
            searcher = SerperSearch()
            raw_intel = searcher.research_company(self.empresa, self.sector, self.producto, url=self.url_cliente)
            
            # Raspado de la web oficial del cliente
            website_markdown = ""
            if self.url_cliente:
                try:
                    logger.info(f"Raspando URL oficial de cliente: {self.url_cliente}")
                    scraper = ResilientScraper()
                    website_markdown = scraper.scrape_url(self.url_cliente)
                except Exception as e:
                    logger.error(f"Error en raspado de url_cliente {self.url_cliente}: {e}")
            
            raw_intel["website_markdown"] = website_markdown
            cache.set(cache_key, raw_intel)
        
        initial_context = f"CONTEXTO ESTRATÉGICO:\n{raw_intel['contexto_estrategico']}\n\nDOLOR OPERATIVO:\n{raw_intel['dolor_operativo']}\n\nPEOPLE:\n{raw_intel['linkedin_discovery']}"
        if raw_intel.get("website_markdown"):
            initial_context = f"CONTENIDO RASPADO DEL SITIO WEB OFICIAL DEL CLIENTE:\n{raw_intel['website_markdown']}\n\n{initial_context}"
        
        # --- INYECCIÓN DE PROPUESTA DE VALOR OFICIAL DE TOKU ---
        toku_kb = ""
        is_toku = "toku" in str(self.vendedor).lower() or "toku" in str(self.producto).lower()
        if is_toku:
            toku_kb = """
🧠 TOKU OFFICIAL VALUE PROPOSITION & KNOWLEDGE BASE:

1. VERTICAL: BIENES DE CONSUMO (Goods / Consumo Masivo B2B)
   - DOLORES / PAIN POINTS PRINCIPALES:
     * Cobranza no digitalizada en canal tradicional (changarros, tienditas pagan en efectivo o transferencia sin trazabilidad).
     * Cobranza manual a distribuidores (costo operativo alto, DSO elevado, cartera vencida que crece sin control).
     * Crédito sin trazabilidad en tiempo real sobre comportamiento de pago.
     * Conciliación manual (pagos de múltiples canales sin aplicación automática en ERP, cierre contable lento y errores).
   - PROPUESTA DE VALOR DE TOKU:
     * Digitalizamos la cobranza B2B con AI Agent, portal de pago y conciliación automática.
     * Conexión única entre sistemas del cliente (ERP/Core Distribución, Sistema de Crédito, Base de Clientes, Core Financiero) con todos los rieles de pago en México:
       - Domiciliación bancaria recurrente (BBVA, Santander, Banamex, Banorte, HSBC, Inbursa, Scotiabank).
       - Pagos con tarjeta (Débito y crédito, one-time y recurrente Visa, Mastercard, American Express).
       - Efectivo en corresponsales (OXXO, 7-Eleven, Farmacias del Ahorro, Telecomm, Walmart).
       - Transferencias conciliadas (SPEI con aplicación automática: CoDi, SPEI, Banregio, STP).
       - Métodos alternativos (BNPL, wallets y pagos digitales: Aplazo, Kueski, Klarna, PayPal, Apple Pay, MercadoPago).
     * Habilitadores clave: Reintentos inteligentes y orquestación, Fallback automático, Antifraude + 3DS2, Conciliación automática y reportería, AI Agent de cobranza, Portal de pago por liga.

2. VERTICAL: ECOMMERCE & RETAIL
   - DOLORES / PAIN POINTS PRINCIPALES:
     * Tasa de aprobación subóptima (rechazos innecesarios por falta de orquestación inteligente de adquirentes y sin fallback automático).
     * Fraude vs Conversión (sin motor adaptativo hay contracargos altos o fricción excesiva; requiere 3DS2 inteligente).
     * Integraciones fragmentadas (cada método de pago es un conector distinto, mantenimiento caro, lento time-to-market).
     * Conciliación manual (pagos capturados sin reflejo automático en ERP/OMS).
   - PROPUESTA DE VALOR DE TOKU:
     * Unificamos adquirencia, métodos, antifraude y conciliación en una sola integración (una API conectable).
     * Conecta plataformas (Storefront, ERP/OMS, CRM, Core de Pagos) con todos los rieles (Tarjetas, Domiciliación, SPEI, Corresponsales y métodos alternativos).

3. VERTICAL: VENTA POR CATÁLOGO (Direct Selling)
   - DOLORES / PAIN POINTS PRINCIPALES:
     * DSO alto y cartera vencida de consultoras (compran a crédito y pagan tarde/no pagan, sin visibilidad ni automatización).
     * Venta a crédito sin domiciliación (top vendedoras con alto volumen sin mecanismo de cobro automático recurrente, dependiendo de recordatorios manuales).
     * Sin herramientas digitales para la fuerza de venta (consultoras y líderes sin acceso digital a su estado de cuenta o autoservicio).
     * Conciliación manual (abonos de múltiples canales sin aplicación automática en el sistema de pedidos, errores).
   - PROPUESTA DE VALOR DE TOKU:
     * Automatizamos la cobranza a consultoras con domiciliación recurrente, AI Agent (WhatsApp/SMS/IVR) y portal self-service para consultoras.
     * Rieles: Domiciliación recurrente, tarjetas, corresponsales físicos, transferencias y wallets.

4. COMPARATIVA / POSICIONAMIENTO VS PASARELAS Y AGREGADORES TRADICIONALES (Clip, Openpay, Stripe, Conekta, etc.)
   - OBJECIÓN COMÚN DEL PROSPECTO: "Ya cobramos con tarjeta / SPEI / OXXO usando Clip o Openpay. No necesitamos a Toku."
   - RESPUESTA ESTRATÉGICA / DIFERENCIADOR CLAVE DE TOKU:
     * TOKU ORQUESTA, NO COMPITE DIRECTAMENTE: Toku no es solo una pasarela de pago; es una plataforma de orquestación y automatización de cobranza. Se puede integrar por encima de pasarelas como Clip o Openpay para complementarlas.
     * CASCADEO INTELIGENTE (SMART ROUTING): Si Clip o Openpay sufren una caída o rechazan una tarjeta (falso positivo), Toku cascadea automáticamente la transacción a otra pasarela en milisegundos para garantizar la aprobación.
     * REDUCCIÓN DE COMISIONES (DOMICILIACIÓN Y SPEI): Clip/Openpay cobran comisiones porcentuales (2.5% a 3.6%+). Toku redirige los cobros recurrentes hacia Domiciliación Bancaria y transferencias SPEI automatizadas con costos fijos mínimos (centavos o pocos pesos), reduciendo costos financieros hasta un 80%.
     * COBRANZA ACTIVA AUTOMATIZADA (AI AGENT): Cuando un pago falla en una pasarela tradicional, la transacción rebota y ahí termina. Toku detecta la falla al instante y activa un AI Agent (WhatsApp, SMS, IVR) que se comunica con el cliente final para gestionar el pago y ofrecerle un link de pago con métodos alternativos.
     * CONCILIACIÓN AUTOMÁTICA EN ERP: Toku automatiza todo el proceso de conciliación bancaria y contable directamente en el ERP del cliente (ej. SAP, NetSuite), algo que las pasarelas estándar no hacen.

5. ACERCAMIENTO CONSULTIVO Y MODELO COMERCIAL DE TOKU
   - MODELO Y FILOSOFÍA COMERCIAL:
     * Modelo de Negocio: Consultoría + SaaS. No vendemos un software cerrado, sino que acompañamos a cada cliente como consultores de pagos para rediseñar su operación de cobros.
     * Compromiso de Valor Real ("Aportar valor o no cobramos"): Si no generamos valor medible en la operación del cliente, no cobramos.
   - METODOLOGÍA DE TRABAJO:
     * 01. Diagnóstico: Evaluación exhaustiva y detallada del proceso y flujos de cobro actuales para encontrar dónde aportar valor real.
     * 02. Acompañamiento: Soporte continuo durante todo el proceso, incluyendo la apertura de cada método de pago y asegurando que las condiciones contractuales respondan a las necesidades del cliente.
     * 03. Definición: En conjunto se definen KPIs prioritarios, tiempos de implementación convenientes y métricas de éxito trazables y medibles desde el primer mes.
   - RESPALDO, INVERSORES Y CERTIFICACIONES:
     * Respaldados por inversores de primer nivel como Wollef Capital.
     * Certificaciones de seguridad empresarial: PCI DSS Level 1 (estándar máximo de seguridad en la industria de pagos) e ISO 27001 (estándar internacional de gestión de seguridad de la información).
"""
            initial_context = f"{toku_kb}\n\n{initial_context}"
        
        # --- BLOQUE RLHF: CARGAR EXPERIENCIA PREVIA ---
        experience_context = db.get_recent_feedback(limit=2)
        if experience_context:
            logger.info("🧠 RLHF: Inyectando ejemplos de dossiers aprobados por el usuario.")
            initial_context = f"{experience_context}\n\n{initial_context}"

        if self.prior_knowledge:
            initial_context = f"{initial_context}\n\nCONTEXTO PREVIO/OBJECIONES:\n{self.prior_knowledge}"
            
        # 2. Ejecucion del Enjambre
        investigador = Agent(self.agents_config['investigador'], log_callback=self.log_callback, engine="groq")
        res_investigacion = investigador.execute(
            self.tasks_config['tarea_investigacion']['description'].format(
                empresa=self.empresa, 
                sector=self.sector,
                vendedor=self.vendedor,
                producto=self.producto
            ),
            context=initial_context
        )
        
        psicologo = Agent(self.agents_config['psicologo'], log_callback=self.log_callback, engine="deepseek")
        res_psicologia = psicologo.execute(
            self.tasks_config['tarea_psicologia']['description'].format(
                empresa=self.empresa,
                vendedor=self.vendedor,
                producto=self.producto
            ),
            context=res_investigacion
        )
        
        gemelo_context = f"PERFIL: {res_psicologia}\nNOTICIAS: {res_investigacion}"
        if is_toku:
            gemelo_context = f"{toku_kb}\n\n{gemelo_context}"

        gemelo = Agent(self.agents_config['gemelo_digital'], log_callback=self.log_callback, engine="deepseek")
        res_gemelo = gemelo.execute(
            self.tasks_config['tarea_simulacion_gemelo']['description'].format(
                empresa=self.empresa,
                vendedor=self.vendedor,
                producto=self.producto
            ),
            context=gemelo_context
        )
        
        estratega_context = f"INVEST: {res_investigacion}\nPSICO: {res_psicologia}\nTWIN: {res_gemelo}"
        if is_toku:
            estratega_context = f"{toku_kb}\n\n{estratega_context}"

        estratega = Agent(self.agents_config['estratega'], log_callback=self.log_callback, engine="deepseek")
        dossier_preliminar = estratega.execute(
            self.tasks_config['tarea_dossier_final']['description'].format(
                empresa=self.empresa,
                sector=self.sector,
                vendedor=self.vendedor,
                producto=self.producto
            ),
            context=estratega_context
        )

        # --- FASE 3: ESTRUCTURACION SUPABASE ---
        if self.log_callback: self.log_callback("\n[ AGENT: Ingeniero de Datos - Sincronizando ]")
        data_engineer = Agent(self.agents_config['ingeniero_datos'], log_callback=self.log_callback, engine="groq")
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

        # 4. Protocolos Galileo & MiroFish
        auditor = GalileoAuditor()
        audit_res = auditor.audit_fact(dossier_preliminar, res_investigacion)
        
        clean_output = f"""
# 🚀 NERV Intelligence Report: {self.empresa}
{dossier_preliminar}

---
## 🛡️ Auditoría Galileo
{audit_res}
"""
        db.log_search(self.empresa, "COMPLETED")
        self.memory.save_dossier(self.empresa, self.sector, clean_output)
        
        return clean_output

# Alias de retrocompatibilidad — evita romper imports que usen TokuCrew
TokuCrew = NervCrew

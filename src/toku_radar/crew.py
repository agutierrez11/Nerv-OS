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
from toku_radar.tools.firecrawl_tool import FirecrawlTool
from toku_radar.tools.wiki import get_company_profile
from toku_radar.tools.auditor import GalileoAuditor
from toku_radar.tools.miro_predictor import MiroPredictor
from toku_radar.tools.memory import TokuMemory
from toku_radar.tools.groq_rotator import GroqRotator
from toku_radar.tools.deepseek_client import DeepSeekClient
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
        else:
            self.rotator = GroqRotator(log_callback=self.log_callback)
            self.model_planning = "llama-3.1-8b-instant"
            self.model_final = "llama-3.3-70b-versatile"
        
        self.search_tool = SerperSearch()
        self.firecrawl_tool = FirecrawlTool()
        self.memory = TokuMemory()

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
            msg = "## Action: Firecrawl Deep Scraping"
            res = "Resultado de scraping profundo..."
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

class TokuCrew:
    def __init__(self, empresa, sector, pitch="Solución de Pagos", vendedor="Toku", url_cliente="", prior_knowledge="", log_callback=None):
        self.empresa = empresa
        self.sector = sector
        self.vendedor = vendedor
        self.producto = pitch # Usamos pitch como el producto/solución
        self.url_cliente = url_cliente
        self.prior_knowledge = prior_knowledge
        self.log_callback = log_callback
        self.base_path = os.path.dirname(__file__)
        self.memory = TokuMemory()
        
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
            # Pasamos la URL para una búsqueda más precisa
            raw_intel = searcher.research_company(self.empresa, self.sector, self.producto, url=self.url_cliente)
            cache.set(cache_key, raw_intel)
        
        initial_context = f"CONTEXTO ESTRATÉGICO:\n{raw_intel['contexto_estrategico']}\n\nDOLOR OPERATIVO:\n{raw_intel['dolor_operativo']}\n\nPEOPLE:\n{raw_intel['linkedin_discovery']}"
        
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
        
        gemelo = Agent(self.agents_config['gemelo_digital'], log_callback=self.log_callback, engine="deepseek")
        res_gemelo = gemelo.execute(
            self.tasks_config['tarea_simulacion_gemelo']['description'].format(
                empresa=self.empresa,
                vendedor=self.vendedor,
                producto=self.producto
            ),
            context=f"PERFIL: {res_psicologia}\nNOTICIAS: {res_investigacion}"
        )
        
        estratega = Agent(self.agents_config['estratega'], log_callback=self.log_callback, engine="deepseek")
        dossier_preliminar = estratega.execute(
            self.tasks_config['tarea_dossier_final']['description'].format(
                empresa=self.empresa,
                sector=self.sector,
                vendedor=self.vendedor,
                producto=self.producto
            ),
            context=f"INVEST: {res_investigacion}\nPSICO: {res_psicologia}\nTWIN: {res_gemelo}"
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

import yaml
import os
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

from toku_radar.tools.search import SerperSearch
from toku_radar.tools.firecrawl_tool import FirecrawlTool
from toku_radar.tools.wiki import get_company_profile
from toku_radar.tools.auditor import GalileoAuditor
from toku_radar.tools.miro_predictor import MiroPredictor
from toku_radar.tools.memory import TokuMemory
from toku_radar.tools.groq_rotator import GroqRotator
from toku_radar.tools.deepseek_client import DeepSeekClient

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
        """Lógica de decisión de herramienta basada en el plan dinámico."""
        if "firecrawl" in plan_text.lower() or "scrape" in plan_text.lower():
            msg = "## Action: Firecrawl Deep Scraping"
            res = "Resultado de scraping profundo..." # Placeholder para ahorro de tiempo
        elif "wiki" in plan_text.lower():
            msg = "## Action: Wikipedia lookup"
            res = get_company_profile(task_desc[:30])
        else:
            msg = "## Action: Serper Search"
            res = self.search_tool._query(task_desc)
        
        if self.log_callback: self.log_callback(f"  {msg}")
        return res

    @retry_with_backoff(retries=3, backoff_in_seconds=2)
    def execute(self, task_desc, context=""):
        logger.info(f"Agente {self.role} iniciando tarea: {task_desc[:50]}...")
        if self.log_callback: self.log_callback(f"\n[ AGENT: {self.role} ]")
        
        # 1. CONSULTA A LA MEMORIA (Knowledge Base Style)
        past_intelligence = self.memory.search_similar_cases(context[:100])

        # 2. PLANIFICACIÓN DINÁMICA (Hermes Style)
        planning_prompt = f"""
        Eres {self.role}. Tu meta es {self.goal}.
        Tarea actual: {task_desc}
        Contexto previo: {context}
        Inteligencia en Memoria: {past_intelligence}
        
        PLAN (Hermes Reasoning): Explica qué buscarás y por qué, considerando lo que ya sabemos.
        """
        
        resp = llm_breaker.call(self.rotator.create_completion,
            model=self.model_planning,
            messages=[{"role": "user", "content": planning_prompt}],
            temperature=0.3
        )
        plan = resp.choices[0].message.content
        if self.log_callback: self.log_callback(f"  ## Pensamiento: {plan[:200]}...")

        # 3. EJECUCIÓN Y RESPUESTA FINAL
        if "investigador" in self.role.lower() or "gemelo" in self.role.lower() or "firecrawl" in plan.lower() or "search" in plan.lower():
            observation = self._execute_tool(plan, task_desc)
        else:
            observation = "Usando contexto previo y análisis deductivo."
        
        final_prompt = f"Genera el entregable final para: {task_desc}. Plan: {plan}. Obs: {observation}. Contexto: {context}"
        
        final_resp = llm_breaker.call(self.rotator.create_completion,
            model=self.model_final,
            messages=[{"role": "user", "content": final_prompt}],
            temperature=0.2
        )
        return final_resp.choices[0].message.content

class TokuCrew:
    def __init__(self, empresa, sector, pitch, prior_knowledge="", log_callback=None):
        self.empresa = empresa
        self.sector = sector
        self.pitch = pitch
        self.prior_knowledge = prior_knowledge
        self.log_callback = log_callback
        self.base_path = os.path.dirname(__file__)
        self.memory = TokuMemory()
        
        with open(os.path.join(self.base_path, 'config', 'agents.yaml'), 'r', encoding='utf-8') as f:
            self.agents_config = yaml.safe_load(f)
        with open(os.path.join(self.base_path, 'config', 'tasks.yaml'), 'r', encoding='utf-8') as f:
            self.tasks_config = yaml.safe_load(f)

    def kickoff(self):
        logger.info(f"Iniciando NERV OS para: {self.empresa}")
        db.log_search(self.empresa, "STARTED")

        # 1. Ingesta Inicial (Con Cache)
        cache_key = f"research_{self.empresa}_{self.sector}".lower()
        cached_data = cache.get(cache_key)
        
        if cached_data:
            logger.info(f"Usando datos cacheados para {self.empresa}")
            raw_intel = cached_data
        else:
            searcher = SerperSearch()
            raw_intel = searcher.research_company(self.empresa, self.sector, self.pitch)
            cache.set(cache_key, raw_intel)
        
        initial_context = str(raw_intel['contexto_estrategico'])
        if self.prior_knowledge:
            self.memory.save_objection(self.empresa, self.sector, self.prior_knowledge)
            
        past_objections = self.memory.search_objections(self.sector)
        if self.prior_knowledge or past_objections:
            initial_context = f"MEMORIA RAG:\n{past_objections}\nObjecion: {self.prior_knowledge}\n\nINTEL:\n{initial_context}"
            
        # 2. Ejecucion del Enjambre
        investigador = Agent(self.agents_config['investigador'], log_callback=self.log_callback, engine="groq")
        res_investigacion = investigador.execute(
            self.tasks_config['tarea_investigacion']['description'].format(empresa=self.empresa, sector=self.sector),
            context=initial_context
        )
        
        psicologo = Agent(self.agents_config['psicologo'], log_callback=self.log_callback, engine="deepseek")
        res_psicologia = psicologo.execute(
            self.tasks_config['tarea_psicologia']['description'].format(empresa=self.empresa),
            context=res_investigacion
        )
        
        gemelo = Agent(self.agents_config['gemelo_digital'], log_callback=self.log_callback, engine="deepseek")
        res_gemelo = gemelo.execute(
            self.tasks_config['tarea_simulacion_gemelo']['description'].format(empresa=self.empresa),
            context=f"PERFIL: {res_psicologia}\nNOTICIAS: {res_investigacion}"
        )
        
        estratega = Agent(self.agents_config['estratega'], log_callback=self.log_callback, engine="deepseek")
        dossier_preliminar = estratega.execute(
            self.tasks_config['tarea_dossier_final']['description'],
            context=f"INVEST: {res_investigacion}\nPSICO: {res_psicologia}\nTWIN: {res_gemelo}"
        )

        # --- FASE 3: ESTRUCTURACION SUPABASE (NERV 2.0) ---
        if self.log_callback: self.log_callback("\n[ AGENT: Ingeniero de Datos - Sincronizando con Supabase ]")
        data_engineer = Agent(self.agents_config['ingeniero_datos'], log_callback=self.log_callback, engine="groq")
        json_output_raw = data_engineer.execute(
            self.tasks_config['tarea_estructuracion_datos']['description'].format(empresa=self.empresa),
            context=dossier_preliminar
        )
        
        try:
            # Extraer JSON limpio de la respuesta del agente
            json_str = json_output_raw.split("```json")[-1].split("```")[0].strip() if "```json" in json_output_raw else json_output_raw
            structured_data = json.loads(json_str)
            db.upsert_empresa(structured_data)
            logger.info(f"Empresa {self.empresa} sincronizada exitosamente con Supabase (empresas_v3)")
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

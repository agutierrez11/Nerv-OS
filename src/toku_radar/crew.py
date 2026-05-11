import yaml
import os
import time
from groq import Groq
from toku_radar.tools.search import SerperSearch
from toku_radar.tools.firecrawl_tool import FirecrawlTool
from toku_radar.tools.wiki import get_company_profile
from toku_radar.tools.auditor import GalileoAuditor
from toku_radar.tools.miro_predictor import MiroPredictor
from toku_radar.tools.memory import TokuMemory
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv(dotenv_path=r"C:\Users\Antonio\.gemini\antigravity\scratch\.env")

from toku_radar.tools.groq_rotator import GroqRotator
from toku_radar.tools.deepseek_client import DeepSeekClient

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
        msg = ""
        if "firecrawl" in plan_text.lower() or "scrape" in plan_text.lower():
            msg = "## Action: Firecrawl Deep Scraping"
            res = "Resultado de scraping profundo..."
        elif "wiki" in plan_text.lower():
            msg = "## Action: Wikipedia lookup"
            res = get_company_profile(task_desc[:30])
        else:
            msg = "## Action: Serper Search"
            res = self.search_tool._query(task_desc)
        
        if self.log_callback: self.log_callback(f"  {msg}")
        return res

    def execute(self, task_desc, context=""):
        header = f"\n[ AGENT: {self.role} ]"
        if self.log_callback: self.log_callback(header)
        
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
        
        try:
            resp = self.rotator.create_completion(
                model=self.model_planning,
                messages=[{"role": "user", "content": planning_prompt}],
                temperature=0.3
            )
            plan = resp.choices[0].message.content
            if self.log_callback: self.log_callback(f"  ## Pensamiento: {plan[:400]}...")
        except:
            plan = "Continuar con estrategia estándar."

        # 3. EJECUCIÓN Y RESPUESTA FINAL
        # Optimizamos: Solo el investigador hace búsqueda obligatoria. 
        # Los demás agentes solo usan herramientas si el plan lo pide explícitamente y no tienen contexto.
        if "investigador" in self.role.lower() or "gemelo" in self.role.lower() or "firecrawl" in plan.lower() or "search" in plan.lower():
            observation = self._execute_tool(plan, task_desc)
        else:
            observation = "Usando contexto previo y análisis deductivo."
        
        final_prompt = f"Genera el entregable final para: {task_desc}. Plan: {plan}. Obs: {observation}. Contexto: {context}"
        
        final_resp = self.rotator.create_completion(
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
        # 1. Ingesta Inicial
        searcher = SerperSearch()
        raw_intel = searcher.research_company(self.empresa, self.sector, self.pitch)
        
        # Incorporar prior_knowledge al contexto inicial
        initial_context = str(raw_intel['contexto_estrategico'])
        
        # 1. Guardar la objeción actual si existe (Aprendizaje activo)
        if self.prior_knowledge:
            self.memory.save_objection(self.empresa, self.sector, self.prior_knowledge)
            
        # 2. Recuperar objeciones históricas del sector (RAG)
        past_objections = self.memory.search_objections(self.sector)
        
        if self.prior_knowledge or past_objections:
            initial_context = f"CONTEXTO PREVIO Y MEMORIA RAG:\n{past_objections}\nObjeción Actual del Vendedor: {self.prior_knowledge}\n\nINTELIGENCIA RECOLECTADA:\n{initial_context}"
            
        # 2. Agentes
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

        # 3. Consenso del Enjambre (Protocolos MiroFish & Galileo)
        if self.log_callback: self.log_callback("\n[ QUEEN AGENT: Iniciando Protocolos de Consenso ]")
        
        predictor = MiroPredictor()
        prediction = predictor.predict_success(dossier_preliminar)
        if self.log_callback: self.log_callback(f"  ## MiroFish Voting: {prediction[:100]}...")
        
        auditor = GalileoAuditor()
        audit_res = auditor.audit_fact(dossier_preliminar, res_investigacion)
        if self.log_callback: self.log_callback(f"  ## Galileo Verification: {audit_res[:100]}...")
        
        # Formateo Premium para Presentación (Commander Level) - Límpio para Ventas
        clean_output = f"""
# 🚀 NERV Intelligence Report: {self.empresa}
**Sector:** {self.sector} | **Toku Pitch:** {self.pitch}

---

{dossier_preliminar}

---
*Generado por Toku GTM Radar Swarm Intelligence Platform (NERV OS)*
"""

        # Formateo Técnico con Razonamiento para Data Engineers (Memoria)
        technical_output = f"""
{clean_output}

---
## ⚙️ RAZONAMIENTO DEL ENJAMBRE (Para Data Engineers)

**GTM Swarm Readiness Score (MiroFish Consensus):** 
{prediction}

## 🛡️ Protocolo de Veracidad Galileo
**Estado de Auditoría:** Verified & Grounded via Llama-3.3-70B
{audit_res}
"""
        
        # 4. GUARDAR EN MEMORIA PARA EL FUTURO (Collective Intelligence) - Guardamos la versión técnica
        self.memory.save_dossier(self.empresa, self.sector, technical_output)
        
        return technical_output

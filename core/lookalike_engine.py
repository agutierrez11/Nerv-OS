"""
lookalike_engine.py — NERV OS Lookalike Generation Engine
Dos vectores:
  1. direct   → empresas similares a un cliente exitoso (by profile)
  2. competitor → extrae clientes de competidores y los intercepta
"""
import os
import json
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from langchain_core.messages import SystemMessage, HumanMessage
from core.llm_loader import get_llm
from tools.search import SerperSearch
from tools.firecrawl_tool import FirecrawlTool
from tools.competitor_intel import CompetitorIntelTool
from core.icp_store import icp_store
from core.database import db

# Cargar entorno
load_dotenv()

# ── LLM (reutiliza el mismo modelo que crew_engine) ──────────────────────────
llm = get_llm(temperature=0.1)

search_tool    = SerperSearch()
firecrawl_tool = FirecrawlTool()
competitor_tool = CompetitorIntelTool()

# ── Helpers ───────────────────────────────────────────────────────────────────

def _llm_call(system: str, human: str) -> str:
    try:
        resp = llm.invoke([
            SystemMessage(content=system),
            HumanMessage(content=human)
        ])
        return resp.content
    except Exception as e:
        return f"[LLM ERROR: {e}]"


def _extract_json(text: str) -> Any:
    """Extrae el primer bloque JSON válido de un string."""
    import re
    match = re.search(r"```json\s*([\s\S]+?)\s*```", text)
    if match:
        try:
            return json.loads(match.group(1))
        except Exception:
            pass
    # Intento directo
    try:
        return json.loads(text)
    except Exception:
        return None


# ── Agentes internos ──────────────────────────────────────────────────────────

class ICPExtractorAgent:
    """Sintetiza el perfil ICP a partir de una empresa base."""

    def run(self, empresa: str, sector: str = "", extra_context: str = "") -> Dict:
        prompt = f"""Analiza esta empresa y extrae su perfil ICP (Ideal Customer Profile).
Empresa: {empresa}
Sector declarado: {sector}
Contexto adicional: {extra_context}

Devuelve SOLO un JSON con este esquema:
```json
{{
  "sector": "...",
  "tamaño": "startup|pyme|midmarket|enterprise",
  "señales_clave": ["señal1", "señal2"],
  "queries_busqueda": ["query para Serper 1", "query para Serper 2"],
  "palabras_clave_negativas": ["evitar1", "evitar2"]
}}
```"""
        raw = _llm_call(
            "Eres un experto en GTM y análisis de ICP. Responde SOLO en JSON válido.",
            prompt
        )
        result = _extract_json(raw)
        return result or {
            "sector": sector,
            "tamaño": "pyme",
            "señales_clave": [],
            "queries_busqueda": [f"empresas similares a {empresa} {sector}"],
            "palabras_clave_negativas": []
        }


class ProspectorAgent:
    """Busca empresas que encajan con el ICP y extrae señales básicas."""

    def run(self, icp_profile: Dict, max_results: int = 15) -> List[Dict]:
        queries = icp_profile.get("queries_busqueda", [])
        all_results = []

        for query in queries[:3]:  # max 3 búsquedas para no agotar cuota
            try:
                raw = search_tool.search(query)
                results = raw if isinstance(raw, list) else []
                for r in results[:5]:
                    all_results.append({
                        "empresa": r.get("title", "").split(" - ")[0].strip(),
                        "snippet": r.get("snippet", ""),
                        "url": r.get("link", ""),
                        "fuente_query": query
                    })
            except Exception:
                pass

        # Deduplicar por nombre
        seen = set()
        unique = []
        for r in all_results:
            key = r["empresa"].lower()
            if key and key not in seen:
                seen.add(key)
                unique.append(r)

        return unique[:max_results]


class ScorerAgent:
    """Puntúa cada prospecto de 0-100 respecto al ICP."""

    def run(self, prospects: List[Dict], icp_profile: Dict, pitch: str = "") -> List[Dict]:
        if not prospects:
            return []

        # Agregar ID numérico temporal
        prospects_with_id = []
        for idx, p in enumerate(prospects):
            prospects_with_id.append({**p, "temp_id": idx + 1})

        prospects_text = "\n".join(
            f"ID: {p['temp_id']} | Empresa: {p['empresa']} | Cita/Snippet: {p.get('snippet', '')}" 
            for p in prospects_with_id
        )
        icp_text = json.dumps(icp_profile, ensure_ascii=False)

        prompt = f"""Eres un Sales Ops expert. Tu trabajo es evaluar una lista de prospectos B2B y calificarlos de 0 a 100 respecto al ICP (Perfil de Cliente Ideal) provisto.

ICP de Referencia:
{icp_text}

Pitch de Ventas a aplicar:
{pitch or 'automatización de ventas B2B'}

Lista de Prospectos a calificar:
{prospects_text}

Analiza cada prospecto y califícalo según su propensión a compra o fit con el ICP.
Debes devolver un JSON con esta estructura exacta (mantén el campo 'id' tal cual se te entrega en la lista de prospectos):
```json
[
  {{
    "id": 1,
    "score": 85,
    "razon": "Razón específica de por qué encaja",
    "señal_principal": "señal más relevante detectada en el snippet",
    "decision_maker_sugerido": "Cargo típico del decisor (ej. CFO, Director de Pagos, E-commerce Manager)"
  }}
]
```"""
        raw = _llm_call(
            "Eres un calificador técnico de prospectos B2B. Responde únicamente con la lista JSON solicitada.",
            prompt
        )
        scored = _extract_json(raw)
        if not scored or not isinstance(scored, list):
            # Fallback: asignar score 50 a todos
            return [{**p, "score": 50, "razon": "Sin scoring disponible", "señal_principal": ""} for p in prospects]

        # Mapear las respuestas del LLM por el ID numérico
        scored_map = {}
        for item in scored:
            if isinstance(item, dict) and "id" in item:
                try:
                    scored_map[int(item["id"])] = item
                except ValueError:
                    pass

        merged = []
        for p in prospects_with_id:
            s = scored_map.get(p["temp_id"], {"score": 50, "razon": "Fallo al evaluar por ID", "señal_principal": ""})
            
            # Limpiar el temp_id para que no ensucie el output
            p_clean = {k: v for k, v in p.items() if k != "temp_id"}
            
            # Combinar datos
            merged.append({
                **p_clean,
                "score": s.get("score", 50),
                "razon": s.get("razon", ""),
                "señal_principal": s.get("señal_principal", ""),
                "decision_maker_sugerido": s.get("decision_maker_sugerido", "")
            })

        return sorted(merged, key=lambda x: x.get("score", 0), reverse=True)


class CompetitorInterceptAgent:
    """Extrae clientes de competidores y los prepara para scoring."""

    def run(self, competitor_url: str) -> List[Dict]:
        empresas = competitor_tool.extract_clients(competitor_url)
        prospects = []
        for emp in empresas:
            prospects.append({
                "empresa": emp,
                "snippet": f"Cliente conocido de {competitor_url}",
                "url": "",
                "fuente_query": f"competitor:{competitor_url}"
            })
        return prospects


def clean_and_filter_prospects(prospects: List[Dict], empresa_base: str = "", vendor: str = "") -> List[Dict]:
    """Filtra y limpia la lista de prospectos para evitar ruidos de directorios y competidores directos."""
    blacklist = {
        "wikipedia", "linkedin", "facebook", "crunchbase", "pitchbook", "glassdoor", 
        "youtube", "twitter", "instagram", "github", "softonic", "amazon", 
        "mercadolibre", "shopify", "medium", "reddit", "bloomberg"
    }
    
    # Agregar empresa base para no recomendársele a sí misma
    if empresa_base:
        blacklist.add(empresa_base.lower().strip())
        
    # Agregar el vendor a la exclusión
    if vendor:
        blacklist.add(vendor.lower().strip())
        
    # Si detectamos Toku como vendor o en el contexto, excluimos pasarelas y agregadores competidores
    if vendor and "toku" in vendor.lower() or not vendor:
        toku_competitors = [
            "toku", "clip", "openpay", "conekta", "stripe", "kushki", "mercado pago", "mercadopago", 
            "sr pago", "srpago", "dlocal", "adyen", "payu", "paypal", "netpay", "paynet", 
            "plug", "todito cash", "culqi", "bold", "pago facil", "pagofacil", "pagoefectivo", 
            "pago efectivo", "kueski", "aplazo", "addi", "sysde", "pago46"
        ]
        for c in toku_competitors:
            blacklist.add(c)
                
    filtered = []
    for p in prospects:
        name = p.get("empresa", "").strip()
        name_lower = name.lower()
        url_lower = p.get("url", "").lower()
        
        # 1. Filtro de longitud y formatos de blogs/directorios
        if len(name) < 2 or len(name) > 35:
            continue
        if any(kw in name_lower for kw in ["las 10", "los 10", "mejores", "ranking", "directorio", "guía", "cómo", "versus", " vs ", "comparativa"]):
            continue
            
        # 2. Filtro de blacklist (exacto o contención)
        is_blacklisted = False
        for b in blacklist:
            if b in name_lower or name_lower in b:
                is_blacklisted = True
                break
            if b in url_lower:
                is_blacklisted = True
                break
                
        if is_blacklisted:
            continue
            
        filtered.append(p)
    return filtered


# ── LookalikeCrew ─────────────────────────────────────────────────────────────

class LookalikeCrew:
    """
    Motor principal. Dos modos:
      - mode='direct'     → lookalikes de empresa base
      - mode='competitor' → intercepta clientes de competidor
    """

    def __init__(
        self,
        mode: str,
        empresa_base: Optional[str] = None,
        sector: Optional[str] = None,
        pitch: Optional[str] = None,
        competitor_url: Optional[str] = None,
        extra_context: Optional[str] = None,
        max_results: int = 15,
        vendor: Optional[str] = None
    ):
        if mode not in ("direct", "competitor"):
            raise ValueError("mode debe ser 'direct' o 'competitor'")
        self.mode = mode
        self.empresa_base = empresa_base or ""
        self.sector = sector or ""
        self.pitch = pitch or "automatización comercial B2B"
        self.competitor_url = competitor_url or ""
        self.extra_context = extra_context or ""
        self.max_results = max_results
        self.vendor = vendor or ""

    def run(self) -> List[Dict]:
        try:
            if self.mode == "direct":
                return self._run_direct()
            else:
                return self._run_competitor()
        except Exception as e:
            return [{"error": str(e), "empresa": "ERROR", "score": 0}]

    def _run_direct(self) -> List[Dict]:
        """Vector 1: Lookalike basado en perfil de empresa exitosa."""
        # Recuperar few-shot gold standard del DPO loop
        gold = db.get_recent_feedback(limit=2)

        # Paso 1 — Extraer ICP
        extractor = ICPExtractorAgent()
        icp = extractor.run(
            self.empresa_base,
            self.sector,
            f"{self.extra_context}\n{gold}"
        )

        # Paso 2 — Prospectar
        prospector = ProspectorAgent()
        raw_prospects = prospector.run(icp, self.max_results)

        # Filtrado de exclusiones dinámico para evitar colisiones y ruido
        prospects = clean_and_filter_prospects(raw_prospects, self.empresa_base, self.vendor)

        # Paso 3 — Puntuar
        scorer = ScorerAgent()
        scored = scorer.run(prospects, icp, self.pitch)

        # Paso 4 — Persistir
        self._save_results(scored, vector="direct", source=self.empresa_base)

        return scored

    def _run_competitor(self) -> List[Dict]:
        """Vector 2: Interceptar clientes de un competidor."""
        # Paso 1 — Extraer clientes del competidor
        interceptor = CompetitorInterceptAgent()
        raw_prospects = interceptor.run(self.competitor_url)

        if not raw_prospects:
            return [{"empresa": "Sin resultados", "score": 0,
                     "razon": "No se encontraron clientes en la URL proporcionada."}]

        # Filtrado de exclusiones dinámico
        prospects = clean_and_filter_prospects(raw_prospects, self.empresa_base, self.vendor)

        # Paso 2 — Construir ICP desde empresa base (si se dio) o genérico
        icp = {}
        if self.empresa_base:
            extractor = ICPExtractorAgent()
            icp = extractor.run(self.empresa_base, self.sector)
        else:
            icp = {"señales_clave": [], "sector": self.sector}

        # Paso 3 — Puntuar propensión a cambiar de proveedor
        scorer = ScorerAgent()
        scored = scorer.run(prospects, icp, self.pitch)

        # Paso 4 — Persistir
        self._save_results(scored, vector="competitor", source=self.competitor_url)

        return scored

    def _save_results(self, results: List[Dict], vector: str, source: str):
        """Persiste los prospectos en Supabase."""
        for r in results:
            if r.get("empresa") and r.get("empresa") != "ERROR":
                icp_store.save_prospect({
                    "empresa": r.get("empresa", ""),
                    "score": r.get("score", 0),
                    "vector": vector,
                    "source": source,
                    "sector": r.get("sector", self.sector),
                    "señales": {
                        "razon": r.get("razon", ""),
                        "señal_principal": r.get("señal_principal", ""),
                        "snippet": r.get("snippet", "")
                    },
                    "decision_maker": r.get("decision_maker_sugerido", ""),
                    "status": "nuevo"
                })

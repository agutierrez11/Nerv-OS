"""
lookalike_engine.py — NERV OS Lookalike Generation Engine
Dos vectores:
  1. direct   → empresas similares a un cliente exitoso (by profile)
  2. competitor → extrae clientes de competidores y los intercepta
"""
import os
import json
from typing import List, Dict, Any, Optional
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from tools.search import SerperSearch
from tools.firecrawl_tool import FirecrawlTool
from tools.competitor_intel import CompetitorIntelTool
from core.icp_store import icp_store
from core.database import db

# ── LLM (reutiliza el mismo modelo que crew_engine) ──────────────────────────
llm = ChatGroq(
    temperature=0.1,
    model_name="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY")
)

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

        prospects_text = "\n".join(
            f"- {p['empresa']}: {p.get('snippet', '')}" for p in prospects
        )
        icp_text = json.dumps(icp_profile, ensure_ascii=False)

        prompt = f"""Eres un Sales Ops expert. Puntúa cada prospecto del 0 al 100 según su fit con el ICP.

ICP:
{icp_text}

Pitch de ventas a aplicar: {pitch or 'automatización de ventas B2B'}

Prospectos:
{prospects_text}

Devuelve SOLO un JSON con este esquema:
```json
[
  {{
    "empresa": "Nombre Empresa",
    "score": 85,
    "razon": "Por qué encaja bien",
    "señal_principal": "señal más relevante detectada",
    "decision_maker_sugerido": "Cargo típico del decisor"
  }}
]
```"""
        raw = _llm_call(
            "Eres un sistema de scoring de prospectos B2B. Responde SOLO en JSON válido.",
            prompt
        )
        scored = _extract_json(raw)
        if not scored or not isinstance(scored, list):
            # Fallback: asignar score 50 a todos
            return [{**p, "score": 50, "razon": "Sin scoring disponible", "señal_principal": ""} for p in prospects]

        # Merge con datos originales (url, snippet)
        scored_map = {s["empresa"].lower(): s for s in scored}
        merged = []
        for p in prospects:
            key = p["empresa"].lower()
            s = scored_map.get(key, {"score": 50, "razon": "", "señal_principal": ""})
            merged.append({**p, **s})

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
        max_results: int = 15
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
        prospects = prospector.run(icp, self.max_results)

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
        prospects = interceptor.run(self.competitor_url)

        if not prospects:
            return [{"empresa": "Sin resultados", "score": 0,
                     "razon": "No se encontraron clientes en la URL proporcionada."}]

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

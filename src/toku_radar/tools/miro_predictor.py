import os
import json
import re
import datetime
from pathlib import Path
from toku_radar.tools.deepseek_client import DeepSeekClient
from toku_radar.tools.groq_rotator import GroqRotator

# ── Rutas persistentes ─────────────────────────────────────────────────────
_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
LOOKALIKE_DB = _ROOT / "lookalike_personas.json"
ROLEPLAY_LOG = _ROOT / "roleplay_dataset.jsonl"

# ── Helpers de Lookalike DB ────────────────────────────────────────────────
def _load_lookalike_db() -> list:
    if LOOKALIKE_DB.exists():
        try:
            return json.loads(LOOKALIKE_DB.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []

def _save_lookalike_db(data: list):
    LOOKALIKE_DB.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def _add_to_lookalike_db(personas: list, sector: str, product: str):
    db = _load_lookalike_db()
    for p in personas:
        entry = {**p, "sector": sector, "product_context": product, "ts": datetime.datetime.utcnow().isoformat()}
        db.append(entry)
    _save_lookalike_db(db)

def _get_lookalike_personas(sector: str, n: int = 3) -> list:
    """Retorna perfiles de la DB filtrados por sector, si existen."""
    db = _load_lookalike_db()
    matches = [p for p in db if p.get("sector", "").lower() == sector.lower()]
    if len(matches) >= n:
        # Devolver los más recientes
        matches.sort(key=lambda x: x.get("ts", ""), reverse=True)
        return matches[:n]
    return []

# ── Helper de Logging JSONL ────────────────────────────────────────────────
def _log_interaction(empresa: str, sector: str, mode: str, result: dict, rating: str = None):
    record = {
        "ts": datetime.datetime.utcnow().isoformat(),
        "empresa": empresa,
        "sector": sector,
        "mode": mode,
        "personas": result.get("personas", []),
        "phase_1": result.get("phase_1", ""),
        "phase_2": result.get("phase_2", ""),
        "battle_plan": result.get("battle_plan", ""),
        "rating": rating,
    }
    with open(ROLEPLAY_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


class ComiteSimulation:
    """
    Motor de Simulación de Comité de Compras integrado en NERV OS.
    Utiliza inteligencia multi-agente para simular la mesa de decisión del cliente.
    """
    def __init__(self, log_callback=None):
        self.log_callback = log_callback
        try:
            self.llm = DeepSeekClient(log_callback=log_callback)
            self.model = "deepseek-chat"
        except Exception:
            self.llm = GroqRotator(log_callback=log_callback)
            self.model = "llama-3.3-70b-versatile"

    def _log(self, msg: str):
        if self.log_callback:
            self.log_callback(msg)

    def _call_llm(self, prompt, system_prompt="Eres un analista de GTM corporativo.", temperature=0.4):
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
        resp = self.llm.create_completion(model=self.model, messages=messages, temperature=temperature)
        return resp.choices[0].message.content

    # ── REALITY CHECKER ────────────────────────────────────────────────────────
    def _reality_check(self, text: str, dossier: str) -> str:
        """
        Filtra el output del LLM para detectar estadísticas inventadas.
        Marca con [⚠️ DATO NO VERIFICADO] cualquier cifra que no esté en el dossier.
        """
        # Patrón: números con % o , seguidos de unidades clave
        stat_pattern = re.compile(
            r'(\d+[.,]?\d*\s*(?:%|por ciento|millones|miles|MXN|USD|horas|días|veces|x\d))'
        )
        def _check_match(m):
            stat = m.group(0)
            # Si la estadística aparece literalmente en el dossier, está bien
            if stat.replace(',', '').replace('.', '').strip() in dossier.replace(',', '').replace('.', ''):
                return stat
            return f"{stat} [⚠️ DATO NO VERIFICADO]"
        return stat_pattern.sub(_check_match, text)

    # ── GENERACIÓN DE PERSONAS ─────────────────────────────────────────────────
    def generate_personas(self, product: str, sector: str, dossier: str, company_url: str = None, icp_linkedin: str = None) -> list:
        """
        Genera los perfiles del comité.
        Prioridad: 1) ICP explícito → 2) Personas reales (scraping si hay URL) → 3) Lookalike DB → 4) LLM inferido.
        """
        self._log("👥 Identificando tomadores de decisiones reales...")

        icp_context = ""
        icp_email = ""
        if icp_linkedin:
            self._log(f"🔍 ICP Especificado: {icp_linkedin}. Buscando correo verificado en Prospeo...")
            try:
                from toku_radar.tools.prospeo_client import prospeo_enrich_person
                email_res = prospeo_enrich_person(icp_linkedin)
                if "@" in email_res:
                    icp_email = email_res
                    self._log(f"✅ Correo encontrado para ICP: {icp_email}")
                else:
                    self._log(f"⚠️ No se encontró correo público para el ICP: {email_res}")
                
                icp_context = f"\n\nATENCIÓN: El usuario ha especificado que ESTE PERFIL DE LINKEDIN {icp_linkedin} es su ICP principal. DEBES crear el 'Persona 1' basándote en que es esta persona. (Asume un rol afín al producto si no tienes su título exacto). Añade su campo 'linkedin_url': '{icp_linkedin}' y 'email': '{icp_email}' al JSON."
            except Exception as e:
                self._log(f"⚠️ Error al consultar Prospeo para el ICP: {e}")

        # ── Paso 1: Buscar personas reales si hay URL ──────────────────────────
        real_profiles_context = ""
        if company_url and not icp_linkedin:
            try:
                from toku_radar.tools.search import SerperSearch
                searcher = SerperSearch()
                query = f'site:linkedin.com/in/ "{company_url.replace("https://","").replace("http://","").split("/")[0]}" ("Director" OR "Head" OR "VP" OR "Gerente" OR "Manager") México'
                linkedin_hits = searcher._query(query)
                if linkedin_hits and "Error" not in linkedin_hits:
                    real_profiles_context = f"\n\nPERFILES REALES ENCONTRADOS EN LINKEDIN:\n{linkedin_hits}"
                    self._log("✅ Perfiles reales encontrados en LinkedIn. Usándolos como base...")
            except Exception as e:
                self._log(f"⚠️ No se pudieron obtener perfiles reales: {e}")

        # ── Paso 2: Lookalike fallback si no hay perfiles reales ───────────────
        lookalike_ctx = ""
        if not real_profiles_context and not icp_context:
            lookalikes = _get_lookalike_personas(sector)
            if lookalikes:
                self._log(f"📚 Usando {len(lookalikes)} perfiles Lookalike de la base de datos ({sector})...")
                lookalike_ctx = f"\n\nPERFILES LOOKALIKE DE REFERENCIA (mismo sector, no inventar C-levels genéricos):\n"
                for lk in lookalikes:
                    lookalike_ctx += f"- {lk['name']} ({lk['role']}): DISC={lk.get('disc','N/A')}, Preocupaciones: {lk.get('core_concerns',[])}\n"

        system_prompt = """
Eres el perfilador de comportamiento del Comité.
Tu misión: identificar los 3 roles que REALMENTE evalúan esta solución.

REGLAS CRÍTICAS:
1. NO uses C-levels genéricos (CEO, CFO, CTO) a menos que el dossier mencione explícitamente que ellos evalúan este tipo de solución.
2. Prefiere roles operativos/funcionales: Head of Product, VP de Operaciones, Gerente de Pagos, Líder de Ingeniería, Champion de Innovación.
3. Si el dossier o el contexto de LinkedIn mencionan nombres reales, ÚSALOS.
4. Si no hay nombres reales, inventa nombres latinos plausibles (no genéricos como García o López).
5. Aplica el framework DISC (D=Dominante/resultados, I=Influente/relaciones, S=Estable/procesos, C=Consciente/datos) en lugar de MBTI.
6. Las preocupaciones deben derivarse del dossier, no de estereotipos del rol.

FORMATO JSON REQUERIDO (lista de 3 objetos):
[
  {
    "role": "Puesto funcional real (Ej: Head de Operaciones de Pagos)",
    "name": "Nombre completo plausible",
    "disc": "D | I | S | C",
    "disc_description": "Descripción breve del estilo de comunicación y toma de decisiones",
    "stance": "Postura real basada en el dossier y su rol funcional",
    "core_concerns": ["Concern 1 derivado del dossier", "Concern 2"],
    "linkedin_url": "URL provista, o inferida de LinkedIn (ej: https://linkedin.com/in/nombre-apellido)",
    "email": "Email verificado obtenido mediante la herramienta (ej: j.perez@empresa.com), o escribe estrictamente 'No detectado' si no hay un correo verificado. Está estrictamente prohibido inventar o calcular correos ficticios."
  }
]
Devuelve SOLO el bloque JSON, sin markdown ni explicaciones.
"""

        prompt = f"""
PRODUCTO A VENDER: {product}
SECTOR: {sector}
DOSSIER DEL CLIENTE:
{dossier}
{icp_context}
{real_profiles_context}
{lookalike_ctx}

Genera los 3 perfiles del comité de compras real y devuelve el JSON.
"""

        raw_res = self._call_llm(prompt, system_prompt=system_prompt, temperature=0.3)
        json_str = re.sub(r'```json\s*|\s*```', '', raw_res).strip()

        try:
            personas = json.loads(json_str)
            # Guardar en Lookalike DB para uso futuro
            _add_to_lookalike_db(personas, sector, product)
            self._log(f"💾 {len(personas)} perfiles guardados en la base de datos Lookalike.")
            return personas
        except Exception as e:
            self._log(f"⚠️ Error parseando JSON de personas, usando fallback contextual. Detalles: {e}")
            return [
                {
                    "role": "Head de Operaciones de Pagos",
                    "name": "Carolina Mendoza",
                    "disc": "C",
                    "disc_description": "Orientada a datos y procesos. Necesita evidencia antes de comprometerse.",
                    "stance": "Quiere ver métricas de adopción y casos de uso reales del sector.",
                    "core_concerns": ["Tasa de error en transacciones", "Tiempo de integración"]
                },
                {
                    "role": "VP de Producto Digital",
                    "name": "Rodrigo Salinas",
                    "disc": "D",
                    "disc_description": "Orientado a resultados. Toma decisiones rápidas si ve el ROI claro.",
                    "stance": "Interesado en velocidad de implementación y diferenciación competitiva.",
                    "core_concerns": ["Time-to-market", "Experiencia del usuario final"]
                },
                {
                    "role": "Gerente de Riesgo y Cumplimiento",
                    "name": "Patricia Herrera",
                    "disc": "S",
                    "disc_description": "Conservadora. Prioriza estabilidad y cumplimiento regulatorio.",
                    "stance": "Preocupada por el impacto en auditorías y cumplimiento con regulaciones locales.",
                    "core_concerns": ["Regulación CNBV", "SLAs contractuales"]
                }
            ]

    def run_simulation(
        self,
        product: str,
        sector: str,
        dossier: str,
        objeciones: str,
        vendor_notes: str = None,
        company_url: str = None,
        empresa: str = "",
        icp_linkedin: str = None,
    ) -> dict:
        """
        Ejecuta la simulación del comité con separación Pre/Post reunión.
        - vendor_notes=None  → Fase 1: Pre-Reunión (alineación interna previa al pitch)
        - vendor_notes=str   → Fase 2: Post-Reunión (debriefing tras el pitch del vendedor)
        """
        personas = self.generate_personas(product, sector, dossier, company_url, icp_linkedin)
        personas_desc = "\n".join(
            [f"- **{p['name']} ({p['role']})** [DISC: {p.get('disc','?')} – {p.get('disc_description','')}]. Postura: {p['stance']}" for p in personas]
        )

        # Anti-Alucinación: regla común para todos los prompts
        _anti_hallucination_rule = """
REGLA CRÍTICA ANTI-ALUCINACIÓN:
Bajo ninguna circunstancia inventes métricas, porcentajes, estadísticas financieras o KPIs que NO estén explícitamente escritos en el dossier del cliente.
Si no hay datos concretos, habla en términos cualitativos (Ej: "hay demora en los pagos", NO "el 34% de los pagos se retrasan").
Si mencionas un número que no está en el dossier, DEBES anteponerle: [⚠️ estimado no verificado].
"""

        mode = "post" if vendor_notes else "pre"

        # ─── FASE 1: PRE-REUNIÓN (Alineación interna antes del pitch) ──────────
        if mode == "pre":
            self._log("📋 Modo PRE-REUNIÓN: El comité se alinea internamente antes de conocer al vendedor...")

            p1_system = f"""
Actúa como un comité de compras interno que acaba de recibir una invitación de reunión de un proveedor de '{product}'.
Aún NO han escuchado al vendedor. Esta es su reunión de alineación previa.

Los participantes son:
{personas_desc}

Contexto relevante de la empresa (dossier):
{dossier}

Objeciones o contexto previo del equipo de ventas:
{objeciones}
{_anti_hallucination_rule}

Simula la reunión de alineación interna. Cada persona habla desde su perspectiva funcional:
- ¿Qué dolor están sintiendo actualmente que podría resolver un proveedor como este?
- ¿Qué expectativas tienen para la reunión?
- ¿Cuáles son sus líneas rojas (lo que definitivamente no aceptarían)?
Escribe en Markdown con diálogos fluidos y realistas. Estilo: Zoom meeting interno.
"""
            phase_1 = self._call_llm("Ejecuta la reunión de Pre-Alineación del Comité.", system_prompt=p1_system, temperature=0.5)
            phase_1 = self._reality_check(phase_1, dossier)

            p2_system = f"""
Actúa como el mismo comité. Ya se realizó la reunión de alineación previa.
Ahora el equipo emite sus condiciones: ¿qué necesitarían ver en el pitch para considerar avanzar?
Define el veredicto preliminar y los criterios de evaluación.

PARTICIPANTES:
{personas_desc}
{_anti_hallucination_rule}

PRE-ALINEACIÓN:
{phase_1}

Escribe en Markdown.
"""
            phase_2 = self._call_llm("Define las condiciones de entrada y criterios de evaluación del proveedor.", system_prompt=p2_system, temperature=0.4)
            phase_2 = self._reality_check(phase_2, dossier)

        # ─── FASE 2: POST-REUNIÓN (Debriefing tras el pitch del vendedor) ───────
        else:
            self._log("🎙️ Modo POST-REUNIÓN: El comité debate internamente lo que acaban de escuchar...")

            p1_system = f"""
Actúa como el comité de compras que ACABA DE salir de una presentación de '{product}'.
El representante de ventas ya no está en la sala. Es el debriefing interno.

Los participantes son:
{personas_desc}

Notas del vendedor sobre lo que ocurrió en la reunión:
{vendor_notes}

Dossier del cliente:
{dossier}
{_anti_hallucination_rule}

Simula el debate post-reunión:
- ¿Qué les pareció convincente del pitch?
- ¿Qué les generó desconfianza o dejó sin responder?
- ¿Cómo se siente cada uno respecto a avanzar?
Diálogos fluidos y realistas. Sin formalidades robóticas.
"""
            phase_1 = self._call_llm("Ejecuta el debriefing post-reunión del Comité.", system_prompt=p1_system, temperature=0.5)
            phase_1 = self._reality_check(phase_1, dossier)

            p2_system = f"""
Actúa como el mismo comité. Luego del debate, emite el veredicto colectivo y las condiciones de negociación.

PARTICIPANTES:
{personas_desc}
{_anti_hallucination_rule}

DEBATE POST-REUNIÓN:
{phase_1}

Veredicto: Aprobado / Pendiente / Rechazado.
Condiciones específicas que le exigirán al proveedor antes de firmar.
Escribe en Markdown.
"""
            phase_2 = self._call_llm("Emite el veredicto y pliego de negociación del Comité.", system_prompt=p2_system, temperature=0.4)
            phase_2 = self._reality_check(phase_2, dossier)

        # ─── PLAN DE ATAQUE GTM ────────────────────────────────────────────────
        self._log("🧠 Estructurando el Plan de Ataque GTM personalizado por DISC...")
        battle_system = f"""
Eres el estratega GTM líder de NERV. Tu trabajo: convertir lo que acaba de ocurrir en la mesa del cliente en acciones concretas para el vendedor.
{_anti_hallucination_rule}

Estructura el plan en Markdown:
1. **Resumen de Bloqueos Críticos**
2. **Guía de Respuestas por Persona y Estilo DISC:**
   - Qué decirle a cada miembro del comité (usa su nombre real) basándote en su estilo DISC.
   - El tipo D quiere resultados rápidos. El tipo I quiere visión y relación. El tipo S quiere estabilidad y proceso. El tipo C quiere datos y detalles.
3. **Próximo Paso Inmediato:** Una acción específica y ejecutable (no genérica).
"""
        battle_prompt = f"""
MODO: {'Pre-Reunión' if mode == 'pre' else 'Post-Reunión'}

FASE 1:
{phase_1}

FASE 2:
{phase_2}

COMITÉ:
{personas_desc}
"""
        battle_plan = self._call_llm(battle_prompt, system_prompt=battle_system, temperature=0.3)
        battle_plan = self._reality_check(battle_plan, dossier)

        result = {
            "personas": personas,
            "mode": mode,
            "phase_1": phase_1,
            "phase_2": phase_2,
            "battle_plan": battle_plan,
            # Retrocompatibilidad con UI existente
            "round_1": phase_1,
            "round_2": phase_2,
            "round_3": "",
        }

        # ─── LOGGING LOCAL JSONL ────────────────────────────────────────────────
        try:
            _log_interaction(empresa=empresa, sector=sector, mode=mode, result=result)
        except Exception:
            pass

        return result


class MiroPredictor:
    """Retrocompatibilidad con código legacy que use MiroPredictor directamente."""
    def __init__(self, log_callback=None):
        self.swarm = ComiteSimulation(log_callback=log_callback)

    def predict_success(self, dossier_context):
        res = self.swarm.run_simulation(
            product="Solución de Pagos",
            sector="General",
            dossier=dossier_context,
            objeciones="Ninguna"
        )
        return f"### Resultado de Simulación\n\n{res['battle_plan']}"

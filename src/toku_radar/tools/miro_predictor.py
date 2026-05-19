import os
import json
import re
from toku_radar.tools.deepseek_client import DeepSeekClient
from toku_radar.tools.groq_rotator import GroqRotator

class MiroSwarmSimulation:
    """
    Motor de Simulación de Comité de Compras (MiroFish Swarm) integrado en NERV OS.
    Utiliza inteligencia multi-agente para simular la mesa de decisión del cliente.
    """
    def __init__(self, log_callback=None):
        self.log_callback = log_callback
        # Intentar inicializar DeepSeek por defecto para razonamiento de alta calidad,
        # y usar Groq como fallback en caso de error.
        try:
            self.llm = DeepSeekClient(log_callback=log_callback)
            self.model = "deepseek-chat"
        except Exception:
            self.llm = GroqRotator(log_callback=log_callback)
            self.model = "llama-3.3-70b-versatile"

    def _call_llm(self, prompt, system_prompt="Eres un analista de GTM corporativo.", temperature=0.4):
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
        resp = self.llm.create_completion(model=self.model, messages=messages, temperature=temperature)
        return resp.choices[0].message.content

    def generate_personas(self, product, sector, dossier):
        if self.log_callback:
            self.log_callback("👥 Creando perfiles dinámicos de los tomadores de decisiones...")
        
        system_prompt = """
        Eres el perfilador de comportamiento de MiroFish.
        Tu misión es analizar la propuesta de valor del vendedor y el dossier del cliente, y definir los 3 roles de compra (C-Level o Directivos) más estratégicos para esta venta.
        Debes devolver un JSON válido conteniendo una lista con los 3 perfiles.
        Asegúrate de que cada perfil tenga nombres realistas (si aparecen nombres en el dossier, utilízalos; si no, inventa nombres latinos realistas de directivos), rasgos psicológicos y un MBTI consistente.
        FORMATO JSON REQUERIDO:
        [
          {
            "role": "Puesto corporativo (Ej: Director de Finanzas (CFO))",
            "name": "Nombre completo",
            "mbti": "Tipo MBTI (Ej: ESTJ)",
            "stance": "Postura realista de compra y objeciones principales hacia el producto basándose en el dossier (Ej: Escéptico con el ROI debido a los costos de integración)",
            "core_concerns": ["Preocupación 1", "Preocupación 2"]
          }
        ]
        No incluyas explicaciones ni bloques Markdown que no sean de tipo json.
        """
        
        prompt = f"""
        PROPUESTA DE VALOR / PRODUCTO A VENDER: {product}
        SECTOR CLIENTE: {sector}
        DOSSIER COMPLETO DEL CLIENTE:
        {dossier}
        
        Extrae o define los 3 perfiles más lógicos y devuélvelos en formato JSON.
        """
        
        raw_res = self._call_llm(prompt, system_prompt=system_prompt, temperature=0.3)
        
        # Limpieza de Markdown
        json_str = re.sub(r'```json\s*|\s*```', '', raw_res).strip()
        try:
            return json.loads(json_str)
        except Exception as e:
            if self.log_callback:
                self.log_callback(f"⚠️ Error parseando JSON de personas, usando fallback. Detalles: {e}")
            # Fallback estático pero contextualizado
            return [
                {
                    "role": "Director de Finanzas (CFO)",
                    "name": "Alejandro García",
                    "mbti": "ESTJ",
                    "stance": "Escéptico con el ROI del producto y los costos de migración.",
                    "core_concerns": ["Retorno de Inversión", "Costes de implementación"]
                },
                {
                    "role": "Director de Tecnología (CTO)",
                    "name": "Sofía Martínez",
                    "mbti": "INTJ",
                    "stance": "Preocupada por la estabilidad de las APIs, la latencia y la seguridad de los datos.",
                    "core_concerns": ["Compatibilidad de APIs", "Seguridad"]
                },
                {
                    "role": "Director de Operaciones (COO)",
                    "name": "Eduardo Ramos",
                    "mbti": "ENFJ",
                    "stance": "Interesado en reducir la carga de trabajo manual y mejorar la conversión, pero teme fricción en el cambio.",
                    "core_concerns": ["Eficacia del equipo", "Fricción operativa"]
                }
            ]

    def run_simulation(self, product, sector, dossier, objeciones):
        personas = self.generate_personas(product, sector, dossier)
        personas_desc = "\n".join([f"- **{p['name']} ({p['role']})**: MBTI: {p['mbti']}. Postura: {p['stance']}" for p in personas])
        
        # --- RONDA 1: OBJECIONES ---
        if self.log_callback:
            self.log_callback("💬 Iniciando Ronda 1: Presentación de objeciones por parte de la mesa de decisión...")
            
        r1_system = f"""
        Actúa como un comité de compras corporativo.
        Los participantes son:
        {personas_desc}
        
        Tu tarea es simular la Ronda 1 del debate, donde cada uno de los 3 ejecutivos expone sus principales dudas y objeciones respecto a comprar el producto '{product}' basándose estrictamente en los puntos débiles de su empresa descritos en el dossier y en el contexto de objeciones previas.
        
        CONTRATACIÓN PREVIA / OBJECIONES REPORTADAS:
        {objeciones}
        
        DOSSIER CLIENTE:
        {dossier}
        
        Escribe la transcripción en Markdown de forma profesional y con diálogos fluidos. Evita formalidades robóticas. Que cada directivo exprese sus verdaderas preocupaciones de negocio.
        """
        
        r1_prompt = "Ejecuta la Ronda 1 de Objeciones del Comité."
        round_1 = self._call_llm(r1_prompt, system_prompt=r1_system, temperature=0.5)
        
        # --- RONDA 2: DEBATE CRUZADO ---
        if self.log_callback:
            self.log_callback("⚔️ Iniciando Ronda 2: Discusión cruzada y réplicas entre los directivos...")
            
        r2_system = f"""
        Actúa como el mismo comité de compras.
        Los participantes son:
        {personas_desc}
        
        Tu tarea es simular la Ronda 2 del debate. Los ejecutivos deben discutir cruzadamente los puntos presentados en la Ronda 1.
        Por ejemplo, el Director de Operaciones (u Operaciones) podría defender el aumento de conversión frente al escepticismo de costos del CFO, mientras que el CTO debate sobre los tiempos de desarrollo requeridos.
        El debate debe ser realista y sustentado en los datos técnicos y financieros del dossier.
        
        TRANSCRIPCIÓN DE LA RONDA 1:
        {round_1}
        
        Escribe la transcripción de la Ronda 2 en Markdown.
        """
        
        r2_prompt = "Ejecuta la Ronda 2 de Debate Cruzado del Comité."
        round_2 = self._call_llm(r2_prompt, system_prompt=r2_system, temperature=0.5)

        # --- RONDA 3: VEREDICTO Y CONDICIONES ---
        if self.log_callback:
            self.log_callback("⚖️ Iniciando Ronda 3: Votación final, veredicto y pliego de negociación...")
            
        r3_system = f"""
        Actúa como el mismo comité de compras.
        Los participantes son:
        {personas_desc}
        
        Tu tarea es simular la Ronda 3 del debate. Los ejecutivos deben emitir un veredicto colectivo (Aprobado / Pendiente de negociación / Rechazado) y detallar las condiciones específicas de negocio o técnicas que le exigirán a la empresa del vendedor (ej: garantías de SLA, piloto de 3 meses sin costo, comisiones específicas).
        
        TRANSCRIPCIÓN DE LA RONDA 2:
        {round_2}
        
        Escribe la transcripción de la Ronda 3 en Markdown.
        """
        
        r3_prompt = "Ejecuta la Ronda 3 de Veredicto del Comité."
        round_3 = self._call_llm(r3_prompt, system_prompt=r3_system, temperature=0.4)

        # --- REPORTE Y PLAN DE ATAQUE GTM ---
        if self.log_callback:
            self.log_callback("🧠 Analizando el debate y estructurando el Plan de Ataque GTM...")
            
        battle_system = """
        Eres el estratega GTM líder de NERV.
        Analiza el debate completo que ocurrió en la mesa del cliente y genera un Plan de Ataque GTM táctico para el vendedor de Toku.
        
        Estructura el plan en Markdown con:
        1. **Resumen de Bloqueos:** Cuáles son las barreras más críticas.
        2. **Guía de Respuestas por Rol:**
           - Qué decirle al CFO (Finanzas) para convencerlo.
           - Qué decirle al CTO (Tecnología) para calmar sus dudas.
           - Qué decirle al tercer tomador de decisiones para empujar la venta.
        3. **Próximo Paso Recomendado:** La acción inmediata para desbloquear el trato (ej: ofrecer piloto, demo técnica con su lead developer, etc.).
        """
        
        battle_prompt = f"""
        HISTORIAL DE DEBATE COMPLETO:
        --- RONDA 1 ---
        {round_1}
        --- RONDA 2 ---
        {round_2}
        --- RONDA 3 ---
        {round_3}
        """
        
        battle_plan = self._call_llm(battle_prompt, system_prompt=battle_system, temperature=0.3)
        
        return {
            "personas": personas,
            "round_1": round_1,
            "round_2": round_2,
            "round_3": round_3,
            "battle_plan": battle_plan
        }

class MiroPredictor:
    """Simulación ejecutable de MiroFish para predicción de enjambre. (Retrocompatibilidad)"""
    def __init__(self, log_callback=None):
        self.swarm = MiroSwarmSimulation(log_callback=log_callback)

    def predict_success(self, dossier_context):
        res = self.swarm.run_simulation(
            product="Solución de Pagos",
            sector="General",
            dossier=dossier_context,
            objeciones="Ninguna"
        )
        return f"### Swarm Simulation Result\n\n{res['battle_plan']}"

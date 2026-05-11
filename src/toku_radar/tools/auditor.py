import os
from toku_radar.tools.groq_rotator import GroqRotator

class GalileoAuditor:
    """Simulación ejecutable de la lógica de Galileo para auditar alucinaciones."""
    def __init__(self, log_callback=None):
        self.rotator = GroqRotator(log_callback=log_callback)

    def audit_fact(self, fact, context):
        prompt = f"""
        ACTÚA COMO EL AUDITOR JEFE DE GALILEO AI (Nivel Metacognitivo). 
        Tu misión es destruir el "humo" y las falsas promesas. 
        
        DATO A VERIFICAR: {fact}
        CONTEXTO DE REFERENCIA (Hallazgos del Investigador): {context}
        
        REGLAS DE AUDITORÍA:
        1. ¿Tiene Evidencia?: Si el dato NO incluye un enlace (URL) de respaldo, el Hallucination Score sube automáticamente a 8+.
        2. Consistencia Lógica: ¿El Estratega está exagerando? Si el contexto dice "problemas leves" y el Estratega dice "colapso total", es una alucinación de tono (Score 7).
        3. Fuente Directa: ¿El link realmente existe en el contexto de referencia?
        
        RESPUESTA:
        - Hallucination Score (0-10): 
        - Veredicto Metacognitivo: Explica brevemente si hay evidencia real o si es "humo" estratégico.
        """
        
        resp = self.rotator.create_completion(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        return resp.choices[0].message.content

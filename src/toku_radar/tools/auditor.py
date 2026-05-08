import os
from toku_radar.tools.groq_rotator import GroqRotator

class GalileoAuditor:
    """Simulación ejecutable de la lógica de Galileo para auditar alucinaciones."""
    def __init__(self, log_callback=None):
        self.rotator = GroqRotator(log_callback=log_callback)

    def audit_fact(self, fact, context):
        prompt = f"""
        ACTÚA COMO UN AUDITOR DE GALILEO AI. 
        Tu misión es encontrar alucinaciones o datos sin sustento.
        
        DATO A VERIFICAR: {fact}
        CONTEXTO DE REFERENCIA: {context}
        
        Responde con un 'Hallucination Score' (0-10) y una breve justificación.
        Si el dato NO está en el contexto, el score debe ser mayor a 7.
        """
        
        resp = self.rotator.create_completion(
            model="llama3-8b-8192",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        return resp.choices[0].message.content

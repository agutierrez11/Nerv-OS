import os
from toku_radar.tools.groq_rotator import GroqRotator

class MiroPredictor:
    """Simulación ejecutable de MiroFish para predicción de enjambre."""
    def __init__(self, log_callback=None):
        self.rotator = GroqRotator(log_callback=log_callback)

    def predict_success(self, dossier_context):
        prompt = f"""
        ACTÚA COMO UN ENJAMBRE DE INTELIGENCIA (MiroFish Style).
        Analiza el siguiente dossier de GTM y predice la probabilidad de éxito de Toku.
        
        DOSSIER: {dossier_context}
        
        Devuelve:
        1. Success Probability (0-100%)
        2. Swarm Reason (Por qué el enjambre tomó esta decisión)
        """
        
        resp = self.rotator.create_completion(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        return resp.choices[0].message.content

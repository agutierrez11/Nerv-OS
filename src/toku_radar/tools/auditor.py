import os
import yaml
from toku_radar.tools.groq_rotator import GroqRotator

class GalileoAuditor:
    """Motor de Auditoría Metacognitiva basada en la Constitución de NERV OS."""
    def __init__(self, log_callback=None):
        self.rotator = GroqRotator(log_callback=log_callback)
        self.base_path = os.path.dirname(__file__)
        self.constitution_path = os.path.join(os.path.dirname(self.base_path), 'config', 'constitution.yaml')
        
        try:
            with open(self.constitution_path, 'r', encoding='utf-8') as f:
                self.constitution = yaml.safe_load(f)
        except Exception:
            self.constitution = {"rules": []}

    def audit_fact(self, fact, context):
        rules_text = ""
        for r in self.constitution.get('rules', []):
            rules_text += f"- [{r['id']}] {r['name']}: {r['instruction']} (Severidad: {r['severity']})\n"

        prompt = f"""
        ACTÚA COMO EL AUDITOR JEFE DE GALILEO AI. 
        Tu misión es verificar si el Dossier cumple con la CONSTITUCIÓN DE NERV OS. 
        
        LEYES A VERIFICAR:
        {rules_text}
        
        DOSSIER A AUDITAR:
        {fact}
        
        CONTEXTO DE INVESTIGACIÓN:
        {context}
        
        RESPUESTA:
        1. Hallucination Score (0-10):
        2. Violaciones Constitucionales: (Lista las leyes violadas si las hay)
        3. Veredicto Final: (Aprobado / Rechazado / Ajuste Necesario)
        4. Notas del Auditor:
        """
        
        resp = self.rotator.create_completion(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        return resp.choices[0].message.content

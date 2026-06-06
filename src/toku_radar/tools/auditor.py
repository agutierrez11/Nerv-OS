import os
import yaml
from toku_radar.tools.deepseek_client import DeepSeekClient

class VeracityAuditor:
    """Motor de Auditoría Metacognitiva basada en la Constitución de NERV OS."""
    def __init__(self, log_callback=None):
        self.rotator = DeepSeekClient(log_callback=log_callback)
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
        ACTÚA COMO EL AUDITOR JEFE DEL PROTOCOLO DE VERACIDAD. 
        Tu misión es verificar si el Dossier cumple con la CONSTITUCIÓN DE NERV OS. 
        
        LEYES A VERIFICAR:
        {rules_text}
        
        DOSSIER A AUDITAR:
        {fact}
        
        CONTEXTO DE INVESTIGACIÓN:
        {context}
        
        RESPUESTA:
        1. Índice de Alucinación (0-10):
        2. Violaciones de Normas: (Lista las leyes violadas si las hay)
        3. Veredicto Final: (Aprobado / Rechazado / Ajuste Necesario)
        4. Notas del Auditor:
        
        IMPORTANTE: En tu respuesta, está estrictamente prohibido utilizar la palabra "Galileo" o "Galileo AI". Utiliza únicamente "Protocolo de Veracidad" o "Auditor de Veracidad" para referirte a este proceso de auditoría.
        """
        
        resp = self.rotator.create_completion(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        return resp.choices[0].message.content

# Alias de retrocompatibilidad
GalileoAuditor = VeracityAuditor

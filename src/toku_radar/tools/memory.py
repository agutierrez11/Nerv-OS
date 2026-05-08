import json
import os
from datetime import datetime

class TokuMemory:
    """Implementación de Memoria Persistente (Knowledge Base Style)."""
    def __init__(self, memory_path="C:/Users/Antonio/.gemini/antigravity/scratch/Toku_GTM_Radar/memory"):
        self.memory_path = memory_path
        self.feedback_path = os.path.join(self.memory_path, "feedback_loop")
        
        if not os.path.exists(self.memory_path):
            os.makedirs(self.memory_path)
        if not os.path.exists(self.feedback_path):
            os.makedirs(self.feedback_path)
            
        self.index_file = os.path.join(self.memory_path, "index.json")
        self.objections_file = os.path.join(self.feedback_path, "objections_library.json")
        self.corrections_file = os.path.join(self.feedback_path, "corrections.json")
        
        self._load_index()
        self._load_objections()

    def _load_index(self):
        if os.path.exists(self.index_file):
            with open(self.index_file, "r", encoding="utf-8") as f:
                self.index = json.load(f)
        else:
            self.index = {}

    def _load_objections(self):
        if os.path.exists(self.objections_file):
            with open(self.objections_file, "r", encoding="utf-8") as f:
                self.objections = json.load(f)
        else:
            self.objections = []

    def save_dossier(self, company, sector, summary):
        """Guarda un resumen del dossier para futuras consultas."""
        entry = {
            "company": company,
            "sector": sector,
            "summary": summary[:2000], # Resumen para búsqueda
            "timestamp": datetime.now().isoformat(),
            "file_path": f"output/{company.replace(' ', '_')}.md"
        }
        self.index[company.lower()] = entry
        with open(self.index_file, "w", encoding="utf-8") as f:
            json.dump(self.index, f, indent=2, ensure_ascii=False)
        print(f"  [MEMORIA] Dossier de {company} indexado.")

    def save_objection(self, company, sector, objection):
        """Guarda una objeción del usuario (RLHF a priori) en la librería."""
        if not objection:
            return
        entry = {
            "company": company,
            "sector": sector,
            "objection": objection,
            "timestamp": datetime.now().isoformat()
        }
        self.objections.append(entry)
        with open(self.objections_file, "w", encoding="utf-8") as f:
            json.dump(self.objections, f, indent=2, ensure_ascii=False)
        print(f"  [MEMORIA] Objeción de {company} guardada en feedback_loop.")

    def search_objections(self, sector):
        """Busca objeciones previas registradas para un sector."""
        similar = [o for o in self.objections if o.get('sector', '').lower() == sector.lower()]
        if not similar:
            return ""
        
        context = f"[MEMORIA RAG] HISTORIAL DE OBJECIONES EN EL SECTOR {sector.upper()}:\n"
        for o in similar[-5:]: # Traer las últimas 5 objeciones
            context += f"- Empresa: {o['company']} | Objeción: {o['objection']}\n"
        return context

    def search_similar_cases(self, sector):
        """Busca empresas del mismo sector para transferir inteligencia."""
        similar = [v for k, v in self.index.items() if v['sector'].lower() == sector.lower()]
        if not similar:
            return "No hay casos previos en este sector."
        
        context = "Casos previos detectados en este sector:\n"
        for s in similar[:3]:
            context += f"- {s['company']}: {s['summary'][:300]}...\n"
        return context

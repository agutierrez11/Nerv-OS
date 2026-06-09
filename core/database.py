import os
import httpx
import logging
from typing import Dict, Any, List
from dotenv import load_dotenv
from pathlib import Path

# Cargar logs
from core.logger import logger

# Cargar .env opcionalmente
if os.path.exists(".env"):
    load_dotenv()
elif os.path.exists("../.env"):
    load_dotenv("../.env")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_ANON_KEY")

class SupabaseManager:
    def __init__(self):
        self.url = SUPABASE_URL or ""
        self.key = SUPABASE_KEY or ""
        self.headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }

    def _execute_request(self, method: str, endpoint: str, data: Any = None):
        try:
            url = f"{self.url}/rest/v1/{endpoint}"
            with httpx.Client() as client:
                if method == "POST":
                    response = client.post(url, headers=self.headers, json=data)
                elif method == "GET":
                    response = client.get(url, headers=self.headers)
                elif method == "PATCH":
                    response = client.patch(url, headers=self.headers, json=data)
                
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.warning(f"Supabase inalcanzable ({endpoint}) - El sistema ignorará esto y continuará. ({e})")
            return None

    def upsert_empresa(self, company_data: Dict[str, Any]):
        """
        Inserta o actualiza una empresa en empresas_v3 basandose en el nombre.
        """
        nombre = company_data.get("nombre")
        if not nombre:
            logger.error("No se puede insertar empresa sin nombre.")
            return None

        # Verificar si existe
        existing = self._execute_request("GET", f"empresas_v3?nombre=eq.{nombre}")
        
        if existing:
            empresa_id = existing[0]["id"]
            logger.info(f"Actualizando empresa existente: {nombre} ({empresa_id})")
            return self._execute_request("PATCH", f"empresas_v3?id=eq.{empresa_id}", company_data)
        else:
            logger.info(f"Insertando nueva empresa: {nombre}")
            return self._execute_request("POST", "empresas_v3", company_data)

    def add_knowledge(self, content: str, metadata: Dict[str, Any] = None):
        """
        Guarda contenido denso en knowledge_base.
        """
        data = {
            "content": content,
            "metadata": metadata or {}
        }
        return self._execute_request("POST", "knowledge_base", data)

    def log_search(self, company_name: str, status: str, metadata: Dict[str, Any] = None):
        """
        Registra el intento de busqueda en logs_busquedas.
        """
        data = {
            "empresa": company_name,
            "status": status,
            "metadata": metadata or {}
        }
        # Nota: Asumimos que logs_busquedas tiene estas columnas. 
        # Si falla por esquema, se logueara el error.
        return self._execute_request("POST", "logs_busquedas", data)

    def save_feedback(self, feedback_data: Dict[str, Any]):
        """
        Guarda el feedback humano en brief_feedback.
        """
        return self._execute_request("POST", "brief_feedback", feedback_data)

    def get_recent_feedback(self, limit: int = 3) -> str:
        """
        Recupera los ultimos dossiers calificados como 'Elite' o 'Excelente'
        para usarlos como referencia (Few-shot learning).
        """
        # Intentamos traer los de mejor rating
        try:
            url = f"{self.url}/rest/v1/brief_feedback?rating=in.(Elite,Excelente)&order=created_at.desc&limit={limit}"
            with httpx.Client() as client:
                response = client.get(url, headers=self.headers)
                if response.status_code == 200:
                    data = response.json()
                    if not data: return ""
                    
                    context = "\n--- EJEMPLOS DE DOSSIERS APROBADOS POR EL USUARIO (GOLD STANDARD) ---\n"
                    for entry in data:
                        context += f"\nEMPRESA: {entry.get('empresa')}\nCONTENIDO:\n{entry.get('content_corrected')[:1000]}...\n"
                    return context
                return ""
        except Exception:
            return ""

# Instancia global
db = SupabaseManager()

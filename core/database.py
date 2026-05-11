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
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

class SupabaseManager:
    def __init__(self):
        self.url = SUPABASE_URL
        self.key = SUPABASE_KEY
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
            logger.error(f"Error en Supabase ({endpoint}): {e}")
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

# Instancia global
db = SupabaseManager()

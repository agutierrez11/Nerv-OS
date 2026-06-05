"""
icp_store.py — CRUD para la tabla icp_lookalikes en Supabase.
Wrapper ligero sobre SupabaseManager existente.
"""
import os
import httpx
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

if os.path.exists(".env"):
    load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = (
    os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    or os.getenv("SUPABASE_KEY")
    or os.getenv("SUPABASE_ANON_KEY")
    or ""
)

_HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

TABLE = "icp_lookalikes"


class ICPStore:
    """Maneja persistencia de prospectos lookalike en Supabase."""

    def _req(self, method: str, endpoint: str, data: Any = None, params: str = ""):
        try:
            url = f"{SUPABASE_URL}/rest/v1/{endpoint}{params}"
            with httpx.Client(timeout=10) as client:
                if method == "GET":
                    r = client.get(url, headers=_HEADERS)
                elif method == "POST":
                    r = client.post(url, headers=_HEADERS, json=data)
                elif method == "PATCH":
                    r = client.patch(url, headers=_HEADERS, json=data)
                elif method == "DELETE":
                    r = client.delete(url, headers=_HEADERS)
                else:
                    return None
                r.raise_for_status()
                return r.json()
        except Exception as e:
            # En desarrollo local silenciar el error y devolver None
            print(f"[icp_store] Supabase error ({endpoint}): {e}")
            return None

    # ── Escritura ─────────────────────────────────────────────────────────────

    def save_prospect(self, data: Dict[str, Any]) -> Optional[Dict]:
        """
        Inserta un prospecto. Si ya existe la empresa, actualiza score/status.
        """
        empresa = data.get("empresa", "")
        existing = self._req("GET", TABLE, params=f"?empresa=eq.{empresa}")

        if existing and len(existing) > 0:
            row_id = existing[0]["id"]
            return self._req("PATCH", TABLE, data=data, params=f"?id=eq.{row_id}")
        else:
            return self._req("POST", TABLE, data=data)

    def update_status(self, prospect_id: str, status: str) -> Optional[Dict]:
        """Actualiza el status de un prospecto (nuevo | contactado | descartado)."""
        return self._req("PATCH", TABLE, data={"status": status}, params=f"?id=eq.{prospect_id}")

    # ── Lectura ───────────────────────────────────────────────────────────────

    def get_prospects(
        self,
        vector: Optional[str] = None,
        status: Optional[str] = None,
        min_score: int = 0,
        limit: int = 50
    ) -> List[Dict]:
        """
        Recupera prospectos con filtros opcionales.
        vector: 'direct' | 'competitor'
        status: 'nuevo' | 'contactado' | 'descartado'
        """
        params = f"?score=gte.{min_score}&order=score.desc&limit={limit}"
        if vector:
            params += f"&vector=eq.{vector}"
        if status:
            params += f"&status=eq.{status}"

        result = self._req("GET", TABLE, params=params)
        return result if isinstance(result, list) else []

    def get_by_source(self, source: str) -> List[Dict]:
        """Trae todos los prospectos de una fuente (empresa base o URL competidor)."""
        result = self._req("GET", TABLE, params=f"?source=eq.{source}&order=score.desc")
        return result if isinstance(result, list) else []

    def get_stats(self) -> Dict[str, Any]:
        """Resumen rápido de la base de lookalikes."""
        total = self._req("GET", TABLE, params="?select=id")
        nuevos = self._req("GET", TABLE, params="?status=eq.nuevo&select=id")
        contactados = self._req("GET", TABLE, params="?status=eq.contactado&select=id")

        return {
            "total": len(total) if isinstance(total, list) else 0,
            "nuevos": len(nuevos) if isinstance(nuevos, list) else 0,
            "contactados": len(contactados) if isinstance(contactados, list) else 0,
        }

    # ── SQL Migration helper ──────────────────────────────────────────────────

    @staticmethod
    def migration_sql() -> str:
        """Devuelve el SQL para crear la tabla en Supabase."""
        return """
-- Run this in Supabase SQL Editor:
CREATE TABLE IF NOT EXISTS icp_lookalikes (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  empresa         TEXT NOT NULL,
  score           INT DEFAULT 0,
  vector          TEXT CHECK (vector IN ('direct', 'competitor')),
  source          TEXT,
  sector          TEXT,
  senales         JSONB DEFAULT '{}',
  decision_maker  TEXT,
  status          TEXT DEFAULT 'nuevo' CHECK (status IN ('nuevo', 'contactado', 'descartado')),
  created_at      TIMESTAMPTZ DEFAULT NOW(),
  updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Index para queries frecuentes
CREATE INDEX IF NOT EXISTS idx_icp_score   ON icp_lookalikes(score DESC);
CREATE INDEX IF NOT EXISTS idx_icp_status  ON icp_lookalikes(status);
CREATE INDEX IF NOT EXISTS idx_icp_vector  ON icp_lookalikes(vector);
CREATE INDEX IF NOT EXISTS idx_icp_source  ON icp_lookalikes(source);

-- Trigger para updated_at automático
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN NEW.updated_at = NOW(); RETURN NEW; END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER icp_lookalikes_updated_at
  BEFORE UPDATE ON icp_lookalikes
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();
"""


# Instancia global
icp_store = ICPStore()

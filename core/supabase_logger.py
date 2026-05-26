import os
import json
import logging
import streamlit as st
from supabase import create_client, Client

logger = logging.getLogger(__name__)

def _get_supabase_client():
    try:
        # Intenta obtener credenciales de st.secrets o de os.environ
        url = None
        key = None
        try:
            url = st.secrets.get("SUPABASE_URL")
            key = st.secrets.get("SUPABASE_ANON_KEY")
        except Exception:
            pass
        
        if not url:
            url = os.environ.get("SUPABASE_URL")
        if not key:
            key = os.environ.get("SUPABASE_ANON_KEY")
            
        if url and key:
            return create_client(url, key)
    except Exception as e:
        logger.error(f"Error inicializando Supabase: {e}")
    return None

def log_dpo_to_supabase(record: dict):
    """
    Inserta el registro DPO en la tabla 'dpo_feedback' de Supabase.
    Si falla (ej. si la tabla no existe), hace fallback al archivo local 'objections_vault.jsonl'.
    """
    supabase = _get_supabase_client()
    success = False
    if supabase:
        try:
            # Supabase Python SDK convierte dicts de python a JSONB automáticamente
            supabase.table('dpo_feedback').insert(record).execute()
            success = True
            logger.info("Registro DPO guardado exitosamente en Supabase.")
        except Exception as e:
            logger.error(f"Fallo al insertar en Supabase (asegúrate de que la tabla 'dpo_feedback' exista): {e}")
    
    # Fallback local persistente si falla la nube o estamos en pruebas
    if not success:
        try:
            with open("objections_vault.jsonl", "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        except Exception:
            pass
            
    return success

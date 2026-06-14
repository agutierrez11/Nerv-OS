import os
import time
import requests
import json
from langchain_core.tools import tool

@tool("Buscar Correo con FullEnrich")
def fullenrich_enrich_person(linkedin_url: str) -> str:
    """
    Herramienta avanzada alternativa para encontrar el correo electrónico y datos de contacto de una persona usando FullEnrich.
    Úsala como alternativa o complemento a Prospeo si Prospeo falla, da límite de cuota o no encuentra el contacto.
    Input: La URL de LinkedIn (ej. https://www.linkedin.com/in/usuario).
    Output: El correo electrónico de trabajo o personal de la persona, o un mensaje indicando que no se encontró.
    """
    api_key = os.environ.get("FULLENRICH_API_KEY", "ca49ba4c-a56b-426e-995e-f384cb484273")
    if not api_key:
        return "Error: FULLENRICH_API_KEY no está configurada en el entorno."

    # Iniciar enriquecimiento
    url_post = "https://app.fullenrich.com/api/v2/contact/enrich/bulk"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "name": "Nerv-OS Lead Enrichment",
        "data": [
            {
                "linkedin_url": linkedin_url,
                "enrich_fields": [
                    "contact.work_emails",
                    "contact.personal_emails"
                ]
            }
        ]
    }

    try:
        response = requests.post(url_post, json=payload, headers=headers, timeout=15)
        if response.status_code == 429:
            return "Error: Límite de peticiones de FullEnrich alcanzado (Rate Limit)."
        if response.status_code == 401:
            return "Error: FULLENRICH_API_KEY no es válida (No autorizado)."
        
        response.raise_for_status()
        res_data = response.json()
        enrichment_id = res_data.get("enrichment_id")
        
        if not enrichment_id:
            return "No encontrado"

        # Polling del resultado de FullEnrich
        max_attempts = 8
        sleep_sec = 2.0
        
        # Primero intentamos v2, luego v1 si v2 falla
        for version in ["v2", "v1"]:
            url_get = f"https://app.fullenrich.com/api/{version}/contact/enrich/bulk/{enrichment_id}"
            
            for attempt in range(max_attempts):
                get_resp = requests.get(url_get, headers=headers, timeout=15)
                
                if get_resp.status_code == 402:
                    # Créditos insuficientes, pero veamos si retornó algún dato residual en el cuerpo
                    try:
                        get_data = get_resp.json()
                        email = _extract_email_from_response(get_data, version)
                        if email:
                            return email
                    except Exception:
                        pass
                    return "Error: Créditos insuficientes en la cuenta de FullEnrich (Status 402)."
                
                if get_resp.status_code == 200:
                    try:
                        get_data = get_resp.json()
                        status = get_data.get("status", "").lower()
                        
                        # Extraer email si ya hay resultados parciales o totales
                        email = _extract_email_from_response(get_data, version)
                        if email:
                            return email
                            
                        if status in ["completed", "complete", "failed", "credits_insufficient"]:
                            break
                    except Exception:
                        pass
                
                time.sleep(sleep_sec)
                
        return "No encontrado"

    except Exception as e:
        return f"Error al consultar la API de FullEnrich: {str(e)}"

def _extract_email_from_response(get_data: dict, version: str) -> str:
    """Extrae el primer correo electrónico válido de la respuesta de FullEnrich según la versión."""
    if version == "v2":
        data_list = get_data.get("data", [])
        if data_list and isinstance(data_list, list):
            item = data_list[0]
            contact_info = item.get("contact_info", {})
            if contact_info:
                # Buscar most_probable_email
                mpe = contact_info.get("most_probable_email")
                if mpe and "@" in mpe:
                    return mpe
                # Buscar en la lista de emails
                emails = contact_info.get("emails", [])
                if emails and isinstance(emails, list):
                    for email_obj in emails:
                        email_val = email_obj.get("email") if isinstance(email_obj, dict) else email_obj
                        if email_val and "@" in email_val:
                            return email_val
                # Fallback a work_email
                work_email = contact_info.get("work_email")
                if work_email and "@" in work_email:
                    return work_email
                # Fallback a personal_email
                personal_email = contact_info.get("personal_email")
                if personal_email and "@" in personal_email:
                    return personal_email
    else:  # v1
        datas_list = get_data.get("datas", [])
        if datas_list and isinstance(datas_list, list):
            item = datas_list[0]
            contact = item.get("contact", {})
            if contact:
                mpe = contact.get("most_probable_email")
                if mpe and "@" in mpe:
                    return mpe
                emails = contact.get("emails", [])
                if emails and isinstance(emails, list):
                    for email_val in emails:
                        if email_val and "@" in email_val:
                            return email_val
                personal_emails = contact.get("personal_emails", [])
                if personal_emails and isinstance(personal_emails, list):
                    for email_val in personal_emails:
                        if email_val and "@" in email_val:
                            return email_val
    return ""

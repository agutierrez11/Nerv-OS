import os
import requests
import json
from langchain_core.tools import tool

@tool("Buscar Correo con Prospeo")
def prospeo_enrich_person(linkedin_url: str) -> str:
    """
    Herramienta CRÍTICA para encontrar el correo electrónico de trabajo de una persona.
    Úsala SIEMPRE que tengas la URL de LinkedIn de un prospecto o tomador de decisiones.
    Input: La URL de LinkedIn (ej. https://www.linkedin.com/in/usuario).
    Output: El correo electrónico verificado de la persona o un mensaje indicando que no se encontro.
    """
    api_key = os.environ.get("PROSPEO_API_KEY")
    if not api_key:
        return "Error: PROSPEO_API_KEY no está configurada en el entorno."

    url = "https://api.prospeo.io/enrich-person"
    
    headers = {
        "X-KEY": api_key,
        "Content-Type": "application/json"
    }
    
    payload = {
        "only_verified_email": True,
        "data": {
            "linkedin_url": linkedin_url
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        
        # Si llegamos al limite de velocidad (429)
        if response.status_code == 429:
            return "Error: Límite de peticiones de Prospeo alcanzado (Rate Limit)."
            
        if response.status_code == 400:
            try:
                err_data = response.json()
                if err_data.get("error_code") == "NO_MATCH":
                    return "No encontrado"
            except Exception:
                pass
            
        response.raise_for_status()
        data = response.json()
        
        if not data.get("error") and data.get("person") and data["person"].get("email"):
            email_info = data["person"]["email"]
            if email_info.get("status") == "VERIFIED":
                return email_info.get("email")
                
        return "No encontrado"
        
    except Exception as e:
        return f"Error al consultar la API de Prospeo: {str(e)}"

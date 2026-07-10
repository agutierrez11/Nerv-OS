import os
import requests
import json
from langchain_core.tools import tool

@tool("Buscar Correo con Prospeo")
def prospeo_enrich_person(linkedin_url: str = None, first_name: str = None, last_name: str = None, company_website: str = None) -> str:
    """
    Herramienta CRÍTICA para encontrar el correo electrónico de trabajo de una persona.
    Puedes buscar usando:
    1. Una URL de LinkedIn (ej. linkedin_url="https://www.linkedin.com/in/usuario").
    2. Nombre, apellido y sitio web de la empresa (ej. first_name="John", last_name="Doe", company_website="company.com").
    Output: El correo electrónico verificado de la persona o un mensaje indicando que no se encontró.
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
        "only_verified_email": True
    }
    
    if linkedin_url:
        payload["data"] = {
            "linkedin_url": linkedin_url
        }
    elif first_name and last_name and company_website:
        domain = company_website.replace('https://', '').replace('http://', '').replace('www.', '').split('/')[0]
        payload["data"] = {
            "first_name": first_name.strip(),
            "last_name": last_name.strip(),
            "company_website": domain.strip()
        }
    else:
        return "Error: Debes proporcionar un linkedin_url o (first_name, last_name, company_website) para usar Prospeo."
    
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

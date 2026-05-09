import os
import requests
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def send_crash_alert(app_name: str, error_details: str, context_info: str = ""):
    """
    Envía una alerta silenciosa al administrador vía Telegram cuando ocurre un fallo crítico.
    """
    # IMPORTANTE: Aquí va el Token del nuevo bot exclusivo para NERV
    token = os.getenv("NERV_TELEGRAM_TOKEN") 
    chat_id = os.getenv("NERV_ADMIN_CHAT_ID")

    if not token or not chat_id:
        print("⚠️ No hay credenciales de Telegram. Alerta cancelada.")
        return

    mensaje = (
        f"🚨 *ALERTA CRÍTICA: {app_name}*\n\n"
        f"⚠️ *Error:* `{error_details}`\n"
        f"🕵️ *Contexto:* {context_info}\n\n"
        f"⏱️ *Timestamp:* `Sistema de Monitoreo NERV`"
    )

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": mensaje,
        "parse_mode": "Markdown"
    }

    try:
        response = requests.post(url, json=payload, timeout=5)
        if response.status_code != 200:
            print(f"[ERROR] Fallo el envio de alerta: {response.text}")
    except Exception as e:
        print(f"[ERROR] Error interno enviando alerta: {e}")

import os
import requests
import logging

logger = logging.getLogger(__name__)

def send_telegram_alert(error_context: str, exception: Exception = None):
    """
    Envia una alerta de error critica a Telegram.
    """
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    
    if not token or not chat_id:
        logger.warning("TELEGRAM_BOT_TOKEN o TELEGRAM_CHAT_ID no configurados. No se envio alerta a Telegram.")
        return False
        
    error_msg = str(exception) if exception else "Error Desconocido"
    
    message = (
        f"🚨 *NERV OS ERROR CRÍTICO* 🚨\n\n"
        f"📍 *Contexto:* {error_context}\n"
        f"❌ *Error:* `{error_msg}`\n\n"
        f"⚠️ _Revisa los logs del servidor (Render) para mas detalles._"
    )
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        logger.info("Alerta de error enviada exitosamente a Telegram.")
        return True
    except Exception as e:
        logger.error(f"Fallo al enviar alerta de Telegram: {e}")
        return False

def send_telegram_notification(message: str):
    """
    Envia una notificacion de auditoria/exito a Telegram.
    """
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    
    if not token or not chat_id:
        return False
        
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }
    
    try:
        requests.post(url, json=payload, timeout=5)
        return True
    except:
        return False

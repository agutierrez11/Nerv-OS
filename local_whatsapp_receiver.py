import os
import sys
import threading
from pathlib import Path
from fastapi import FastAPI, Request, BackgroundTasks
import requests
import uvicorn
from dotenv import load_dotenv

# --- CONFIGURACION DE RUTAS LOCALES ---
ROOT_DIR = Path(__file__).parent.absolute()
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Cargar entorno local
load_dotenv()

from src.toku_radar.crew import TokuCrew
from core.logger import logger

app = FastAPI(title="NERV OS - Local WhatsApp Bridge")

# Configuración de OpenWA local
OPENWA_API_URL = os.getenv("OPENWA_API_URL", "http://localhost:2785")
OPENWA_SESSION = os.getenv("OPENWA_SESSION", "my-bot")
OPENWA_API_KEY = os.getenv("OPENWA_API_KEY", "")

def send_whatsapp_message(chat_id: str, text: str):
    """Envía un mensaje de texto de vuelta a WhatsApp usando la API de OpenWA."""
    url = f"{OPENWA_API_URL}/api/sessions/{OPENWA_SESSION}/messages/send-text"
    headers = {
        "Content-Type": "application/json"
    }
    if OPENWA_API_KEY:
        headers["X-API-Key"] = OPENWA_API_KEY

    payload = {
        "chatId": chat_id,
        "text": text
    }

    try:
        logger.info(f"Enviando respuesta a WhatsApp ({chat_id})...")
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        if response.status_code in [200, 201]:
            logger.info("¡Mensaje enviado con éxito!")
        else:
            logger.error(f"Error de OpenWA ({response.status_code}): {response.text}")
    except Exception as e:
        logger.error(f"Fallo al conectar con OpenWA: {e}")

def run_nerv_analysis(chat_id: str, empresa: str, sector: str, pitch: str, prior_knowledge: str):
    """Ejecuta el enjambre de agentes en segundo plano y envía el reporte final."""
    send_whatsapp_message(chat_id, f"🧠 *NERV OS:* Iniciando análisis forense de *{empresa}*...\nEsto puede tardar entre 1 y 2 minutos mientras el enjambre de agentes (Investigador, Psicólogo, Twin y Estratega) debate y Galileo audita las fuentes.")
    
    # Callback para reportar progreso en tiempo real
    def log_progress(msg):
        # Para no spamear demasiado WhatsApp, filtramos solo los inicios de Agente
        if "[ AGENT:" in msg:
            send_whatsapp_message(chat_id, f"⚙️ *Swarm:* {msg.strip()}")

    try:
        crew = TokuCrew(
            empresa=empresa,
            sector=sector,
            pitch=pitch,
            prior_knowledge=prior_knowledge,
            log_callback=log_progress
        )
        
        dossier = crew.kickoff()
        
        # Enviar el reporte final
        send_whatsapp_message(chat_id, f"✅ *¡ANÁLISIS COMPLETADO!*\n\nAquí tienes el Dossier Estratégico:")
        # WhatsApp no soporta Markdown complejo, pero negritas y listas sí, mandamos el texto
        send_whatsapp_message(chat_id, dossier)
        
    except Exception as e:
        logger.error(f"Error procesando análisis local de WA: {e}")
        send_whatsapp_message(chat_id, f"❌ *Error de NERV OS:* Ocurrió un error al procesar el análisis.\nDetalles: {str(e)}")

@app.post("/webhook")
async def whatsapp_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Recibe los webhooks enviados por OpenWA cuando llega un mensaje nuevo.
    """
    try:
        payload = await request.json()
        
        # Verificar que sea un evento de mensaje
        event_type = payload.get("event")
        if event_type != "message":
            return {"status": "ignored_event", "event": event_type}
            
        data = payload.get("data", {})
        message_type = data.get("type")
        
        # Ignorar si no es mensaje de texto
        if message_type != "chat":
            return {"status": "ignored_message_type"}
            
        body = data.get("body", "").strip()
        chat_id = data.get("from") # El ID de chat del remitente (ej: 521XXXXXXXXXX@c.us)
        
        # Ignorar si el mensaje viene del propio bot para evitar bucles infinitos
        is_from_me = data.get("fromMe", False)
        if is_from_me:
            return {"status": "ignored_self"}

        logger.info(f"Mensaje recibido de {chat_id}: '{body}'")

        # DISPARADOR: !radar Empresa, Sector, [Pitch/Propuesta]
        if body.lower().startswith("!radar"):
            parts = [p.strip() for p in body[6:].split(",")]
            
            if len(parts) < 2:
                send_whatsapp_message(
                    chat_id, 
                    "💡 *Instrucciones de NERV OS:*\n\nPara iniciar un radar, escribe:\n`!radar [Nombre Empresa], [Sector], [Propuesta/Pitch (Opcional)]`"
                )
                return {"status": "invalid_format"}
                
            empresa = parts[0]
            sector = parts[1]
            pitch = parts[2] if len(parts) > 2 else "Solución de Pagos + Recurrencia B2B"
            
            # Lanzar el enjambre de agentes en segundo plano
            background_tasks.add_task(
                run_nerv_analysis, 
                chat_id=chat_id, 
                empresa=empresa, 
                sector=sector, 
                pitch=pitch,
                prior_knowledge=""
            )
            
            return {"status": "queued"}
            
        # Si el usuario escribe hola o ayuda
        elif body.lower() in ["hola", "help", "ayuda", "start"]:
            welcome_msg = (
                "🧠 *¡Hola! Bienvenido al canal local de NERV OS Intelligence.*\n\n"
                "Soy el Swarm Intelligence Core de Toku. Puedo realizar un dossier estratégico forense de cualquier prospecto directamente desde aquí.\n\n"
                "👉 *¿Cómo usarme?*\n"
                "Escribe un comando con este formato:\n"
                "`!radar Walmart México, Retail` o\n"
                "`!radar Nike, Ecommerce, Orquestación de Pagos y Recurrencia`"
            )
            send_whatsapp_message(chat_id, welcome_msg)
            return {"status": "help_sent"}

    except Exception as e:
        logger.error(f"Error procesando webhook: {e}")
        return {"status": "error", "detail": str(e)}

if __name__ == "__main__":
    print("🚀 Iniciando Local WhatsApp Bridge para NERV OS...")
    print("Escuchando en http://localhost:8080")
    print("Configura en tu panel de OpenWA (http://localhost:2886) la URL del Webhook a: http://host.docker.internal:8080/webhook (o http://localhost:8080/webhook si no usas docker para el bridge)")
    uvicorn.run(app, host="0.0.0.0", port=8080)

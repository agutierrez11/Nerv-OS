import os
import sys
import time
import threading
from pathlib import Path
import requests
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

from src.toku_radar.crew import NervCrew
from core.logger import logger

# Obtener credenciales de Telegram
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram_message(chat_id: str, text: str):
    """Envía un mensaje de texto de vuelta a Telegram, dividiéndolo si supera el límite de caracteres."""
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN no configurada.")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    # El límite de Telegram es 4096 caracteres
    max_length = 4000
    chunks = [text[i:i+max_length] for i in range(0, len(text), max_length)]
    
    for chunk in chunks:
        payload = {
            "chat_id": chat_id,
            "text": chunk,
            "parse_mode": "Markdown"
        }
        
        try:
            logger.info(f"Enviando respuesta a Telegram ({chat_id})...")
            response = requests.post(url, json=payload, timeout=15)
            if response.status_code not in [200, 201]:
                logger.error(f"Error de Telegram ({response.status_code}): {response.text}")
                # Reintento de emergencia desactivando Markdown por si hay errores de sintaxis
                logger.info("Reintentando envío sin Markdown...")
                payload.pop("parse_mode", None)
                response_fallback = requests.post(url, json=payload, timeout=10)
                if response_fallback.status_code not in [200, 201]:
                    logger.error(f"Error de Telegram Fallback ({response_fallback.status_code}): {response_fallback.text}")
        except Exception as e:
            logger.error(f"Fallo al enviar mensaje a Telegram: {e}")

def run_nerv_analysis(chat_id: str, empresa: str, sector: str, pitch: str, vendedor: str, prior_knowledge: str):
    """Ejecuta el enjambre de agentes en segundo plano, guarda el dossier y notifica éxito/falla."""
    send_telegram_message(
        chat_id, 
        f"🧠 *NERV OS:* Iniciando análisis forense ({'Modo Toku 🟢' if vendedor.lower() == 'toku' else 'Modo Agnóstico 🔵'}) de *{empresa}*...\n"
        f"Esto puede tardar entre 1 y 2 minutos mientras el enjambre de agentes debate y audita las fuentes."
    )
    
    # Callback para reportar progreso en tiempo real
    def log_progress(msg):
        # Filtramos solo los inicios de Agente
        if "[ AGENT:" in msg:
            send_telegram_message(chat_id, f"⚙️ *Swarm:* {msg.strip()}")

    try:
        crew = NervCrew(
            empresa=empresa,
            sector=sector,
            pitch=pitch,
            vendedor=vendedor,
            prior_knowledge=prior_knowledge,
            log_callback=log_progress
        )
        
        dossier = crew.kickoff()
        
        # Limpiar pensamientos y guardar localmente en carpeta output
        import re
        dossier_limpio = re.sub(r'<thought>.*?</thought>', '', dossier, flags=re.DOTALL).strip()
        safe_name = re.sub(r'[^\w\-]', '_', empresa).strip('_')
        output_dir = ROOT_DIR / "output"
        output_dir.mkdir(exist_ok=True)
        file_path = output_dir / f"{safe_name}.md"
        file_path.write_text(dossier_limpio, encoding="utf-8")
        
        # Enviar reporte de éxito resumido
        modo_label = "Modo Toku 🟢" if vendedor.lower() == "toku" else "Modo Agnóstico 🔵"
        msg_exito = (
            f"✅ *¡ANÁLISIS COMPLETADO CON ÉXITO!*\n\n"
            f"🎯 *Empresa:* {empresa}\n"
            f"🏢 *Sector:* {sector}\n"
            f"👤 *Fase:* {modo_label}\n\n"
            f"📂 *Guardado:* El dossier estratégico se ha guardado en la base de datos de Supabase y localmente en:\n"
            f"`output/{safe_name}.md`"
        )
        send_telegram_message(chat_id, msg_exito)
        
    except Exception as e:
        logger.error(f"Error procesando análisis local de Telegram: {e}")
        send_telegram_message(chat_id, f"❌ *Error de NERV OS:* Ocurrió un error al procesar el análisis de *{empresa}*.\nDetalles: `{str(e)}`")
        try:
            from core.telegram_logger import send_telegram_alert
            send_telegram_alert(f"Telegram Bot Analysis ({empresa})", e)
        except Exception as alert_err:
            logger.error(f"Fallo al enviar alerta de Telegram: {alert_err}")

def process_message(chat_id: str, text: str):
    """Parsea el mensaje y decide la acción a tomar."""
    text_clean = text.strip()
    
    is_radar = False
    is_toku = False
    args_str = ""
    
    if text_clean.lower().startswith("/radar "):
        is_radar = True
        args_str = text_clean[7:]
    elif text_clean.lower().startswith("!radar "):
        is_radar = True
        args_str = text_clean[7:]
    elif text_clean.lower().startswith("/toku "):
        is_toku = True
        args_str = text_clean[6:]
    elif text_clean.lower().startswith("!toku "):
        is_toku = True
        args_str = text_clean[6:]
    elif text_clean.lower() == "/radar" or text_clean.lower() == "!radar":
        send_telegram_message(
            chat_id, 
            "💡 *Instrucciones de NERV OS (Modo Agnóstico):*\n\nPara iniciar un radar, escribe:\n`/radar [Nombre Empresa], [Sector], [Propuesta/Pitch (Opcional)]`"
        )
        return
    elif text_clean.lower() in ["/toku", "!toku"]:
        send_telegram_message(
            chat_id, 
            "💡 *Instrucciones de NERV OS (Modo Toku):*\n\nPara iniciar un radar de Toku, escribe:\n`/toku [Nombre Empresa], [Sector]`"
        )
        return

    if is_radar or is_toku:
        parts = [p.strip() for p in args_str.split(",")]
        
        if len(parts) < 2:
            if is_toku:
                send_telegram_message(
                    chat_id, 
                    "💡 *Instrucciones de NERV OS (Modo Toku):*\n\nPara iniciar un radar de Toku, escribe:\n`/toku [Nombre Empresa], [Sector]`"
                )
            else:
                send_telegram_message(
                    chat_id, 
                    "💡 *Instrucciones de NERV OS (Modo Agnóstico):*\n\nPara iniciar un radar, escribe:\n`/radar [Nombre Empresa], [Sector], [Propuesta/Pitch (Opcional)]`"
                )
            return
            
        empresa = parts[0]
        sector = parts[1]
        
        if is_toku:
            pitch = "Solución de Pagos + Recurrencia B2B"
            vendedor = "Toku"
        else:
            pitch = parts[2] if len(parts) > 2 else "Software SaaS B2B"
            vendedor = "Agnóstico"
        
        # Lanzar el enjambre de agentes en segundo plano
        thread = threading.Thread(
            target=run_nerv_analysis,
            kwargs={
                "chat_id": chat_id,
                "empresa": empresa,
                "sector": sector,
                "pitch": pitch,
                "vendedor": vendedor,
                "prior_knowledge": ""
            }
        )
        thread.daemon = True
        thread.start()
        
    elif text_clean.lower() in ["/start", "/help", "hola", "help", "ayuda", "start"]:
        welcome_msg = (
            "🧠 *¡Hola! Bienvenido al canal Telegram de NERV OS Intelligence.*\n\n"
            "Soy el Swarm Intelligence Core de NERV OS. Puedo realizar un dossier estratégico forense de cualquier prospecto en modo Toku o Agnóstico.\n\n"
            "👉 *¿Cómo usarme?*\n\n"
            "🟢 **Modo Toku (Propuesta Oficial):**\n"
            "`/toku [Nombre Empresa], [Sector]`\n"
            "Ej: `/toku Walmart México, Retail`\n\n"
            "🔵 **Modo Agnóstico (Cualquier Producto/Empresa):**\n"
            "`/radar [Nombre Empresa], [Sector], [Propuesta]`\n"
            "Ej: `/radar Nike, Ecommerce, Orquestación de Pagos y Recurrencia`"
        )
        send_telegram_message(chat_id, welcome_msg)

def start_polling():
    """Inicia el bucle de long-polling de Telegram."""
    if not TELEGRAM_BOT_TOKEN:
        print("[ERROR] TELEGRAM_BOT_TOKEN no configurada en el entorno.")
        return

    print("[START] Iniciando Local Telegram Receiver para NERV OS...")
    print(f"Token: {TELEGRAM_BOT_TOKEN[:10]}... Chat ID Configurado: {TELEGRAM_CHAT_ID}")
    print("Presiona Ctrl+C para detener.")

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
    offset = 0

    while True:
        try:
            # Petición con timeout largo para long polling
            response = requests.get(url, params={"offset": offset, "timeout": 30}, timeout=35)
            if response.status_code == 200:
                data = response.json()
                updates = data.get("result", [])
                for update in updates:
                    # Actualizar offset para no procesar el mismo mensaje de nuevo
                    offset = update["update_id"] + 1
                    
                    message = update.get("message", {})
                    chat = message.get("chat", {})
                    chat_id = str(chat.get("id"))
                    text = message.get("text")

                    if not text or not chat_id:
                        continue

                    # Opcional: Validar que el chat_id sea el administrador configurado
                    if TELEGRAM_CHAT_ID and chat_id != str(TELEGRAM_CHAT_ID):
                        logger.warning(f"Mensaje ignorado del chat no autorizado: {chat_id}")
                        send_telegram_message(chat_id, "⚠️ *Acceso Restringido:* Este bot de NERV OS está configurado de forma privada.")
                        continue

                    logger.info(f"Mensaje recibido en chat {chat_id}: '{text}'")
                    process_message(chat_id, text)
            else:
                logger.error(f"Error en getUpdates de Telegram ({response.status_code}): {response.text}")
                time.sleep(5)
        except KeyboardInterrupt:
            print("\nDeteniendo bot...")
            break
        except Exception as e:
            logger.error(f"Error de conexión en polling: {e}")
            time.sleep(5)

if __name__ == "__main__":
    start_polling()

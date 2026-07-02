import os
import sys
import time
import threading
import unicodedata
import re
from pathlib import Path
import requests
from dotenv import load_dotenv

def clean_filename(text):
    if not text:
        return ""
    nfkd_form = unicodedata.normalize('NFKD', text)
    only_ascii = nfkd_form.encode('ASCII', 'ignore').decode('utf-8')
    return re.sub(r'[^\w\-]', '_', only_ascii).strip('_')

def clean_brackets(text):
    if not text:
        return ""
    text = re.sub(r'\[\[([^\]\|]+)\|([^\]]+)\]\]', r'\2', text)
    text = re.sub(r'\[\[([^\]]+)\]\]', r'\1', text)
    return text.strip()

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
from src.toku_radar.tools.deepseek_client import DeepSeekClient

# Obtener credenciales de Telegram
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram_message(chat_id: str, text: str):
    """Envía un mensaje de texto de vuelta a Telegram, dividiéndolo si supera el límite de caracteres."""
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN no configurada.")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
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
                logger.info("Reintentando envío sin Markdown...")
                payload.pop("parse_mode", None)
                response_fallback = requests.post(url, json=payload, timeout=10)
                if response_fallback.status_code not in [200, 201]:
                    logger.error(f"Error de Telegram Fallback ({response_fallback.status_code}): {response_fallback.text}")
        except Exception as e:
            logger.error(f"Fallo al enviar mensaje a Telegram: {e}")

def run_nerv_analysis(chat_id: str, empresa: str, sector: str, pitch: str, vendedor: str, prior_knowledge: str, pais: str = "México"):
    """Ejecuta el enjambre de agentes en segundo plano, guarda el dossier y notifica éxito/falla."""
    send_telegram_message(
        chat_id, 
        f"🧠 *NERV OS:* Iniciando análisis forense ({'Modo Toku 🟢' if vendedor.lower() == 'toku' else 'Modo Agnóstico 🔵'}) de *{empresa}* en *{pais}*...\n"
        f"Esto puede tardar entre 1 y 2 minutos mientras el enjambre de agentes debate y audita las fuentes."
    )
    
    def log_progress(msg):
        if "[ AGENT:" in msg:
            send_telegram_message(chat_id, f"⚙️ *Swarm:* {msg.strip()}")

    try:
        crew = NervCrew(
            empresa=empresa,
            sector=sector,
            pitch=pitch,
            vendedor=vendedor,
            prior_knowledge=prior_knowledge,
            log_callback=log_progress,
            pais=pais
        )
        
        dossier = crew.kickoff()
        dossier_limpio = re.sub(r'<thought>.*?</thought>', '', dossier, flags=re.DOTALL).strip()
        safe_name = clean_filename(empresa)
        output_dir = ROOT_DIR / "output"
        output_dir.mkdir(exist_ok=True)
        file_path = output_dir / f"{safe_name}.md"
        file_path.write_text(dossier_limpio, encoding="utf-8")
        
        # Guardar automáticamente en la bóveda de Obsidian si existe
        if vendedor.lower() == "toku":
            vault_path = Path("/home/antonio/Desktop/Toku_WarRoom_Vault")
            dest_file = vault_path / f"{safe_name}.md"
        elif vendedor.lower() == "incode":
            vault_path = Path("/home/antonio/Desktop/Incode_WarRoom_Vault")
            dest_file = vault_path / "Empresas" / f"{safe_name}.md"
        else:
            vault_path = Path("/home/antonio/Desktop/Toku_WarRoom_Vault")
            dest_file = vault_path / f"{safe_name}.md"

        if vault_path.exists():
            try:
                from core.obsidian_linker import link_dossier
                dossier_linked = link_dossier(dossier_limpio, str(vault_path))
            except Exception as le:
                logger.error(f"Error running obsidian linker in telegram receiver: {le}")
                dossier_linked = dossier_limpio
            try:
                dest_file.parent.mkdir(parents=True, exist_ok=True)
                dest_file.write_text(dossier_linked, encoding="utf-8")
                logger.info(f"Dossier auto-guardado en Obsidian desde Telegram: {safe_name}")
            except Exception as ve:
                logger.error(f"Error guardando automático en bóveda Obsidian desde Telegram: {ve}")
        
        # Enviar reporte de éxito resumido
        if vendedor.lower() == "toku":
            modo_label = "Modo Toku 🟢"
        elif vendedor.lower() == "incode":
            modo_label = "Modo Incode 🔴"
        else:
            modo_label = "Modo Agnóstico 🔵"
        msg_exito = (
            f"✅ *¡ANÁLISIS COMPLETADO CON ÉXITO!*\n\n"
            f"🎯 *Empresa:* {empresa}\n"
            f"🏢 *Sector:* {sector}\n"
            f"🌍 *País:* {pais}\n"
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

# --- METODOS DE NERV AGENT BOT MERGED ---
def search_company_file(name):
    name_clean = clean_filename(name).lower()
    vaults = [
        Path("/home/antonio/Desktop/Boveda_Prueba/Judaísmo")
    ]
    for vault_path in vaults:
        if not vault_path.exists():
            continue
        for item in vault_path.rglob("*.md"):
            item_name_clean = clean_filename(item.stem).lower()
            if name_clean in item_name_clean or item_name_clean in name_clean:
                return item
    return None

def search_battlecard_file(name):
    name_clean = clean_filename(name).lower()
    competencia_dirs = [
        Path("/home/antonio/Desktop/Incode_WarRoom_Vault/Empresas")
    ]
    for competencia_dir in competencia_dirs:
        if competencia_dir.exists():
            for item in competencia_dir.glob("*.md"):
                item_name_clean = clean_filename(item.stem).lower()
                if name_clean in item_name_clean or item_name_clean in name_clean:
                    return item
    return None

def parse_markdown_profile(file_path):
    content = file_path.read_text(encoding="utf-8", errors="ignore")
    
    # Extract Title
    title_match = re.search(r'^#\s+(.*)', content, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else file_path.stem.replace('_', ' ')
    
    # Extract UVP (usually the quote line)
    uvp_match = re.search(r'^>\s*(.*)', content, re.MULTILINE)
    uvp = uvp_match.group(1).strip() if uvp_match else "Sin descripción"
    
    # Extract Metadata
    metadata = {}
    frontmatter_match = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
    if frontmatter_match:
        for line in frontmatter_match.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                metadata[k.strip().lower()] = v.strip().replace('"', '')
                
    # Extract Pains
    pains = []
    pains_section = re.search(r'###?\s*🤧?\s*Pains.*?\n(.*?)(?:\n###?|---|\Z)', content, re.DOTALL | re.IGNORECASE)
    if pains_section:
        pains = [p.strip() for p in re.findall(r'-\s*(.*)|\d+\.\s*(.*)', pains_section.group(1))]
        pains = [clean_brackets(p) for p in pains if p]
        
    # Extract Strategic Hook & Killer Argument
    hook = "No especificado"
    killer = "No especificado"
    gtm_section = re.search(r'###?\s*⚔️?\s*Estrategia GTM.*?\n(.*?)(?:\n###?|---|\Z)', content, re.DOTALL | re.IGNORECASE)
    if gtm_section:
        hook_match = re.search(r'-\s*Strategic Hook:\s*(.*)', gtm_section.group(1), re.IGNORECASE)
        killer_match = re.search(r'-\s*Argumento de Venta \(Killer Argument\):\s*(.*)', gtm_section.group(1), re.IGNORECASE)
        if hook_match: hook = clean_brackets(hook_match.group(1))
        if killer_match: killer = clean_brackets(killer_match.group(1))
        
    return {
        "title": title,
        "uvp": uvp,
        "country": metadata.get("country", "Desconocido").replace("[[", "").replace("]]", ""),
        "vertical": metadata.get("vertical", "Desconocido").replace("[[", "").replace("]]", ""),
        "tier": metadata.get("tier", "Tier 3"),
        "pains": pains[:3] if pains else [],
        "hook": hook,
        "killer": killer
    }

def handle_perfil(chat_id, query):
    if not query:
        send_telegram_message(chat_id, "⚠️ Por favor, ingresa el nombre de una empresa. Ej: `/perfil Under Armour` o `/perfil Mary Kay`")
        return
        
    file_path = search_company_file(query)
    if not file_path:
        send_telegram_message(chat_id, f"❌ No encontré ningún perfil guardado para '{query}' en tu bóveda de Obsidian.")
        return
        
    try:
        data = parse_markdown_profile(file_path)
        pains_str = "\n".join([f"• {p}" for p in data["pains"]]) if data["pains"] else "• No especificados"
        
        response = f"""📙 *Ficha GTM: {data["title"]}*
 
*Propuesta:* 
> {data["uvp"]}
 
*Detalles:*
• *País:* {data["country"]}
• *Vertical:* {data["vertical"]}
• *Prioridad:* {data["tier"]}
 
*Pains Críticos:*
{pains_str}
 
*⚔️ Estrategia GTM:*
• *Hook:* {data["hook"]}
• *Argumento Ganador:* {data["killer"]}
"""
        send_telegram_message(chat_id, response)
    except Exception as e:
        logger.error(f"Error procesando perfil en Telegram: {e}")
        send_telegram_message(chat_id, f"Error al procesar el perfil: {e}")

def handle_battlecard(chat_id, query):
    if not query:
        send_telegram_message(chat_id, "⚠️ Por favor, ingresa el nombre del competidor. Ej: `/battlecard Incode` o `/battlecard Jumio`")
        return
        
    file_path = search_battlecard_file(query)
    if not file_path:
        file_path = search_company_file(query)
        
    if not file_path:
        send_telegram_message(chat_id, f"❌ No se encontró ninguna Battlecard para '{query}' en tu carpeta de Competencia.")
        return
        
    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
        
        strengths = re.search(r'##\s*💪\s*Fortalezas.*?\n(.*?)(?:\n##|---|\Z)', content, re.DOTALL | re.IGNORECASE)
        weaknesses = re.search(r'##\s*⚠️\s*Debilidades.*?\n(.*?)(?:\n##|---|\Z)', content, re.DOTALL | re.IGNORECASE)
        how_to_win = re.search(r'##\s*⚔️\s*Cómo ganar.*?\n(.*?)(?:\n##|---|\Z)', content, re.DOTALL | re.IGNORECASE)
        
        res = f"🥊 *BATTLECARD: {file_path.stem.replace('_', ' ')}*\n\n"
        
        if strengths:
            res += "*💪 Fortalezas:*\n" + strengths.group(1).strip()[:400] + "\n\n"
        if weaknesses:
            res += "*⚠️ Debilidades (Tus argumentos de venta):*\n" + weaknesses.group(1).strip()[:500] + "\n\n"
        if how_to_win:
            res += "*⚔️ Cómo ganar en la llamada:*\n" + how_to_win.group(1).strip()[:600]
            
        send_telegram_message(chat_id, res)
    except Exception as e:
        logger.error(f"Error procesando battlecard: {e}")
        send_telegram_message(chat_id, f"Error al procesar la battlecard: {e}")

def handle_buscar(chat_id, query):
    if not query:
        send_telegram_message(chat_id, "⚠️ Ingresa tu consulta. Ej: `/buscar Nike` o `/buscar Under`")
        return
        
    vaults = [
        Path("/home/antonio/Desktop/Boveda_Prueba/Judaísmo")
    ]
    
    send_telegram_message(chat_id, f"🔍 Buscando '{query}' en las bóvedas de Incode y Ecosistema Global...")
    matches = []
    query_lower = query.lower().strip()
    
    for vault_path in vaults:
        if not vault_path.exists():
            continue
        for item in vault_path.rglob("*.md"):
            if query_lower in item.stem.lower():
                matches.append(f"• *{item.stem.replace('_', ' ')}* (Bóveda: {vault_path.name.replace('_WarRoom_Vault', '')})")
                if len(matches) >= 15:
                    break
        if len(matches) >= 15:
            break
                
    if matches:
        res = "✅ *Resultados encontrados en Obsidian:*\n" + "\n".join(matches)
        send_telegram_message(chat_id, res)
    else:
        send_telegram_message(chat_id, f"❌ No encontré coincidencias para '{query}' en ninguna bóveda.")

def run_general_chat(chat_id, query):
    """Busca contexto en las bóvedas de Obsidian y responde la consulta usando DeepSeek."""
    send_telegram_message(chat_id, "🔍 *NERV OS:* Analizando tu consulta y buscando en la base de conocimientos...")
    try:
        import unicodedata
        
        def clean_accents(text):
            if not text:
                return ""
            nfkd = unicodedata.normalize('NFKD', text)
            return "".join([c for c in nfkd if not unicodedata.combining(c)]).lower().strip()
            
        context_pieces = []
        vaults = [
            Path("/home/antonio/Desktop/Boveda_Prueba/Judaísmo")
        ]
        
        # Normalize and strip accents from search keywords
        query_words = [clean_accents(w) for w in re.split(r'\W+', query) if len(w.strip()) > 3]
        if not query_words:
            query_words = [clean_accents(query)]
            
        matched_files = set()
        for vault in vaults:
            if not vault.exists():
                continue
            for md_file in vault.rglob("*.md"):
                if md_file.name.startswith('.') or "Archivado" in str(md_file):
                    continue
                
                # Check match against normalized file stem
                file_stem_clean = clean_accents(md_file.stem)
                if any(word in file_stem_clean for word in query_words):
                    matched_files.add(md_file)
                    continue
                try:
                    content = md_file.read_text(encoding="utf-8", errors="ignore")
                    content_clean = clean_accents(content)
                    if any(word in content_clean for word in query_words):
                        matched_files.add(md_file)
                except Exception:
                    pass
                    
        list_matched = list(matched_files)[:5]
        
        if list_matched:
            context_pieces.append("Aquí tienes información relevante de tu base de conocimientos local:")
            for mf in list_matched:
                try:
                    content = mf.read_text(encoding="utf-8", errors="ignore")
                    content_clean = re.sub(r'^---\s*\n(.*?)\n---', '', content, flags=re.DOTALL)
                    content_clean = re.sub(r'<thought>.*?</thought>', '', content_clean, flags=re.DOTALL)
                    context_pieces.append(f"--- Fichero: {mf.name} ---\n{content_clean.strip()[:1500]}")
                except Exception:
                    pass
        else:
            context_pieces.append("No se encontró información directa en los archivos de la bóveda local.")
            
        context_str = "\n\n".join(context_pieces)
        
        client = DeepSeekClient()
        prompt = f"""Eres el Swarm Intelligence Core de NERV OS. Tu objetivo es responder la pregunta del usuario utilizando la información de contexto de la base de conocimientos proporcionada a continuación.
Si la información no es suficiente, responde con tu conocimiento general sobre el tema de la consulta.

CONTESTA DE FORMA CONCISA, ESTRUCTURADA Y CON TONO EJECUTIVO. Usa viñetas y negritas para mejorar la legibilidad.

CONTEXTO LOCAL DISPONIBLE:
{context_str}

PREGUNTA DEL USUARIO:
{query}
"""
        messages = [
            {"role": "system", "content": "Eres el Core de Inteligencia de NERV OS, un asistente experto que responde preguntas de forma concisa y estructurada basándose en tu base de conocimientos (que abarca fintech, prevención de fraude, así como judaísmo, teología, negocios y desarrollo personal)."},
            {"role": "user", "content": prompt}
        ]
        
        response = client.create_completion(model="deepseek-chat", messages=messages, temperature=0.5)
        reply = response.choices[0].message.content
        reply_clean = re.sub(r'<thought>.*?</thought>', '', reply, flags=re.DOTALL).strip()
        
        send_telegram_message(chat_id, reply_clean)
        
    except Exception as e:
        logger.error(f"Error en run_general_chat: {e}")
        send_telegram_message(chat_id, f"❌ *Error al procesar el chat general:* {e}")

def process_message(chat_id: str, text: str):
    """Parsea el mensaje y decide la acción a tomar."""
    text_clean = text.strip()
    
    is_radar = False
    is_toku = False
    is_incode = False
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
    elif text_clean.lower().startswith("/incode "):
        is_incode = True
        args_str = text_clean[8:]
    elif text_clean.lower().startswith("!incode "):
        is_incode = True
        args_str = text_clean[8:]
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
    elif text_clean.lower() in ["/incode", "!incode"]:
        send_telegram_message(
            chat_id, 
            "💡 *Instrucciones de NERV OS (Modo Incode):*\n\nPara iniciar un radar de Incode, escribe:\n`/incode [Nombre Empresa], [Sector], [País (Opcional)]`"
        )
        return
    elif text_clean.lower().startswith("/perfil"):
        query = text_clean.replace("/perfil", "", 1).strip()
        handle_perfil(chat_id, query)
        return
    elif text_clean.lower().startswith("/battlecard"):
        query = text_clean.replace("/battlecard", "", 1).strip()
        handle_battlecard(chat_id, query)
        return
    elif text_clean.lower().startswith("/buscar"):
        query = text_clean.replace("/buscar", "", 1).strip()
        handle_buscar(chat_id, query)
        return

    if is_radar or is_toku or is_incode:
        parts = [p.strip() for p in args_str.split(",")]
        
        if len(parts) < 2:
            if is_toku:
                send_telegram_message(
                    chat_id, 
                    "💡 *Instrucciones de NERV OS (Modo Toku):*\n\nPara iniciar un radar de Toku, escribe:\n`/toku [Nombre Empresa], [Sector], [País (Opcional)]`"
                )
            elif is_incode:
                send_telegram_message(
                    chat_id, 
                    "💡 *Instrucciones de NERV OS (Modo Incode):*\n\nPara iniciar un radar de Incode, escribe:\n`/incode [Nombre Empresa], [Sector], [País (Opcional)]`"
                )
            else:
                send_telegram_message(
                    chat_id, 
                    "💡 *Instrucciones de NERV OS (Modo Agnóstico):*\n\nPara iniciar un radar, escribe:\n`/radar [Nombre Empresa], [Sector], [Propuesta/Pitch (Opcional)], [País (Opcional)]`"
                )
            return
            
        empresa = parts[0]
        sector = parts[1]
        
        if is_toku:
            pitch = "Solución de Pagos + Recurrencia B2B"
            vendedor = "Toku"
            pais = parts[2] if len(parts) > 2 else "México"
        elif is_incode:
            pitch = "Identidad digital y Biometría facial anti-fraude"
            vendedor = "Incode"
            pais = parts[2] if len(parts) > 2 else "México"
        else:
            pitch = parts[2] if len(parts) > 2 else "Software SaaS B2B"
            vendedor = "Agnóstico"
            pais = parts[3] if len(parts) > 3 else "México"
        
        thread = threading.Thread(
            target=run_nerv_analysis,
            kwargs={
                "chat_id": chat_id,
                "empresa": empresa,
                "sector": sector,
                "pitch": pitch,
                "vendedor": vendedor,
                "prior_knowledge": "",
                "pais": pais
            }
        )
        thread.daemon = True
        thread.start()
        
    elif text_clean.lower() in ["/start", "/help", "hola", "help", "ayuda", "start"]:
        welcome_msg = (
            "🧠 *¡Hola! Bienvenido al canal Telegram de NERV OS Intelligence.*\n\n"
            "Soy el Swarm Intelligence Core de NERV OS. Puedo realizar un dossier estratégico forense de cualquier prospecto en modo Toku, Incode o Agnóstico.\n\n"
            "👉 *¿Cómo usarme?*\n\n"
            "🟢 **Modo Toku (Propuesta de Pagos):**\n"
            "`/toku [Nombre Empresa], [Sector], [País (Opcional)]`\n"
            "Ej: `/toku Walmart, Retail, México` o `/toku Walmart, Retail, Brasil`\n\n"
            "🔴 **Modo Incode (Propuesta de Biometría):**\n"
            "`/incode [Nombre Empresa], [Sector], [País (Opcional)]`\n"
            "Ej: `/incode Nu, Fintech, México` o `/incode Itaú, Finanzas, Brasil`\n\n"
            "🔵 **Modo Agnóstico (Cualquier Producto/Empresa):**\n"
            "`/radar [Nombre Empresa], [Sector], [Propuesta], [País (Opcional)]`\n"
            "Ej: `/radar Nike, Ecommerce, Orquestación de Pagos, México`\n\n"
            "🔍 **Consultas de Bóveda y Competencia (Incode + Ecosistema):**\n"
            "• `/perfil [Nombre]` -> Ver pains, hook y UVP de una fintech. Ej: `/perfil Under Armour`\n"
            "• `/battlecard [Competidor]` -> Ver fortalezas y debilidades. Ej: `/battlecard Sumsub`\n"
            "• `/buscar [Término]` -> Buscar notas en tu bóveda. Ej: `/buscar Incode`\n\n"
            "💬 **Chat General:**\n"
            "Escríbeme cualquier pregunta en lenguaje natural y buscaré respuestas en tu bóveda."
        )
        send_telegram_message(chat_id, welcome_msg)
    elif text_clean.startswith('/') or text_clean.startswith('!'):
        send_telegram_message(chat_id, "⚠️ *Comando no reconocido.* Escribe /help para ver la lista de comandos disponibles.")
    else:
        thread = threading.Thread(
            target=run_general_chat,
            args=(chat_id, text_clean)
        )
        thread.daemon = True
        thread.start()

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
            response = requests.get(url, params={"offset": offset, "timeout": 30}, timeout=35)
            if response.status_code == 200:
                data = response.json()
                updates = data.get("result", [])
                for update in updates:
                    offset = update["update_id"] + 1
                    message = update.get("message", {})
                    chat = message.get("chat", {})
                    chat_id = str(chat.get("id"))
                    text = message.get("text")

                    if not text or not chat_id:
                        continue

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

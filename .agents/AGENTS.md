# MEMORIA PERSISTENTE DE PROYECTOS Y CONFIGURACIÓN (NERV OS)

Este documento sirve como memoria del ecosistema de proyectos de Antonio. Debes leerlo siempre al iniciar cualquier sesión en este workspace para evitar duplicar recursos o sugerir arquitecturas redundantes.

---

## 🗺️ Ecosistema de Bots y Hosting Actual

### 1. Bot de NERV OS / Toku (`@nerv_stealth_bot`)
*   **Propósito:** Core de Inteligencia GTM, ventas B2B y análisis de prospectos.
*   **Código Principal:** [local_telegram_receiver.py](file:///C:/Users/Antonio/Nerv-OS/local_telegram_receiver.py) en este repositorio.
*   **Hosting:** VM temporal (`103.101.202.237`) bajo el servicio systemd `nerv-telegram.service`.
*   **Modos de Uso:**
    *   `/toku [Empresa]`: Dossier de ventas enfocado en cobros, recurrencia y pagos.
    *   `/incode [Empresa]`: Dossier enfocado en el ecosistema anti-fraude y validación de identidad en LATAM (Incode, Sumsub, Truora).
    *   `Mensaje normal`: Chat general con DeepSeek que busca en tiempo real en las bóvedas de Obsidian en la VM (`Toku_WarRoom_Vault`, `Incode_WarRoom_Vault`, `Sumsub_GTM_Strategy`). También detecta links web y los extrae con Firecrawl.

### 2. Bot de Torá y Estudios (`@AntonioEstudioTorah_Bot`)
*   **Propósito:** Q&A interactivo sobre Torá, Judaísmo y textos sagrados.
*   **Código Principal:** `bot.py` en el repositorio `telegram-study-bot` (`C:\Users\Antonio\antigravity-unified\Mis-Proyectos-Antigravitty\telegram-study-bot`).
*   **Hosting:** **Render** (`https://telegram-study-bot-66h6.onrender.com`) y se mantiene despierto 24/7 de forma gratuita usando **Uptime Robot**.
*   **Datos y Libros:** Los libros PDF/Markdown están subidos directamente en el repositorio en la carpeta `libros/`. **No requiere de la VM temporal.**
*   **Nota de Operación:** El servicio systemd en la VM (`torah-telegram.service`) fue apagado y deshabilitado para evitar conflictos de tokens. El bot corre exclusivamente en Render.

---

## ⚠️ Reglas Críticas de Arquitectura y Desarrollo

1.  **La VM es Temporal:** La máquina virtual en la IP `103.101.202.237` es estrictamente temporal. Ningún desarrollo de código debe hacerse directamente en la VM sin estar previamente guardado, commiteado y pusheado en los repositorios locales de la laptop (`C:\Users\Antonio\Nerv-OS`, etc.).
2.  **No Duplicar Bots en la misma API:** Nunca inicies dos procesos de bot (ej. uno en la VM y otro en Render) escuchando al mismo token de Telegram simultáneamente, ya que causará colisiones de red.
3.  **Seguridad de Secretos:** Nunca expongas tokens de Telegram, API Keys de DeepSeek o credenciales en archivos del repositorio público (como `.env.example`). Usa siempre placeholders.

---

## 🖥️ Tablero Visual de Control (Local)
*   **Código:** [dashboard_server.py](file:///C:/Users/Antonio/.gemini/antigravity-ide/brain/9d72bb75-2384-4b92-be66-8e9e9a5df52b/scratch/dashboard_server.py)
*   **Función:** Levanta una web local en `http://localhost:8000` que monitorea el estado de Git de tus proyectos locales, recursos de la VM, el bot de NERV (en la VM) y el bot de Torá (haciendo ping a Render).

# MEMORIA PERSISTENTE DE PROYECTO: NERV OS (TOKU / RADAR / ECO SISTEMA DE IDENTIDAD)

Este documento sirve como la guía de arquitectura y reglas del Core de NERV OS. Léelo siempre al iniciar este workspace.

---

## 🗺️ Arquitectura de NERV OS

### 1. Bot de Telegram
*   **Identidad:** `@nerv_stealth_bot` (nombre en interfaz: `NERV_bot`).
*   **Código Principal:** [local_telegram_receiver.py](file:///C:/Users/Antonio/Nerv-OS/local_telegram_receiver.py) en este repositorio.
*   **Hosting:** VM temporal (`103.101.202.237`) bajo el servicio systemd `nerv-telegram.service`.

### 2. Modos y Funciones de Entrada
*   **/toku [Empresa]**: Corre el enjambre de agentes (Crew) enfocado en dolores de cobro, pagos y facturación recurrente B2B para Toku.
*   **/incode [Empresa]**: Corre el enjambre de agentes enfocado en el ecosistema anti-fraude y de validación de identidad en LATAM (Incode, Sumsub, Truora, etc.).
*   **/radar [Empresa], [Sector], [Propuesta]**: Corre el análisis con una propuesta de valor libre.
*   **Mensaje normal (Lenguaje natural):** Chat directo con DeepSeek utilizando las bóvedas de Obsidian en la VM (`Toku_WarRoom_Vault`, `Incode_WarRoom_Vault`, `Sumsub_GTM_Strategy`) como contexto local. También detecta enlaces web y los extrae con Firecrawl automáticamente.

---

## ⚠️ Reglas Críticas del Proyecto
1.  **La VM es Temporal:** La máquina virtual es un entorno de ejecución temporal. Todo el código desarrollado debe nacer, modificarse y empujarse a GitHub desde esta laptop local (`C:\Users\Antonio\Nerv-OS`). No dejes cambios huérfanos en la VM.
2.  **Seguridad de Secretos:** Nunca expongas tokens de bots, API Keys de DeepSeek o de los agentes en archivos subidos a GitHub. El archivo de ejemplo es `.env.example`.
3.  **Bóvedas en la VM:** Las bóvedas de Obsidian que lee el bot residen en la VM en la ruta `/home/antonio/Desktop/`. Asegúrate de tener copias actualizadas en tu laptop.

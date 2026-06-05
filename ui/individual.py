import streamlit as st
import re
from pathlib import Path
from src.toku_radar.crew import NervCrew
from core.logger import logger
from core.database import db
from core.telegram_logger import send_telegram_notification

def render_individual_tab(companies_data, output_dir, user_active=None):
    st.subheader("// Configurar Analisis Forense")

    col1, col2 = st.columns(2)
    with col1:
        empresa_opciones = [r["empresa"] for r in companies_data] + ["[ Escribir manualmente ]"]
        empresa_sel = st.selectbox("Empresa objetivo", empresa_opciones)

        if empresa_sel == "[ Escribir manualmente ]":
            empresa = st.text_input("Nombre de la empresa", placeholder="ej: Walmart México")
            sector = st.text_input("Sector", placeholder="ej: Retail")
            pitch = st.text_area("Propuesta de Valor (Vendedor)", placeholder="ej: Orquestacion de Pagos")
        else:
            row = next(r for r in companies_data if r["empresa"] == empresa_sel)
            empresa = row["empresa"]
            sector = row["sector"]
            # Permitir editar la propuesta aunque venga del CSV
            pitch = st.text_area("Propuesta de Valor (Personalizable)", value=row["pitch_principal"])
            st.success(f"**Empresa:** {empresa} | **Sector:** {sector}")

    with col2:
        st.markdown("**Inteligencia de Venta / Objeciones:**")
        prior_knowledge = st.text_area(
            "Contexto Previo (RLHF)", 
            placeholder="Ej: 'A este CFO le preocupa la regulacion de la CNBV'...",
            help="Cualquier objecion conocida. El enjambre lo usara para calibrar el ataque."
        )

    # Verificar si ya existe un dossier guardado localmente para evitar regenerarlo
    safe_name = re.sub(r'[^\w\-]', '_', empresa).strip('_') if empresa else ""
    file_path = output_dir / f"{safe_name}.md" if safe_name else None
    
    if file_path and file_path.exists():
        st.info(f"📂 Se detectó un dossier guardado localmente para **{empresa}**.")
        if st.button("📂 Cargar Dossier Guardado", use_container_width=True):
            st.session_state[f"dossier_{empresa}"] = file_path.read_text(encoding="utf-8")
            st.rerun()

    if st.button("GENERAR NUEVO DOSSIER E INYECTAR EN SUPABASE", use_container_width=True):
        if not user_active:
            st.error("⚠️ Identificación requerida: Por favor, selecciona tu perfil o regístrate en el panel lateral antes de activar el análisis forense.")
            return
            
        if not empresa:
            st.error("Por favor selecciona o escribe una empresa.")
            return

        with st.status(f"🧠 Analizando {empresa}...", expanded=True) as status:
            try:
                log_placeholder = st.empty()
                st.session_state.full_log = ""
                def update_ui_log(msg):
                    st.session_state.full_log += msg + "\n\n"
                    log_placeholder.markdown(f"```text\n{st.session_state.full_log}\n```")

                vendedor_url = user_active.get("vendedor_url", "https://toku.com") if user_active else "https://toku.com"
                crew = NervCrew(
                    empresa=empresa, 
                    sector=sector, 
                    pitch=pitch, 
                    vendedor=vendedor_url, 
                    prior_knowledge=prior_knowledge, 
                    log_callback=update_ui_log
                )
                dossier = crew.kickoff()
                
                # Limpiar bloques <thought> generados por modelos de razonamiento (como DeepSeek R1)
                dossier_limpio = re.sub(r'<thought>.*?</thought>', '', dossier, flags=re.DOTALL).strip()
                
                st.session_state[f"dossier_{empresa}"] = dossier_limpio
                
                # Guardar automáticamente en el output_dir para consulta posterior
                safe_name = re.sub(r'[^\w\-]', '_', empresa).strip('_')
                (output_dir / f"{safe_name}.md").write_text(dossier_limpio, encoding="utf-8")
                
                status.update(label="✅ Analisis Completado y Guardado en Local", state="complete")
                
                vendedor_name = user_active.get("name", "Invitado") if user_active else "Invitado"
                is_toku_mode = user_active.get("is_toku", False) if user_active else False
                modo_str = "Modo Toku 🟢" if is_toku_mode else "Modo Agnóstico 🔵"
                send_telegram_notification(
                    f"📊 *NERV Dossier Audit* ({modo_str})\n"
                    f"Se ha generado un análisis individual.\n\n"
                    f"🎯 *Empresa:* {empresa}\n"
                    f"🏢 *Sector:* {sector}\n"
                    f"👤 *Vendedor:* {vendedor_name}"
                )
            except Exception as e:
                logger.error(f"Error en UI Individual: {e}")
                from core.telegram_logger import send_telegram_alert
                send_telegram_alert(f"Individual Analysis Kickoff ({empresa})", e)
                st.error(f"Error critico: {e}")
                return

    # Mostrar y Editar Resultado
    if f"dossier_{empresa}" in st.session_state:
        st.divider()
        st.subheader("📝 Dossier Generado")
        
        # Modo Edicion
        with st.expander("🛠️ Editar o Calificar Dossier", expanded=True):
            col_ed1, col_ed2 = st.columns([3, 1])
            with col_ed1:
                final_dossier = st.text_area("Modifica el contenido si es necesario:", 
                                            value=st.session_state[f"dossier_{empresa}"], 
                                            height=400)
            with col_ed2:
                st.markdown("⭐ **Califica la Calidad**")
                rating = st.select_slider("Feedback RLHF", options=["Pobre", "Regular", "Bueno", "Excelente", "Elite"], value="Bueno")
                if st.button("Guardar Feedback"):
                    feedback_payload = {
                        "empresa": empresa,
                        "rating": rating,
                        "content_corrected": final_dossier,
                        "vendedor": user_active.get("vendedor_name", "Toku") if user_active else "Toku",
                        "user_role": user_active.get("role", "Otro") if user_active else "Otro",
                        "user_industry": user_active.get("industry", "General") if user_active else "General"
                    }
                    res = db.save_feedback(feedback_payload)
                    if res:
                        st.toast(f"✅ Feedback '{rating}' guardado en Supabase. El sistema usará esto para mejorar futuros reportes.")
                    else:
                        st.error("Error al conectar con Supabase. Feedback guardado solo en memoria local.")
        
        st.markdown(final_dossier)
        
        # Guardar y Compartir
        safe_name = re.sub(r'[^\w\-]', '_', empresa).strip('_')
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            st.download_button(
                "📩 Descargar Dossier Final",
                final_dossier,
                file_name=f"NERV_{safe_name}.md",
                mime="text/markdown",
                use_container_width=True
            )
        with col_btn2:
            import urllib.parse
            # El dossier completo es muy grande para un enlace web, mandamos una alerta corta
            short_msg = f"🚨 *Inteligencia NERV: {empresa}* 🚨\nAcabo de generar el perfil forense y la estrategia de ataque. Revisa el documento adjunto."
            encoded_text = urllib.parse.quote(short_msg)
            wa_url = f"https://wa.me/?text={encoded_text}"
            st.link_button("🟢 Enviar Alerta por WhatsApp", wa_url, use_container_width=True)


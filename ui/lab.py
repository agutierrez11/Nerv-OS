import streamlit as st
import time
from src.toku_radar.crew import TokuCrew
from core.database import db

def render_lab_tab():
    st.markdown("""
        <div style='background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%); padding: 20px; border-radius: 10px; margin-bottom: 25px;'>
            <h2 style='color: white; margin: 0;'>🧪 NERV Experimentation Lab</h2>
            <p style='color: #d1d5db; margin: 5px 0 0 0;'>Cruza inteligencia de vendedor y cliente para crear el ataque perfecto.</p>
        </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🚀 Datos del Vendedor")
        url_vendedor = st.text_input("URL de tu Empresa (Vendedor)", placeholder="Ej: https://stripe.com")
        producto = st.text_input("¿Qué producto/servicio vendes?", placeholder="Ej: Infraestructura de pagos por internet")
    
    with col2:
        st.subheader("🎯 Datos del Prospecto")
        url_cliente = st.text_input("URL de la Empresa Cliente", placeholder="https://empresa-cliente.com")
        empresa_nombre = st.text_input("Nombre de la Empresa Cliente", placeholder="Ej: Claro, Bimbo, Rappi...")

    objeciones = st.text_area("🧠 Objeciones / Contexto Previo", 
                             placeholder="¿Qué te han dicho antes? ¿Qué barreras quieres romper?",
                             help="Esto entrena al sistema para ser más agresivo o persuasivo en puntos específicos.")

    with st.expander("🛠️ Configuración Avanzada de Estrategia (Opcional)", expanded=False):
        uvp_especifica = st.text_area("Propuesta de Valor Específica", placeholder="Ej: Ofrecemos comisiones del 2% vs el 4% de la competencia...")
        sector_nicho = st.text_input("Sector / Nicho del Cliente", placeholder="Ej: Hospitales Privados, Gimnasios de Lujo...")


    if st.button("🧬 Generar Inteligencia de Match", use_container_width=True):
        faltantes = []
        if not url_vendedor: faltantes.append("URL del Vendedor")
        if not producto: faltantes.append("Producto")
        if not url_cliente: faltantes.append("URL del Cliente")
        if not empresa_nombre: faltantes.append("Nombre de la Empresa Cliente")
        
        if faltantes:
            st.warning(f"⚠️ Por favor completa los campos: {', '.join(faltantes)}")
            return

        with st.status("📡 Iniciando Protocolos de Cruce...", expanded=True) as status:
            log_container = st.empty()
            def lab_logger(msg):
                log_container.markdown(f"`{msg}`")

            # Instanciamos el Crew con el modo especial de Lab
            crew = TokuCrew(
                empresa=empresa_nombre,
                sector=sector_nicho if sector_nicho else "General", 
                pitch=uvp_especifica if uvp_especifica else producto,
                vendedor=url_vendedor,
                url_cliente=url_cliente,
                prior_knowledge=objeciones,
                log_callback=lab_logger
            )
            
            try:
                import re
                st.write("🔍 Investigando ambas puntas del negocio...")
                resultado = crew.kickoff()
                
                # Limpiar bloques <thought> de modelos de razonamiento
                resultado_limpio = re.sub(r'<thought>.*?</thought>', '', resultado, flags=re.DOTALL).strip()
                
                st.session_state[f"lab_{empresa_nombre}"] = resultado_limpio
                status.update(label="✅ Inteligencia Generada con Éxito", state="complete")
                
                from core.telegram_logger import send_telegram_notification
                send_telegram_notification(f"🧪 *NERV Lab Audit*\nSe ha generado un dossier exitosamente.\n\n🎯 *Objetivo:* {empresa_nombre}\n💼 *Vendedor:* {url_vendedor}\n🛠️ *Producto:* {producto}")
            except Exception as e:
                from core.telegram_logger import send_telegram_alert
                send_telegram_alert(f"Experimentation Lab Kickoff ({empresa_nombre})", e)
                st.error(f"Error Crítico durante el cruce de inteligencia: {e}")
                status.update(label="❌ Error Crítico en el Enjambre", state="error")

    # Mostrar y Editar Resultado Lab
    if f"lab_{empresa_nombre}" in st.session_state:
        st.divider()
        st.subheader("📝 Inteligencia de Match")
        
        # Modo Edicion y Feedback
        with st.expander("🛠️ Editar o Calificar Inteligencia", expanded=True):
            col_ed1, col_ed2 = st.columns([3, 1])
            with col_ed1:
                final_output = st.text_area("Modifica el reporte final:", 
                                           value=st.session_state[f"lab_{empresa_nombre}"], 
                                           height=400)
            with col_ed2:
                st.markdown("⭐ **Calidad del Match**")
                rating = st.select_slider("Rating Lab", options=["Inútil", "Pobre", "Útil", "Genial", "🎯 Perfecto"], value="Útil")
                if st.button("Guardar Calificación"):
                    feedback_payload = {
                        "empresa": empresa_nombre,
                        "rating": rating,
                        "content_corrected": final_output,
                        "vendedor": url_vendedor
                    }
                    res = db.save_feedback(feedback_payload)
                    if res:
                        st.toast(f"✅ Calificación '{rating}' guardada. El enjambre aprenderá de este match.")
                    else:
                        st.error("Error al guardar en Supabase. Se guardó solo en local.")

        st.markdown(final_output)
        
        # Guardar y Compartir
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            st.download_button(
                "📩 Descargar Dossier Lab Final", 
                final_output, 
                file_name=f"NERV_Lab_{empresa_nombre}.md",
                use_container_width=True
            )
        with col_btn2:
            import urllib.parse
            # El texto es muy grande, mandamos una alerta
            short_msg = f"🧪 *Experimento NERV Lab: {empresa_nombre}* 🧪\nAcabo de generar el reporte de inteligencia. Revisa el documento adjunto."
            encoded_text = urllib.parse.quote(short_msg)
            wa_url = f"https://wa.me/?text={encoded_text}"
            st.link_button("🟢 Enviar Alerta por WhatsApp", wa_url, use_container_width=True)


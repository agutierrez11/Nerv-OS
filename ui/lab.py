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
        url_vendedor = st.text_input("URL de tu Empresa (Vendedor)", placeholder="https://tu-empresa.com")
        producto = st.text_input("¿Qué producto/servicio vendes?", placeholder="Ej: Pasarela de pagos, Software de Cobranza...")
    
    with col2:
        st.subheader("🎯 Datos del Prospecto")
        url_cliente = st.text_input("URL de la Empresa Cliente", placeholder="https://empresa-cliente.com")
        empresa_nombre = st.text_input("Nombre de la Empresa Cliente", placeholder="Ej: Claro, Bimbo, Rappi...")

    objeciones = st.text_area("🧠 Objeciones / Contexto Previo", 
                             placeholder="¿Qué te han dicho antes? ¿Qué barreras quieres romper?",
                             help="Esto entrena al sistema para ser más agresivo o persuasivo en puntos específicos.")

    if st.button("🧬 Generar Inteligencia de Match", use_container_width=True):
        if not (url_vendedor and url_cliente and producto):
            st.warning("⚠️ Por favor completa los campos básicos para iniciar el experimento.")
            return

        with st.status("📡 Iniciando Protocolos de Cruce...", expanded=True) as status:
            log_container = st.empty()
            def lab_logger(msg):
                log_container.markdown(f"`{msg}`")

            # Instanciamos el Crew con el modo especial de Lab
            crew = TokuCrew(
                empresa=empresa_nombre,
                sector="General", 
                pitch=producto, # Este es el producto del usuario
                vendedor=url_vendedor, # Esta es la empresa del usuario
                url_cliente=url_cliente,
                prior_knowledge=objeciones,
                log_callback=lab_logger
            )
            
            st.write("🔍 Investigando ambas puntas del negocio...")
            resultado = crew.kickoff()
            
            st.session_state[f"lab_{empresa_nombre}"] = resultado
            status.update(label="✅ Inteligencia Generada con Éxito", state="complete")

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
        
        # Botón para descargar reporte
        st.download_button(
            "📩 Descargar Dossier Lab Final", 
            final_output, 
            file_name=f"NERV_Lab_{empresa_nombre}.md",
            use_container_width=True
        )

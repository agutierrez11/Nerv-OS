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
            full_pitch = f"Vendedor: {url_vendedor} | Producto: {producto}"
            crew = TokuCrew(
                empresa=empresa_nombre,
                sector="General", 
                pitch=full_pitch,
                url_cliente=url_cliente, # PASAR LA URL
                prior_knowledge=objeciones,
                log_callback=lab_logger
            )
            
            st.write("🔍 Investigando ambas puntas del negocio...")
            resultado = crew.kickoff()
            
            status.update(label="✅ Inteligencia Generada con Éxito", state="complete")

        st.divider()
        st.markdown(resultado)
        
        # Botón para descargar reporte
        st.download_button("📩 Descargar Dossier Lab", resultado, file_name=f"NERV_Lab_{empresa_nombre}.md")

import streamlit as st
import re
from pathlib import Path
from src.toku_radar.crew import TokuCrew
from core.logger import logger

def render_individual_tab(companies_data, output_dir):
    st.subheader("// Configurar Analisis Forense")

    col1, col2 = st.columns(2)
    with col1:
        empresa_opciones = [r["empresa"] for r in companies_data] + ["[ Escribir manualmente ]"]
        empresa_sel = st.selectbox("Empresa objetivo", empresa_opciones)

        if empresa_sel == "[ Escribir manualmente ]":
            empresa = st.text_input("Nombre de la empresa", placeholder="ej: Walmart México")
            sector = st.text_input("Sector", placeholder="ej: Retail")
            pitch = st.text_input("Propuesta de Toku", placeholder="ej: Orquestacion de Pagos")
        else:
            row = next(r for r in companies_data if r["empresa"] == empresa_sel)
            empresa = row["empresa"]
            sector = row["sector"]
            pitch = row["pitch_principal"]
            st.success(f"**Empresa:** {empresa}")
            st.info(f"**Sector:** {sector}\n\n**Propuesta:** {pitch}")

    with col2:
        st.markdown("**Inteligencia de Venta:**")
        prior_knowledge = st.text_area(
            "Contexto Previo (RLHF)", 
            placeholder="Ej: 'A este CFO le preocupa la regulacion de la CNBV'...",
            help="Cualquier objecion conocida. El enjambre lo usara para calibrar el ataque."
        )
        
        st.divider()
        engine_type = st.radio("Cerebro del Radar", ["NERV 2.0 (Hibrido + Supabase)", "Motor Rapido (Legacy)"], index=0)

    generar = st.button("GENERAR DOSSIER E INYECTAR EN SUPABASE", use_container_width=True)

    if generar and empresa:
        with st.spinner(f"Analizando {empresa} con {engine_type}..."):
            try:
                # Log UI Setup
                log_container = st.expander("🕵️ Enjambre en Operacion (Live)", expanded=True)
                log_placeholder = st.empty()
                
                # Buffer para logs en vivo
                st.session_state.full_log = ""
                def update_ui_log(msg):
                    st.session_state.full_log += msg + "\n\n"
                    log_placeholder.markdown(f"```text\n{st.session_state.full_log}\n```")

                crew = TokuCrew(empresa, sector, pitch, prior_knowledge=prior_knowledge, log_callback=update_ui_log)
                dossier = crew.kickoff()

                st.success("Analisis completado y sincronizado con Supabase.")
                st.divider()
                st.markdown(dossier)
                
                # Guardar localmente
                safe_name = re.sub(r'[^\w\-]', '_', empresa).strip('_')
                filepath = output_dir / f"{safe_name}.md"
                filepath.write_text(dossier, encoding="utf-8")

                st.download_button(
                    "Descargar Dossier (.md)",
                    dossier,
                    file_name=f"NERV_{safe_name}.md",
                    mime="text/markdown",
                )
            except Exception as e:
                logger.error(f"Error en UI Individual: {e}")
                st.error(f"Error critico: {e}")

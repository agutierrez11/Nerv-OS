"""
app.py — Streamlit UI para Toku GTM Radar.
Modo individual: genera dossier para una empresa.
Modo batch: dispara el proceso completo de 41 empresas.
"""
import streamlit as st
import csv
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=r"C:\Users\Antonio\.gemini\antigravity\scratch\.env")

st.set_page_config(
    page_title="Toku GTM Radar",
    page_icon="🎯",
    layout="wide",
)

# Estilos
st.markdown("""
<style>
    .main { background-color: #0d0d0d; }
    .stApp { background-color: #0d0d0d; color: #e0e0e0; }
    h1 { color: #00ff88; font-family: monospace; }
    h2, h3 { color: #00ccff; }
    .stButton > button {
        background-color: #00ff88;
        color: #000;
        font-weight: bold;
        border-radius: 6px;
        width: 100%;
    }
    .stSelectbox label, .stTextInput label { color: #aaa; }
    .metric-card {
        background: #1a1a1a;
        border: 1px solid #333;
        border-radius: 8px;
        padding: 12px;
        margin: 4px 0;
    }
</style>
""", unsafe_allow_html=True)

st.title("🎯 TOKU GTM RADAR")
st.caption("GTM Intelligence OS · Fintech México · v1.0")
st.divider()

# Cargar lista de empresas
COMPANIES_CSV = Path(__file__).parent / "companies.csv"
OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

companies_data = []
if COMPANIES_CSV.exists():
    with open(COMPANIES_CSV, encoding="utf-8") as f:
        companies_data = list(csv.DictReader(f))

tab1, tab2 = st.tabs(["🔍 Análisis Individual", "📦 Batch 41 Empresas"])

# ─── TAB 1: INDIVIDUAL ────────────────────────────────────────────
with tab1:
    st.subheader("// Configurar Análisis")

    col1, col2 = st.columns(2)
    with col1:
        # Selector de empresa del CSV o entrada manual
        empresa_opciones = [r["empresa"] for r in companies_data] + ["[ Escribir manualmente ]"]
        empresa_sel = st.selectbox("Empresa objetivo", empresa_opciones)

        if empresa_sel == "[ Escribir manualmente ]":
            empresa = st.text_input("Nombre de la empresa", placeholder="ej: Walmart México")
            sector = st.text_input("Sector", placeholder="ej: Retail")
            pitch = st.text_input("Propuesta de Toku", placeholder="ej: Orquestación de Pagos")
        else:
            row = next(r for r in companies_data if r["empresa"] == empresa_sel)
            empresa = row["empresa"]
            sector = row["sector"]
            pitch = row["pitch_principal"]
            st.success(f"**Empresa:** {empresa}")
            st.info(f"**Sector detectado:** {sector}\n\n**Propuesta asignada:** {pitch}")

    with col2:
        st.markdown("**Toku vende:**")
        st.markdown("""
        - 🔄 Orquestación de Pagos  
        - 💳 Gateway + Cobranza Digital  
        - 📊 BNPL / Crédito Embebido  
        - 🔁 Recurrencia y Suscripciones  
        - 💸 Payouts Masivos  
        """)
        
        prior_knowledge = st.text_area(
            "🧠 Contexto Previo (RLHF a Priori)", 
            placeholder="Ej: 'A este CFO le preocupa la regulación de la CNBV' o 'El año pasado nos dijeron que su CRM era legacy.'",
            help="Cualquier objeción conocida o contexto que ya tengas. El enjambre lo usará para calibrar el ataque."
        )
        
        st.divider()
        engine_type = st.radio("Cerebro del Radar", ["⚡ Motor Rápido", "🤖 Enjambre CrewAI (Agentes Reales)"], index=0)

    generar = st.button("⚡ GENERAR DOSSIER FORENSE", use_container_width=True)

    if generar and empresa:
        with st.spinner(f"Analizando {empresa} con {engine_type}..."):
            try:
                if engine_type == "⚡ Motor Rápido":
                    from orchestrator import TokuDossierEngine
                    engine = TokuDossierEngine()
                    dossier = engine.generate_dossier(empresa, sector, pitch, contexto_crm=prior_knowledge)
                else:
                    import sys
                    from pathlib import Path
                    src_path = str(Path(__file__).parent / "src")
                    if src_path not in sys.path:
                        sys.path.append(src_path)
                        
                    try:
                        from toku_radar.crew import TokuCrew
                    except ImportError:
                        from src.toku_radar.crew import TokuCrew
                    
                    # Setup Log UI
                    log_container = st.expander("🕵️ Agentes Trabajando (Live Log)", expanded=True)
                    log_text = st.empty()
                    global full_log
                    full_log = ""
                    
                    def update_log(msg):
                        global full_log
                        full_log += msg + "\n\n"
                        log_text.markdown(f"```text\n{full_log}\n```")

                    crew = TokuCrew(empresa, sector, pitch, prior_knowledge=prior_knowledge, log_callback=update_log)
                    dossier = str(crew.run()) if hasattr(crew, 'run') else str(crew.kickoff())

                st.success("✅ Dossier generado")
                st.divider()
                st.markdown(dossier)
            except Exception as e:
                import traceback
                error_trace = traceback.format_exc()
                st.error("⚠️ La inteligencia artificial experimentó un error o tardó demasiado en responder (Timeout).")
                st.info("Por favor, inténtalo de nuevo en 1 minuto.")
                
                # Enviar alerta por Telegram
                try:
                    from src.toku_radar.tools.telegram_alerter import send_crash_alert
                    error_msg = str(e)[:100]
                    if "504" in str(e) or "502" in str(e):
                        error_msg = "HTTP Gateway Time-out (OpenResty / Ollama)"
                    send_crash_alert("NERV OS (Streamlit)", error_msg, f"Usuario intentó generar dossier para '{empresa}'")
                except Exception as alert_e:
                    print(f"Error al intentar enviar alerta: {alert_e}")
                
                st.stop()

        # Guardar y ofrecer descarga
        import re
        safe_name = re.sub(r'[^\w\-]', '_', empresa).strip('_')
        filepath = OUTPUT_DIR / f"{safe_name}.md"
        filepath.write_text(dossier, encoding="utf-8")

        st.download_button(
            "⬇️ Descargar Markdown",
            dossier,
            file_name=f"toku_dossier_{safe_name}.md",
            mime="text/markdown",
        )

# ─── TAB 2: BATCH ─────────────────────────────────────────────────
with tab2:
    st.subheader("// Batch: 41 Empresas Toku")

    col1, col2, col3 = st.columns(3)
    total = len(companies_data)
    existing = len(list(OUTPUT_DIR.glob("*.md")))

    with col1:
        st.metric("Total empresas", total)
    with col2:
        st.metric("Dossiers generados", existing)
    with col3:
        st.metric("Pendientes", total - existing)

    st.divider()

    # Tabla de empresas
    sector_filter = st.selectbox("Filtrar por sector", ["Todos"] + list(set(r["sector"] for r in companies_data)))

    filtered = companies_data if sector_filter == "Todos" else [r for r in companies_data if r["sector"] == sector_filter]

    for row in filtered:
        safe_name = __import__('re').sub(r'[^\w\-]', '_', row['empresa']).strip('_')
        exists = (OUTPUT_DIR / f"{safe_name}.md").exists()
        status = "✅" if exists else "⏳"

        col1, col2, col3 = st.columns([3, 4, 1])
        with col1:
            st.markdown(f"{status} **{row['empresa']}**")
        with col2:
            st.caption(row["pitch_principal"][:60])
        with col3:
            if exists:
                dossier_content = (OUTPUT_DIR / f"{safe_name}.md").read_text(encoding="utf-8")
                st.download_button("⬇️", dossier_content, file_name=f"{safe_name}.md", key=f"dl_{safe_name}")

    st.divider()

    if st.button("🚀 GENERAR TODOS LOS DOSSIERS PENDIENTES", use_container_width=True):
        progress = st.progress(0)
        status_text = st.empty()

        from orchestrator import TokuDossierEngine
        import time, re as _re

        engine = TokuDossierEngine()
        pending = [r for r in companies_data if not (OUTPUT_DIR / f"{_re.sub(r'[^\\w\\-]', '_', r['empresa']).strip('_')}.md").exists()]

        for i, row in enumerate(pending):
            status_text.text(f"Procesando: {row['empresa']} ({i+1}/{len(pending)})")
            try:
                dossier = engine.generate_dossier(row["empresa"], row["sector"], row["pitch_principal"], row.get("contexto", ""))
                safe = _re.sub(r'[^\w\-]', '_', row['empresa']).strip('_')
                (OUTPUT_DIR / f"{safe}.md").write_text(dossier, encoding="utf-8")
            except Exception as e:
                st.warning(f"Error en {row['empresa']}: {e}")
            progress.progress((i + 1) / len(pending))
            time.sleep(1.5)

        status_text.text("✅ Batch completo")
        st.success(f"Dossiers generados en: {OUTPUT_DIR}")
        st.rerun()

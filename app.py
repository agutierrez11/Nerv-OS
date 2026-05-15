import sys
from pathlib import Path

# --- CONFIGURACION DE RUTAS ---
ROOT_DIR = Path(__file__).parent.absolute()
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import streamlit as st
import csv
import os
from dotenv import load_dotenv

# --- CONFIGURACION DE RUTAS NERV 2.0 ---
ROOT_DIR = Path(__file__).parent.absolute()
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# --- CONFIGURACION NERV 2.0 ---
from ui.styles import apply_styles
from ui.individual import render_individual_tab
from ui.batch import render_batch_tab
from ui.lab import render_lab_tab
from core.logger import logger

# Cargar entorno opcionalmente
if os.path.exists(".env"):
    load_dotenv()

# Configuración de página
st.set_page_config(
    page_title="NERV OS Intelligence",
    page_icon="🧠",
    layout="wide",
)

# Aplicar estilos CSS personalizados (FORCE LIGHT MODE)
st.markdown("""
<style>
    .main { background-color: #f8fafc !important; }
    .stApp { background-color: #f8fafc !important; color: #1e293b !important; }
    h1 { color: #1e3a8a !important; }
    h2, h3, .stSubheader { color: #1e3a8a !important; border-bottom: 2px solid #e2e8f0 !important; }
    label, [data-testid="stWidgetLabel"] p { color: #000000 !important; font-weight: 800 !important; }
    .stTextInput input, .stTextArea textarea { background-color: #ffffff !important; color: #000000 !important; border: 2px solid #94a3b8 !important; }
    .stButton > button { background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%) !important; color: #ffffff !important; font-weight: 800 !important; }
    #MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# Titulo y Header
st.title("🧠 NERV OS Intelligence")
st.caption("Forensic GTM Engine · v2.0 Production-Ready")
st.divider()

# Rutas base
BASE_DIR = Path(__file__).parent
COMPANIES_CSV = BASE_DIR / "companies.csv"
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# Carga de datos
companies_data = []
if COMPANIES_CSV.exists():
    with open(COMPANIES_CSV, encoding="utf-8") as f:
        companies_data = list(csv.DictReader(f))
else:
    logger.error("No se encontro companies.csv")
    st.error("Archivo companies.csv no encontrado.")

# Tabs principales
tab_ind, tab_batch, tab_lab = st.tabs(["🎯 Analisis Individual", "📦 Procesamiento Batch", "🧪 NERV Lab"])

with tab_ind:
    render_individual_tab(companies_data, OUTPUT_DIR)

with tab_batch:
    render_batch_tab(companies_data, OUTPUT_DIR)

with tab_lab:
    render_lab_tab()

# Footer con observabilidad
st.sidebar.title("🛠️ Observabilidad")
st.sidebar.info(f"Dossiers en local: {len(list(OUTPUT_DIR.glob('*.md')))}")
if st.sidebar.button("Limpiar Cache Local"):
    if os.path.exists("nerv_cache.db"):
        os.remove("nerv_cache.db")
        st.sidebar.success("Cache eliminado.")

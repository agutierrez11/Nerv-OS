import streamlit as st

def apply_styles():
    st.markdown("""
    <style>
        /* FONDO CLARO Y LIMPIO - MODO LIGHT */
        .main { background-color: #f8fafc !important; }
        .stApp { background-color: #f8fafc !important; color: #1e293b !important; }
        
        /* TITULOS - AZUL PROFUNDO */
        h1 { color: #1e3a8a !important; font-family: 'Inter', sans-serif; font-weight: 800; }
        
        /* ENCABEZADOS DE SECCION */
        h2, h3, .stSubheader, [data-testid="stSubheader"] { 
            color: #1e3a8a !important; 
            font-weight: 800 !important; 
            font-size: 1.5rem !important;
            border-bottom: 2px solid #e2e8f0 !important;
            padding-bottom: 10px !important;
            margin-bottom: 20px !important;
        }
        
        /* LABELS - MÁXIMO CONTRASTE (NEGRO SOBRE BLANCO) */
        label, 
        .stWidgetLabel, 
        [data-testid="stWidgetLabel"] p, 
        [data-testid="stHeader"] p { 
            color: #000000 !important; 
            font-weight: 800 !important;
            font-size: 1.1rem !important;
            opacity: 1 !important;
        }
        
        /* INPUTS Y TEXTAREAS - FONDO BLANCO, BORDE OSCURO */
        .stTextInput input, .stTextArea textarea {
            background-color: #ffffff !important;
            color: #000000 !important;
            border: 2px solid #94a3b8 !important;
            font-size: 1rem !important;
            border-radius: 8px !important;
        }
        .stTextInput input:focus, .stTextArea textarea:focus {
            border-color: #2563eb !important;
            box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.2) !important;
        }
        
        /* RADIO BUTTONS */
        .stRadio label { 
            color: #000000 !important; 
            font-weight: 700 !important; 
        }
        
        /* CAJAS DE NOTIFICACIÓN */
        [data-testid="stNotification"] {
            background-color: #ffffff !important;
            border: 1px solid #e2e8f0 !important;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1) !important;
        }
        
        /* BOTÓN PRINCIPAL - TOKU BLUE GRADIENT */
        .stButton > button {
            background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%) !important;
            color: #ffffff !important;
            font-weight: 800 !important;
            font-size: 1.1rem !important;
            text-transform: uppercase;
            letter-spacing: 1px;
            border-radius: 10px !important;
            padding: 18px !important;
            border: none !important;
            box-shadow: 0 10px 15px -3px rgba(59, 130, 246, 0.4) !important;
            width: 100% !important;
        }
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 20px 25px -5px rgba(59, 130, 246, 0.5) !important;
        }

        /* SIDEBAR PROFESIONAL */
        [data-testid="stSidebar"] {
            background-color: #ffffff !important;
            border-right: 1px solid #e2e8f0;
        }

        /* METRIC CARDS */
        .metric-card {
            background: white !important;
            border: 1px solid #e2e8f0 !important;
            border-radius: 12px !important;
            padding: 20px !important;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1) !important;
            color: #1e293b !important;
        }

        /* EXPANDERS */
        .stExpander {
            background-color: #ffffff !important;
            border: 1px solid #e2e8f0 !important;
            border-radius: 8px !important;
        }

        /* OCULTAR ELEMENTOS DE STREAMLIT */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .stDeployButton {display:none;}
    </style>
    """, unsafe_allow_html=True)

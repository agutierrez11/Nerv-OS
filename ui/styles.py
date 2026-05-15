import streamlit as st

def apply_styles():
    st.markdown("""
    <style>
        /* FONDO CLARO Y LIMPIO */
        .main { background-color: #f8fafc; }
        .stApp { background-color: #f8fafc; color: #1e293b; }
        
        /* TITULOS - AZUL PROFUNDO */
        h1 { color: #1e3a8a !important; font-family: 'Inter', sans-serif; font-weight: 800; }
        
        /* ENCABEZADOS DE SECCION */
        h2, h3, .stSubheader, [data-testid="stSubheader"] { 
            color: #1e3a8a !important; 
            font-weight: 800 !important; 
            font-size: 1.5rem !important;
            border-bottom: 2px solid #e2e8f0;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }
        
        /* LABELS - MÁXIMO CONTRASTE EN OSCURO */
        label, 
        .stWidgetLabel, 
        [data-testid="stWidgetLabel"] p, 
        [data-testid="stHeader"] p { 
            color: #0f172a !important; 
            font-weight: 700 !important;
            font-size: 1rem !important;
            opacity: 1 !important;
        }
        
        /* INPUTS Y TEXTAREAS - FONDO BLANCO, BORDE GRIS */
        .stTextInput input, .stTextArea textarea {
            background-color: #ffffff !important;
            color: #1e293b !important;
            border: 2px solid #cbd5e1 !important;
            font-size: 1rem !important;
            border-radius: 8px !important;
        }
        .stTextInput input:focus, .stTextArea textarea:focus {
            border-color: #3b82f6 !important;
            box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1) !important;
        }
        
        /* RADIO BUTTONS */
        .stRadio label { 
            color: #334155 !important; 
            font-weight: 600 !important; 
        }
        
        /* CAJAS DE NOTIFICACIÓN */
        [data-testid="stNotification"] {
            background-color: #ffffff !important;
            border: 1px solid #e2e8f0 !important;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1) !important;
        }
        
        /* BOTÓN PRINCIPAL - TOKU BLUE */
        .stButton > button {
            background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%) !important;
            color: #ffffff !important;
            font-weight: 700 !important;
            font-size: 1.1rem !important;
            text-transform: uppercase;
            letter-spacing: 1px;
            border-radius: 10px !important;
            padding: 15px !important;
            border: none !important;
            box-shadow: 0 10px 15px -3px rgba(59, 130, 246, 0.3) !important;
        }
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 20px 25px -5px rgba(59, 130, 246, 0.4) !important;
        }

        /* SIDEBAR PROFESIONAL */
        [data-testid="stSidebar"] {
            background-color: #ffffff !important;
            border-right: 1px solid #e2e8f0;
        }

        /* METRIC CARDS */
        .metric-card {
            background: white;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }

        /* OCULTAR ELEMENTOS INNECESARIOS */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
    </style>
        .metric-card {
            background: #1a1a1a;
            border: 1px solid #333;
            border-radius: 12px;
            padding: 20px;
            text-align: center;
        }
        .stExpander {
            background-color: #111;
            border: 1px solid #222;
        }
        /* Ocultar elementos de Streamlit para una vista profesional */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .stDeployButton {display:none;}
    </style>
    """, unsafe_allow_html=True)

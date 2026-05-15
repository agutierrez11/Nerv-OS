import streamlit as st

def apply_styles():
    st.markdown("""
    <style>
        .main { background-color: #000000; }
        .stApp { background-color: #000000; color: #ffffff; }
        
        /* Titulos - Neon Green */
        h1 { color: #00ff88 !important; font-family: 'Inter', sans-serif; font-weight: 800; }
        
        /* Subtitulos y Encabezados de seccion - Blanco Puro */
        h2, h3, .stSubheader, [data-testid="stSubheader"] { 
            color: #ffffff !important; 
            font-weight: 800 !important; 
            font-size: 1.5rem !important;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        /* Labels (Nombres de los campos) - Blanco Brillante */
        label, [data-testid="stWidgetLabel"] p { 
            color: #ffffff !important; 
            font-weight: 800 !important;
            font-size: 1.1rem !important;
            opacity: 1 !important;
        }
        
        /* Textos de ayuda y placeholders */
        .stMarkdown p, .stText, [data-testid="stMarkdownContainer"] p { 
            color: #ffffff !important; 
            font-weight: 500 !important;
            font-size: 1rem !important;
        }
        
        /* Inputs y Textareas - Fondo negro, Borde cian, Texto blanco */
        .stTextInput input, .stTextArea textarea {
            background-color: #0a0a0a !important;
            color: #ffffff !important;
            border: 2px solid #00ccff !important;
            font-size: 1rem !important;
            font-weight: 500 !important;
        }
        
        /* Placeholders - Gris claro para que se lean pero se distingan */
        ::placeholder {
            color: #aaaaaa !important;
            opacity: 1;
        }

        /* Radio buttons */
        .stRadio label { 
            color: #ffffff !important; 
            font-weight: 600 !important; 
            font-size: 1rem !important;
        }
        
        /* Cajas de Alerta (Info/Success) */
        [data-testid="stNotification"] {
            background-color: #111 !important;
            border: 2px solid #333 !important;
        }
        [data-testid="stNotification"] p { 
            color: #ffffff !important; 
            font-weight: 700 !important;
            font-size: 1rem !important;
        }
        
        /* Boton Principal - Ultra Contraste */
        .stButton > button {
            background: linear-gradient(90deg, #00ff88 0%, #00ccff 100%);
            color: #000000 !important;
            font-weight: 900 !important;
            font-size: 1.2rem !important;
            text-transform: uppercase;
            letter-spacing: 2px;
            border-radius: 12px;
            padding: 20px;
            margin-top: 20px;
        }
        .stButton > button:hover {
            transform: scale(1.01);
            box-shadow: 0 0 20px rgba(0, 255, 136, 0.6);
        }
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

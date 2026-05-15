import streamlit as st

def apply_styles():
    st.markdown("""
    <style>
        .main { background-color: #050505; }
        .stApp { background-color: #050505; color: #ffffff; }
        
        /* Titulos y Subtitulos */
        h1 { color: #00ff88; font-family: 'Inter', sans-serif; font-weight: 800; }
        h2, h3, .stSubheader { color: #ffffff !important; font-weight: 700 !important; }
        
        /* Labels y Textos de ayuda */
        label, .stMarkdown p, .stText { 
            color: #ffffff !important; 
            font-weight: 600 !important;
            font-size: 0.9rem !important;
        }
        
        /* Radio buttons y Checkboxes */
        .stRadio label { color: #ffffff !important; font-weight: 500 !important; }
        
        /* Inputs y Textareas */
        .stTextInput input, .stTextArea textarea {
            background-color: #111 !important;
            color: #ffffff !important;
            border: 1px solid #333 !important;
        }
        
        /* Cajas de Info/Success con alto contraste */
        .stAlert {
            background-color: #111 !important;
            border: 1px solid #333 !important;
        }
        .stAlert p { color: #ffffff !important; font-weight: 600 !important; }
        
        /* Boton Principal */
        .stButton > button {
            background: linear-gradient(90deg, #00ff88 0%, #00ccff 100%);
            color: #000 !important;
            font-weight: 900 !important;
            text-transform: uppercase;
            letter-spacing: 1px;
            border-radius: 8px;
            border: none;
            padding: 15px;
            transition: all 0.3s ease;
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

import streamlit as st

def apply_styles():
    st.markdown("""
    <style>
        .main { background-color: #0d0d0d; }
        .stApp { background-color: #0d0d0d; color: #e0e0e0; }
        h1 { color: #00ff88; font-family: 'Courier New', Courier, monospace; letter-spacing: -1px; }
        h2, h3 { color: #00ccff; }
        .stButton > button {
            background: linear-gradient(90deg, #00ff88 0%, #00ccff 100%);
            color: #000;
            font-weight: bold;
            border-radius: 8px;
            border: none;
            padding: 10px;
            transition: all 0.3s ease;
        }
        .stButton > button:hover {
            transform: scale(1.02);
            box-shadow: 0 0 15px rgba(0, 255, 136, 0.4);
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

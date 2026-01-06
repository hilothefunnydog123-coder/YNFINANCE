import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import google.generativeai as genai
from groq import Groq
from PIL import Image
import requests

# --- 1. GOOGLE SEARCH CONSOLE TAG ---
components.html(
    f"""<script>
        var meta = document.createElement('meta');
        meta.name = "google-site-verification";
        meta.content = "HTd_e07Z3vt7rxoCVHyfti8A1mm9sWs_eRSETKtN-BY";
        parent.document.getElementsByTagName('head')[0].appendChild(meta);
    </script>""", height=0,
)

# --- 2. DARK MODE UI STYLING (CSS) ---
st.set_page_config(page_title="YNFINANCE | AI Terminal", page_icon="🌱", layout="wide")

st.markdown("""
    <style>
    /* Main Background */
    .stApp {
        background-color: #0E1117;
        color: #FFFFFF;
    }
    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
        background-color: #161B22;
        padding: 10px;
        border-radius: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        color: #8B949E;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        color: #58A6FF !important;
        border-bottom-color: #58A6FF !important;
    }
    /* Metric / Card Styling */
    div[data-testid="stMetricValue"] {
        font-size: 24px;
        color: #58A6FF;
    }
    /* Global Buttons */
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        background-color: #238636;
        color: white;
        border: none;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: #2ea043;
        transform: translateY(-2px);
    }
    </style>
    """, unsafe_allow_html=True)

# API Setup
groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"]) if "GROQ_API_KEY" in st.secrets else None
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    vision_model = genai.GenerativeModel('gemini-2.0-flash')

# --- 3. DATA ENGINE ---
@st.cache_data(ttl=3600)
def get_full_sp500_ranked():
    url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    tickers = pd.read_html(response.text)[0]['Symbol'].str.replace('.', '-').tolist()
    data = yf.download(tickers, period="2d", group_by='ticker', progress=False)
    
    ranked_list = []
    for t in tickers:
        try:
            df = data[t]

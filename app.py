import streamlit as st
import pandas as pd
import plotly.express as px
import io

# --- 1. Page Config ---
st.set_page_config(page_title="GDTD Dashboard", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    .stApp { background-color: #121417; color: #F0F2F6; }
    [data-testid="stSidebar"] { background-color: #1a1d21; border-right: 1px solid #333; }
    
    .block-container { 
        padding-top: 1.8rem !important; 
        padding-bottom: 2rem !important; 
    } 

    p, span, label, div, h1, h2, h3, .stMetric label, [data-testid="stMarkdownContainer"] p, 
    .stMultiSelect label, .stSlider label { 
        color: #F0F2F6 !important; 
    } 

    /* Gombok stílusa */
    div.stButton > button, [data-testid="stBaseButton-secondary"] {
        background-color: #262730 !important;
        color: #FFFFFF !important;
        border: 1px solid #4B4B4B !important;
        width: 100%;
        transition: all 0.3s ease;
    }
    
    div.stButton > button:hover, [data-testid="stBaseButton-secondary"]:hover {
        background-color: #00FF41 !important;
        color: #000000 !important;
        border-color: #00FF41 !important;
    }

    .sidebar-cite {
        font-size: 0.85rem !important;
        background-color: #262730;
        padding: 10px;
        border-radius: 5px;
        border: 1px solid #4B4B4B;
        margin-bottom: 20px;
    }
    .sidebar-cite a { color: #D3D3D3 !important; text-decoration: underline; }

    .main-title {
        font-size: 1.6rem !important;
        font-weight: 800;
        color: #FFFFFF !important;
        line-height: 1.0;
        margin-bottom: 0;
    }

    [data-testid="stMetric"] {
        background-color: #1e2124;
        padding: 5px 12px;
        border-radius: 4px;
        border-left: 3px solid #FFFFFF;
    }

    .chart-container {
        background-color: #FFFFFF;
        padding: 15px;
        border-radius: 4px;
        border: 1px solid #E0E0E0;
        margin-bottom: 20px;
    }

    .footer-note {
        font-size: 0.75rem;
        color: #888888 !important;
        margin-top: 20px;
        border-top: 1px solid #333;
        padding-top: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. Data Loading ---
@st.cache_data
def load_data():
    filename = "Acled_GTD_Drone_Database_20260509.csv"
    try:
        # Ellenőrizzük, hogy a fájl a "sep=;" sorral kezdődik-e
        with open(filename, 'r', encoding='utf-8-sig') as f:
            first_line = f.readline()
        
        # Ha benne van a sep=; jelzés, átugorjuk az első sort (skiprows=1)
        skip = 1 if "sep=" in first_line else 0
        
        # Beolvasás pontosvessző elválasztóval
        df = pd.read_csv(filename, sep=';', skiprows=skip, engine='python', encoding='utf-8-sig')
        
        # Oszlopnevek egységesítése (kisbetű, szóközmentes)
        df.columns = df.columns.str.strip().str.lower()
        
        # Dátum oszlop létrehozása a térképes hoverhez
        def create_date(row):
            try:
                return f"{int(row['year'])}-{int(row['month']):02d}-{int(row['day']):02d}"
            except:
                return str(row.get('year', 'N/A'))
        
        df['formatted_date'] = df.apply(create_date, axis=1)

        # Forrás oszlop elnevezése (ha dbsource néven van a CSV-ben)
        if 'dbsource' in df.columns:
            df.rename(columns={'dbsource': 'data_source'}, inplace=True)
        
        # Actor kategória meghatározása
        def categorize_actor(name):
            name = str(name).strip()
            if name.lower() == 'unknown': return 'Unknown'
            elif name.lower().startswith('unidentified'): return 'Unidentified'
            else: return 'Terrorist Organization'
        
        actor_col = 'gname' if 'gname' in df.columns else 'actor1'
        if actor_col in df.columns:
            df['actor_category'] = df[actor_col].apply(categorize_actor)
        else:
            df['actor_category'] = 'Unknown'
            
        return df
    except Exception as e:
        # Hiba esetén kiírjuk a technikai részleteket a sidebarba a javításhoz
        st.sidebar.error(f"Hiba a CSV beolvasásakor: {e}")
        return pd.DataFrame()

df_raw = load_data()

if not df_raw.empty:
    # --- 3. Sidebar Filters ---
    with st.sidebar:
        st.markdown(f"""
        <div class="sidebar-cite">
        <b>Cite as:</b><br>
        Besenyő, J.; Edelmann, D. (2026): Global Drone Terrorism Database (GDTD). Figshare. <br>
        <a href="https://doi.org/10.6084/m9.figshare.32128399" target="_blank">DOI: 10.6084/m9.figshare.32128399</a><br>
        License: CC BY 4.0
        </div>
        """, unsafe_allow_html=True)

        st.markdown("### Filters")
        
        # --- MANUAL SZŰRŐ ---
        manual_filter = st.toggle("Manual Filter (Terrorist Attack Only)", value=False)

        # Év szűrő
        if 'year' in df_raw.columns:
            years = sorted(df_raw['year'].dropna().unique().astype(int))
            yr_range = st.select_slider("Period", options=years, value=(min(years), max(years)))
            df_filtered = df_raw[(df_raw['year'] >= yr_range

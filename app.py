import streamlit as st
import pandas as pd
import plotly.express as px
import io

# --- 1. Page Config ---
st.set_page_config(page_title="GDTD Dashboard", layout="wide", initial_sidebar_state="expanded")

# Agresszív CSS a Streamlit gyári piros/kék színeinek felülírására
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    .stApp { background-color: #121417; color: #F0F2F6; }
    [data-testid="stSidebar"] { background-color: #1a1d21; border-right: 1px solid #333; }
    
    /* FELSŐ HELY MEGTAKARÍTÁSA */
    .block-container { 
        padding-top: 1rem !important; 
        padding-bottom: 2rem !important; 
    } 

    /* GOMBOK ÉS ELEMENTEK SZÍNEZÉSE - MINDENRE KITERJEDŐEN */
    div.stButton > button, 
    div.stDownloadButton > button, 
    button[kind="secondary"],
    [data-testid="stBaseButton-secondary"],
    [data-testid="stBaseButton-primary"] {
        background-color: #262730 !important;
        color: #FFFFFF !important;
        border: 1px solid #4B4B4B !important;
        width: 100%;
        transition: all 0.3s ease;
    }
    
    div.stButton > button:hover, 
    div.stDownloadButton > button:hover,
    [data-testid="stBaseButton-secondary"]:hover,
    [data-testid="stBaseButton-primary"]:hover {
        background-color: #00FF41 !important;
        color: #000000 !important;
        border-color: #00FF41 !important;
    }

    /* INPUTOK ÉS SZŰRŐK SZÍNEI */
    div[data-baseweb="select"] > div { background-color: #262730 !important; border-color: #4B4B4B !important; }
    div[data-baseweb="popover"] * { color: #000000 !important; }
    
    /* Feliratok színe */
    p, span, label, div, h1, h2, h3, .stMetric label, [data-testid="stMarkdownContainer"] p { 
        color: #F0F2F6 !important; 
    } 

    .sidebar-cite {
        font-size: 0.85rem !important;
        background-color: #262730;
        padding: 10px;
        border-radius: 5px;
        border: 1px solid #4B4B4B;
        margin-bottom: 20px;
    }

    .main-title {
        font-size: 1.6rem !important;
        font-weight: 800;
        color: #FFFFFF !important;
        line-height: 1.0;
        margin: 0;
    }

    [data-testid="stMetric"] {
        background-color: #1e2124;
        padding: 5px 12px;
        border-radius: 4px;
        border-left: 3px solid #FFFFFF;
    }

    .chart-container {
        background-color: #FFFFFF;
        padding: 10px;
        border-radius: 2px;
        border: 2px solid #000000;
        margin-bottom: 20px;
    }

    .footer-note {
        font-size: 0.75rem;
        color: #888888 !important;
        margin-top: 20px;
        border-top: 1px solid #333;
        padding-top: 10px;
    }
    
    /* Teszt sor */
    .debug-info { font-size: 0.65rem; color: #444 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. Data Loading ---
@st.cache_data
def load_data():
    filename = "Acled_GTD_Drone_Database_20260509.csv"
    try:
        # Beolvasás: sep=; sor átugrása ha van, oszlopnevek tisztítása
        df = pd.read_csv(filename, sep=';', skiprows=0, engine='python', encoding='utf-8-sig')
        if "sep=" in str(df.columns[0]):
            df = pd.read_csv(filename, sep=';', skiprows=1, engine='python', encoding='utf-8-sig')
        
        df.columns = df.columns.str.strip().str.lower()
        
        # Dátum generálás
        def create_date(row):
            try: return f"{int(row['year'])}-{int(row['month']):02d}-{int(row['day']):02d}"
            except: return str(row.get('year', ''))
        df['formatted_date'] = df.apply(create_date, axis=1)

        # Forrás oszlop elnevezése
        if 'adatforras' in df.columns:
            df.rename(columns={'adatforras': 'data_source'}, inplace=True)
        elif 'dbsource' in df.columns:
            df.rename(columns={'dbsource': 'data_source'}, inplace=True)

        return df
    except Exception as e:
        return pd.DataFrame()

df_raw = load_data()

if not df_raw.empty:
    # --- 3. Sidebar Filters ---
    with st.sidebar:
        # TESZT SZÁMLÁLÓ (Később eltávolítható)
        st.markdown(f'<div class="debug-info">DEBUG: Total records in CSV: {len(df_raw)}</div>', unsafe_allow_html=True)

        st.markdown("""
        <div class="sidebar-cite">
        <b>Cite as:</b><br>
        Besenyő, J.; Edelmann, D. (2026): Global Drone Terrorism Database (GDTD). Figshare. <br>
        <a href="https://doi.org/10.6084/m9.figshare.32128399" target="_blank">DOI: 10.6084/m9.figshare.32128399</a>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("### Filters")
        
        # 1. PONT: MANUAL FILTER TOGGLE
        manual_on = st.toggle("Manual Filter: Terrorist Attacks Only", value=False)
        if manual_on and 'manual' in df_raw.columns:
            df_filtered = df_raw[df_raw['manual'] == "terrorist attack"].copy()
        else:
            df_filtered = df_raw.copy()

        # ÉV SZŰRŐ
        if 'year' in df_filtered.columns:
            years = sorted(df_filtered['year'].dropna().unique().astype(int))
            yr_range = st.select_slider("Period", options=years, value=(min(years), max(years)))
            df_filtered = df_filtered[(df_filtered['year'] >= yr_range[0]) & (df_filtered['year'] <= yr_range[1])]

        # ADATFORRÁS SZŰRŐ
        if 'data_source' in df_filtered.columns:
            srcs = sorted(df_filtered['data_source'].unique())
            sel_srcs = st.multiselect("Data Source", srcs, default=srcs)
            df_filtered = df_filtered[df_filtered['data_source'].isin(sel_srcs)]

        # ORSZÁG SZŰRŐ
        if 'country_txt' in df_filtered.columns:
            cntrs = sorted(df_filtered['country_txt'].dropna().unique())
            sel_cntrs = st.multiselect("Country", cntrs, default=cntrs)
            df_filtered = df_filtered[df_filtered['country_txt'].isin(sel_cntrs)]

        # TÁMADÁS TÍPUSA
        if 'attacktype1_txt' in df_filtered.columns:
            atks = sorted(df_filtered['attacktype1_txt'].dropna().unique())
            sel_atks = st.multiselect("Attack Type", atks, default=atks)
            df_filtered = df_filtered[df_filtered['attacktype1_txt'].isin(sel_atks)]

        st.markdown("---")
        st.markdown("### Export")
        csv_data = df_filtered.to_csv(index=False, sep=';', encoding='utf-8-sig')
        st.download_button("Download CSV", csv_data, "GDTD_filtered.csv", "text/csv")

    # --- 4. Header & Metrics ---
    h1, h2, h3, h4 = st.columns([2.5, 1, 1, 1])
    with h1: st.markdown('<p class="main-title">GLOBAL DRONE<br>TERRORISM DATABASE</p>', unsafe_allow_html=True)
    with h2: st.metric("INCIDENTS", len(df_filtered))
    with h3: st.metric("COUNTRIES", df_filtered['country_txt'].nunique() if 'country_txt' in df_filtered.columns else 0)
    with h4:
        # Biztonságos összegzés a hibák elkerülésére
        if 'nkill' in df_filtered.columns:
            f_val = pd.to_numeric(df_filtered['nkill'], errors='coerce').sum()
            st.metric("FATALITIES", int(f_val if pd.notnull(f_val) else 0))
        else:
            st.metric("FATALITIES", 0)

    st.markdown("<hr style='margin:10px 0px'>", unsafe_allow_html=True)

    # --- 5. Map ---
    if not df_filtered.empty:
        df_filtered['latitude'] = pd.to_numeric(df_filtered['latitude'], errors='coerce')
        df_filtered['longitude'] = pd.to_numeric(df_filtered['longitude'], errors='coerce')
        df_map = df_filtered.dropna(subset=['latitude', 'longitude'])
        
        # Színkódolás a halálos kimenetel alapján
        df_map['lethality'] = pd.to_numeric(df_map['nkill'], errors='coerce').fillna(0).apply(lambda x: "Fatal Attack" if x > 0 else "Non-Fatal")

        fig_map = px.scatter_mapbox(
            df_map, lat='latitude', lon='longitude', 
            size=pd.to_numeric(df_map['nkill'], errors='coerce').fillna(0) + 3,
            color='lethality', color_discrete_map={'Fatal Attack': '#FF8C00', 'Non-Fatal':

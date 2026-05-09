import streamlit as st
import pandas as pd
import plotly.express as px
import io

# --- 1. Page Config ---
st.set_page_config(page_title="GDTD Dashboard", layout="wide", initial_sidebar_state="expanded")

# Agresszív CSS a gombok és az elrendezés javítására
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    .stApp { background-color: #121417; color: #F0F2F6; }
    [data-testid="stSidebar"] { background-color: #1a1d21; border-right: 1px solid #333; }
    
    /* Elrendezés: Feljebb kezdődjön a tartalom */
    .block-container { 
        padding-top: 1rem !important; 
        padding-bottom: 2rem !important; 
    } 
    [data-testid="stVerticalBlock"] > div:first-child { margin-top: 0rem !important; }

    /* GOMBOK SZÍNE: Sötétszürke -> Zöld hover */
    /* Targetálunk minden lehetséges Streamlit gomb típust */
    button, [data-testid="stBaseButton-secondary"], [data-testid="stBaseButton-primary"], .stDownloadButton button {
        background-color: #262730 !important;
        color: #FFFFFF !important;
        border: 1px solid #4B4B4B !important;
        width: 100%;
        border-radius: 4px !important;
        transition: all 0.3s ease !important;
    }
    
    button:hover, [data-testid="stBaseButton-secondary"]:hover, [data-testid="stBaseButton-primary"]:hover, .stDownloadButton button:hover {
        background-color: #00FF41 !important;
        color: #000000 !important;
        border-color: #00FF41 !important;
    }

    /* Feliratok és inputok színe */
    p, span, label, div, h1, h2, h3, .stMetric label, [data-testid="stMarkdownContainer"] p, 
    .stMultiSelect label, .stSlider label, .stToggle label p { 
        color: #F0F2F6 !important; 
    } 

    div[data-baseweb="select"] > div { background-color: #262730 !important; border-color: #4B4B4B !important; }
    div[data-baseweb="popover"] * { color: #000000 !important; }

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
    
    [data-testid="stMetricValue"] { color: #FFFFFF !important; font-size: 1.8rem !important; }

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

    /* DEBUG felirat stílusa */
    .debug-text { font-size: 0.65rem; color: #444 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. Data Loading ---
@st.cache_data
def load_data():
    filename = "Acled_GTD_Drone_Database_20260509.csv"
    try:
        # Beolvasás pontosvesszővel, sep=; sor kezelése
        df = pd.read_csv(filename, sep=';', skiprows=0, engine='python', encoding='utf-8-sig')
        if "sep=" in str(df.columns[0]):
            df = pd.read_csv(filename, sep=';', skiprows=1, engine='python', encoding='utf-8-sig')
        
        # Oszlopnevek tisztítása (kisbetű, szóközmentes)
        df.columns = df.columns.str.strip().str.lower()
        
        # Dátum készítése
        def create_date(row):
            try: return f"{int(row['year'])}-{int(row['month']):02d}-{int(row['day']):02d}"
            except: return str(row.get('year', ''))
        df['formatted_date'] = df.apply(create_date, axis=1)

        # Forrás oszlop elnevezése
        if 'adatforras' in df.columns:
            df.rename(columns={'adatforras': 'data_source'}, inplace=True)
        elif 'dbsource' in df.columns:
            df.rename(columns={'dbsource': 'data_source'}, inplace=True)
        else:
            df['data_source'] = "Unknown"

        return df
    except Exception as e:
        return pd.DataFrame()

df_raw = load_data()

if not df_raw.empty:
    # --- 3. Sidebar Filters ---
    with st.sidebar:
        # PONT 3: Teszt számláló
        st.markdown(f'<div class="debug-text">DEBUG: Total rows read from CSV: {len(df_raw)}</div>', unsafe_allow_html=True)

        st.markdown("""
        <div class="sidebar-cite">
        <b>Cite as:</b><br>
        Besenyő, J.; Edelmann, D. (2026): Global Drone Terrorism Database (GDTD). Figshare. <br>
        <a href="https://doi.org/10.6084/m9.figshare.32128399" target="_blank">DOI: 10.6084/m9.figshare.32128399</a>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("### Filters")
        
        # PONT 1: MANUAL FILTER
        manual_active = st.toggle("Terrorist Attacks Only (Manual Filter)", value=False)
        if manual_active and 'manual' in df_raw.columns:
            df_filtered = df_raw[df_raw['manual'].str.contains("terrorist attack", case=False, na=False)].copy()
        else:
            df_filtered = df_raw.copy()

        # Év szűrő
        if 'year' in df_filtered.columns:
            years = sorted(df_filtered['year'].dropna().unique().astype(int))
            yr_range = st.select_slider("Period", options=years, value=(min(years), max(years)))
            df_filtered = df_filtered[(df_filtered['year'] >= yr_range[0]) & (df_filtered['year'] <= yr_range[1])]

        # Forrás szűrő
        if 'data_source' in df_filtered.columns:
            srcs = sorted(df_filtered['data_source'].dropna().unique())
            sel_srcs = st.multiselect("Data Source", srcs, default=srcs)
            df_filtered = df_filtered[df_filtered['data_source'].isin(sel_srcs)]

        # Ország szűrő
        if 'country_txt' in df_filtered.columns:
            cntrs = sorted(df_filtered['country_txt'].dropna().unique())
            sel_cntrs = st.multiselect("Country", cntrs, default=cntrs)
            df_filtered = df_filtered[df_filtered['country_txt'].isin(sel_cntrs)]

        st.markdown("---")
        st.markdown("### Export")
        csv_exp = df_filtered.to_csv(index=False, sep=';', encoding='utf-8-sig')
        st.download_button("Download CSV", csv_exp, "GDTD_filtered.csv", "text/csv")

    # --- 4. Header & Metrics ---
    h1, h2, h3, h4 = st.columns([2.5, 1, 1, 1])
    with h1: st.markdown('<p class="main-title">GLOBAL DRONE<br>TERRORISM DATABASE</p>', unsafe_allow_html=True)
    with h2: st.metric("INCIDENTS", len(df_filtered))
    with h3: st.metric("COUNTRIES", df_filtered['country_txt'].nunique() if 'country_txt' in df_filtered.columns else 0)
    with h4:
        kills = pd.to_numeric(df_filtered['nkill'], errors='coerce').sum() if 'nkill' in df_filtered.columns else 0
        st.metric("FATALITIES", int(kills if pd.notnull(kills) else 0))

    st.markdown("<hr style='margin:10px 0px'>", unsafe_allow_html=True)

    # --- 5. Main Map ---
    if not df_filtered.empty:
        df_filtered['latitude'] = pd.to_numeric(df_filtered['latitude'], errors='coerce')
        df_filtered['longitude'] = pd.to_numeric(df_filtered['longitude'], errors='coerce')
        df_map = df_filtered.dropna(subset=['latitude', 'longitude'])
        
        df_map['lethality'] = pd.to_numeric(df_map['nkill'], errors='coerce').fillna(0).apply(lambda x: "Fatal Attack" if x > 0 else "Non-Fatal")

        fig_map = px.scatter_mapbox(
            df_map, lat='latitude', lon='longitude', 
            size=pd.to_numeric(df_map['nkill'], errors='coerce').fillna(0) + 3,
            color='lethality', color_discrete_map={'Fatal Attack': '#FF8C00', 'Non-Fatal': '#00FF41'},
            zoom=1.5, height=500, mapbox_style="carto-darkmatter",
            hover_name='city',
            hover_data={'formatted_date': True,

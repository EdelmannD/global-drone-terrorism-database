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
    
    /* GOMBOK: Visszaállítás sötétszürkére, ahogy kérted */
    div.stButton > button, [data-testid="stBaseButton-secondary"], .stDownloadButton > button {
        background-color: #262730 !important;
        color: #FFFFFF !important;
        border: 1px solid #4B4B4B !important;
        width: 100%;
        transition: all 0.3s ease;
    }
    
    /* HOVER: Zöld */
    div.stButton > button:hover, [data-testid="stBaseButton-secondary"]:hover, .stDownloadButton > button:hover {
        background-color: #00FF41 !important;
        color: #000000 !important;
        border-color: #00FF41 !important;
    }

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
    
    /* Teszt sor stílusa */
    .test-counter {
        font-size: 0.7rem;
        color: #444 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. Data Loading ---
@st.cache_data
def load_data():
    filename = "Acled_GTD_Drone_Database_20260509.csv"
    try:
        with open(filename, 'r', encoding='utf-8-sig') as f:
            first_line = f.readline()
        skip = 1 if "sep=" in first_line else 0
        df = pd.read_csv(filename, sep=';', skiprows=skip, engine='python', encoding='utf-8-sig')
        
        # Oszlopnevek tisztítása
        df.columns = df.columns.str.strip()
        
        # Dátum készítése
        def create_date(row):
            try:
                return f"{int(row['year'])}-{int(row['month']):02d}-{int(row['day']):02d}"
            except:
                return str(row.get('year', 'N/A'))
        df['formatted_date'] = df.apply(create_date, axis=1)

        # Actor kategória
        def categorize_actor(name):
            name = str(name).strip().lower()
            if 'unknown' in name: return 'Unknown'
            elif 'unidentified' in name: return 'Unidentified'
            else: return 'Terrorist Organization'
        
        if 'gname' in df.columns:
            df['actor_category'] = df['gname'].apply(categorize_actor)
            
        return df
    except Exception as e:
        st.error(f"Hiba: {e}")
        return pd.DataFrame()

df_raw = load_data()

if not df_raw.empty:
    # 3. PONT: TESZT SZÁMLÁLÓ (kicsi, sötét betűvel a sidebar tetején)
    st.sidebar.markdown(f'<p class="test-counter">DEBUG: Total rows in CSV: {len(df_raw)}</p>', unsafe_allow_html=True)

    # --- 3. Sidebar Filters ---
    with st.sidebar:
        st.markdown(f"""
        <div class="sidebar-cite">
        <b>Cite as:</b><br>
        Besenyő, J.; Edelmann, D. (2026): Global Drone Terrorism Database (GDTD). Figshare. <br>
        <a href="https://doi.org/10.6084/m9.figshare.32128399" target="_blank">DOI: 10.6084/m9.figshare.32128399</a>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("### Filters")
        
        # 1. MANUAL FILTER
        if 'manual' in df_raw.columns:
            m_opts = sorted(df_raw['manual'].dropna().unique())
            sel_m = st.multiselect("Manual Filter", m_opts, default=m_opts)
            df_filtered = df_raw[df_raw['manual'].isin(sel_m)].copy()
        else:
            df_filtered = df_raw.copy()

        # 2. PERIOD
        if 'year' in df_filtered.columns:
            years = sorted(df_filtered['year'].dropna().unique().astype(int))
            yr_range = st.select_slider("Period", options=years, value=(min(years), max(years)))
            df_filtered = df_filtered[(df_filtered['year'] >= yr_range[0]) & (df_filtered['year'] <= yr_range[1])]

        # 2. PONT JAVÍTÁSA: DATA SOURCE (dbsource oszlop használata)
        source_col = 'dbsource' if 'dbsource' in df_filtered.columns else ('adatforras' if 'adatforras' in df_filtered.columns else None)
        if source_col:
            sources = sorted(df_filtered[source_col].dropna().unique())
            selected_sources = st.multiselect("Data Source", sources, default=sources)
            df_filtered = df_filtered[df_filtered[source_col].isin(selected_sources)]

        # COUNTRY
        if 'country_txt' in df_filtered.columns:
            countries = sorted(df_filtered['country_txt'].dropna().unique())
            sel_c = st.multiselect("Country", countries, default=countries)
            df_filtered = df_filtered[df_filtered['country_txt'].isin(sel_c)]

        st.markdown("---")
        csv_data = df_filtered.to_csv(index=False, sep=';', encoding='utf-8-sig')
        st.download_button("Download CSV", csv_data, "GDTD_export.csv", "text/csv")

    # --- 4. Header Metrics ---
    c1, c2, c3, c4 = st.columns([2.5, 1, 1, 1])
    with c1: st.markdown('<p class="main-title">GLOBAL DRONE<br>TERRORISM DATABASE</p>', unsafe_allow_html=True)
    with c2: st.metric("INCIDENTS", len(df_filtered))
    with c3: st.metric("COUNTRIES", df_filtered['country_txt'].nunique() if 'country_txt' in df_filtered else 0)
    with c4: 
        kills = pd.to_numeric(df_filtered['nkill'], errors='coerce').sum()
        st.metric("FATALITIES", int(kills if pd.notnull(kills) else 0))

    st.markdown("<hr style='margin:10px 0px'>", unsafe_allow_html=True)

    # --- 5. Map ---
    if not df_filtered.empty:
        df_filtered['latitude'] = pd.to_numeric(df_filtered['latitude'], errors='coerce')
        df_filtered['longitude'] = pd.to_numeric(df_filtered['longitude'], errors='coerce')
        df_map = df_filtered.dropna(subset=['latitude', 'longitude'])
        
        fig_map = px.scatter_mapbox(
            df_map, lat='latitude', lon='longitude', 
            size=pd.to_numeric(df_map['nkill'], errors='coerce').fillna(0) + 3,
            color_discrete_sequence=['#00FF41'],
            zoom=1.5, height=550, mapbox_style="carto-darkmatter",
            hover_name='city',
            hover_data={'formatted_date': True, 'gname': True, 'nkill': True}
        )
        fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_map, use_container_width=True)

    # --- 4. PONT: FOOTER VISSZAÁLLÍTÁSA ---
    st.markdown("""
        <div class="footer-note">
            <b>Data sources:</b><br>
            GTD: START - National Consortium for the Study of Terrorism and Responses to Terrorism, Global Terrorism Database, 1970 - 2022, 2025 database, 2025. <br>
            ACLED: C. Raleigh, A. Linke, H. Hegre, J. Karlsen, Introducing ACLED: An armed conflict location and event dataset, J. Peace Res. 47, 2010.
        </div>
    """, unsafe_allow_html=True)
else:
    st.error("Dataset error.")

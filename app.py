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
    [data-testid="stVerticalBlock"] > div:first-child { margin-top: 0rem !important; }

    p, span, label, div, h1, h2, h3, .stMetric label, [data-testid="stMarkdownContainer"] p, 
    .stMultiSelect label, .stSlider label { 
        color: #F0F2F6 !important; 
    } 

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

    div[data-baseweb="popover"] * { color: #000000 !important; }
    div[data-baseweb="popover"] { background-color: #ffffff !important; border-radius: 4px; }
    div[role="listbox"] li { background-color: #ffffff !important; color: #000000 !important; }
    div[role="listbox"] li:hover { background-color: #eeeeee !important; }

    .sidebar-cite {
        font-size: 0.85rem !important;
        background-color: #262730;
        padding: 10px;
        border-radius: 5px;
        border: 1px solid #4B4B4B;
        margin-bottom: 20px;
    }
    .sidebar-cite a { color: #D3D3D3 !important; text-decoration: underline; }

    div[data-baseweb="select"] > div {
        background-color: #262730 !important;
        border-color: #4B4B4B !important;
    }

    div[data-baseweb="slider"] > div > div > div { background-color: #00FF41 !important; }
    div[role="slider"] { background-color: #00FF41 !important; border: 2px solid #FFFFFF !important; }
    
    span[data-baseweb="tag"] { background-color: #444 !important; color: white !important; }

    .main-title {
        font-size: 1.6rem !important;
        font-weight: 800;
        color: #FFFFFF !important;
        line-height: 1.0;
        margin-top: 0px;
        margin-bottom: 0;
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
        padding-bottom: 10px;
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
        df.columns = df.columns.str.strip().str.lower()
        
        # SZŰRÉS: Csak a "terrorist attack" sorok megtartása az új manual oszlop alapján
        if 'manual' in df.columns:
            df = df[df['manual'] == 'terrorist attack'].copy()
        
        def create_date(row):
            try:
                return f"{int(row['year'])}-{int(row['month']):02d}-{int(row['day']):02d}"
            except:
                return str(row.get('year', ''))
        
        df['formatted_date'] = df.apply(create_date, axis=1)

        # Forrás oszlop harmonizálása
        if 'adatforras' in df.columns:
            df.rename(columns={'adatforras': 'data_source'}, inplace=True)
        elif 'dbsource' in df.columns:
            df.rename(columns={'dbsource': 'data_source'}, inplace=True)
        
        def categorize_actor(name):
            name = str(name).strip()
            if name.lower() == 'unknown':
                return 'Unknown'
            elif name.lower().startswith('unidentified'):
                return 'Unidentified'
            else:
                return 'Terrorist Organization'
        
        if 'gname' in df.columns:
            df['actor_category'] = df['gname'].apply(categorize_actor)
        else:
            df['actor_category'] = 'Unknown'
            
        return df
    except Exception as e:
        # st.error(f"Hiba: {e}") # Debughoz visszakapcsolható
        return pd.DataFrame()

df_raw = load_data()

if not df_raw.empty:
    lat_col, lon_col = 'latitude', 'longitude'
    year_col, country_col = 'year', 'country_txt'
    fatal_col, source_col = 'nkill', 'data_source'
    city_col = 'city'

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
        
        if year_col in df_raw.columns:
            years = sorted(df_raw[year_col].dropna().unique().astype(int))
            if years:
                yr_range = st.select_slider("Period", options=years, value=(min(years), max(years)))
                df_filtered = df_raw[(df_raw[year_col] >= yr_range[0]) & (df_raw[year_col] <= yr_range[1])].copy()
        else:
            df_filtered = df_raw.copy()

        sources = sorted(df_filtered[source_col].unique()) if source_col in df_filtered.columns else []
        selected_sources = st.multiselect("Data Source", sources, default=sources)
        df_filtered = df_filtered[df_filtered[source_col].isin(selected_sources)]

        actor_cats = sorted(df_filtered['actor_category'].unique())
        selected_actors = st.multiselect("Actor Type", actor_cats, default=actor_cats)
        df_filtered = df_filtered[df_filtered['actor_category'].isin(selected_actors)]

        countries = sorted(df_filtered[country_col].dropna().unique()) if country_col in df_filtered.columns else []
        selected_countries = st.multiselect("Country", countries, default=countries)
        df_filtered = df_filtered[df_filtered[country_col].isin(selected_countries)]

        attack_types_list = sorted(df_filtered['attacktype1_txt'].fillna("N/A").unique())
        selected_types = st.multiselect("Attack Type", attack_types_list, default=attack_types_list)
        df_filtered = df_filtered[df_filtered['attacktype1_txt'].fillna("N/A").isin(selected_types)]

        # --- EXPORT SECTION ---
        st.markdown("---")
        st.markdown("### Export Filtered Data")
        
        csv_data = df_filtered.to_csv(index=False, sep=';', encoding='utf-8-sig')
        st.download_button(
            label="Download CSV",
            data=csv_data,
            file_name=f"GDTD_filtered_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
        )

        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_filtered.to_excel(writer, index=False, sheet_name='Filtered_Data')
        
        st.download_button(
            label="Download Excel",
            data=buffer.getvalue(),
            file_name=f"GDTD_filtered_{pd.Timestamp.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    # --- 4. Header ---
    header_col1, header

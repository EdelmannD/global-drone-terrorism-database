import streamlit as st
import pandas as pd
import plotly.express as px

# --- 1. Page Config & Professional Styling ---
st.set_page_config(page_title="GDTD Dashboard", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    /* Alap háttér és szöveg */
    .stApp { background-color: #121417; color: #E0E0E0; }
    
    /* Sidebar */
    [data-testid="stSidebar"] { background-color: #1a1d21; border-right: 1px solid #333; }
    
    /* Hivatkozás stílusa */
    .small-citation {
        font-size: 0.7rem;
        color: #999999;
        line-height: 1.3;
        margin-bottom: 20px;
    }
    
    /* Világosszürke feliratok a menüben */
    [data-testid="stSidebar"] label, 
    [data-testid="stSidebar"] .stMarkdown h3 { 
        color: #CCCCCC !important; 
        font-weight: normal !important;
        text-transform: uppercase;
        font-size: 0.85rem !important;
    }

    /* CSÚSZKA STÍLUSA */
    div[data-baseweb="slider"] > div > div { background-color: #444444 !important; } 
    div[data-baseweb="slider"] [role="slider"] { background-color: #FFFFFF !important; border: 1px solid #FFFFFF !important; }
    div[data-testid="stThumbValue"] { color: #FFFFFF !important; }
    
    /* Multiselect  */
    span[data-baseweb="tag"] { background-color: #FFFFFF !important; color: #000 !important; }

    /* Metric kártyák (Fehér széllel) */
    [data-testid="stMetric"] {
        background-color: #1e2124;
        padding: 10px 15px;
        border-radius: 4px;
        border-left: 3px solid #FFFFFF;
        width: 100%;
    }
    [data-testid="stMetricLabel"] { color: #999999 !important; font-size: 0.8rem !important; }
    [data-testid="stMetricValue"] { color: #FFFFFF !important; font-size: 1.5rem !important; }

    header[data-testid="stHeader"] { background-color: rgba(0,0,0,0) !important; }
    .block-container { padding-top: 1.5rem; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. Data Loading ---
@st.cache_data
def load_data():
    filename = "Acled_GTD_Drone_Database_20260429.csv"
    try:
        with open(filename, 'r', encoding='utf-8-sig') as f:
            first_line = f.readline()
        skip = 1 if "sep=" in first_line else 0
        
        df = pd.read_csv(filename, sep=';', skiprows=skip, engine='python', encoding='utf-8-sig')
        df.columns = df.columns.str.strip().str.lower()
        
        if 'adatforras' in df.columns:
            df.rename(columns={'adatforras': 'data_source'}, inplace=True)
            
        return df
    except Exception as e:
        return pd.DataFrame()

df_raw = load_data()

if not df_raw.empty:
    lat_col, lon_col = 'latitude', 'longitude'
    year_col, country_col = 'year', 'country_txt'
    fatal_col, source_col = 'nkill', 'data_source'
    group_col, type_col = 'gname', 'attacktype1_txt'
    target_col = 'targtype1_txt'

    # --- 3. Sidebar ---
    with st.sidebar:
        st.markdown(f"""
        <div class="small-citation">
        CITATION<br>
        J. Besenyő, D. Edelmann: Global Drone Terrorism Database (GDTD)<br>
        Source: Figshare database<br>
        DOI: <a href="https://doi.org/10.6084/m9.figshare.21381312" style="color:#FFFFFF; text-decoration:none;">10.6084/m9.figshare.21381312</a><br>
        License: CC-BY 4.0
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### Filters")
        
        sources = sorted(df_raw[source_col].unique()) if source_col in df_raw.columns else []
        selected_sources = st.multiselect("Data Source", sources, default=sources)
        df_filtered = df_raw[df_raw[source_col].isin(selected_sources)]

        if year_col in df_filtered.columns:
            years = sorted(df_filtered[year_col].dropna().unique().astype(int))
            yr_range = st.select_slider("Time Period", options=years, value=(min(years), max(years)))
            df_filtered = df_filtered[(df_filtered[year_col] >= yr_range[0]) & (df_filtered[year_col] <= yr_range[1])]

        countries = sorted(df_filtered[country_col].dropna().unique()) if country_col in df_filtered.columns else []
        sel_countries = st.multiselect("Country", countries)
        if sel_countries:
            df_filtered = df_filtered[df_filtered[country_col].isin(sel_countries)]

    # --- 4. Main Header (Felirat és Metrikák egymás mellett) ---
    # Az arányt 5:1:1:1-re állítottam, hogy a hatalmas betűk ne tolják el a többi mezőt
    header_col1, header_col2, header_col3, header_col4 = st.columns([2.8, 1, 1, 1])

    with header_col1:
        # Itt a kért 10rem méret, inline HTML-el kényszerítve
        st.markdown('<h1 style="font-size: 6rem !important; font-weight: bold; color: white; line-height: 0.9; margin: 0; padding: 0;">Global Drone<br>Terrorism Database</h1>', unsafe_allow_html=True)
    
    with header_col2:
        st.metric("INCIDENTS", len(df_filtered))
    
    with header_col3:
        st.metric("COUNTRIES", df_filtered[country_col].nunique())
    
    with header_col4:
        f_val = pd.to_numeric(df_filtered[fatal_col], errors='coerce').sum()
        st.metric("FATALITIES", int(f_val))

    st.markdown("<br>", unsafe_allow_html=True)

    # --- 5. Map ---
    df_filtered[lat_col] = pd.to_numeric(df_filtered[lat_col], errors='coerce')
    df_filtered[lon_col] = pd.to_numeric(df_filtered[lon_col], errors='coerce')
    df_map = df_filtered.dropna(subset=[lat_col, lon_col])

    fig_map = px.scatter_mapbox(
        df_map, lat=lat_col, lon=lon_col, 
        size=pd.to_numeric(df_map[fatal_col], errors='coerce').fillna(0) + 3,
        color=source_col,
        color_discrete_map={'GTD': '#FF8C00', 'ACLED': '#00FF41'},
        hover_name=country_col,
        zoom=1.2, height=600, mapbox_style="carto-darkmatter"
    )
    fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, paper_bgcolor='rgba(0,0,0,0)', legend=dict(font=dict(color="white")))
    st.plotly_chart(fig_map, use_container_width=True)

    # --- 6. Analytics ---
    st.markdown("---")
    t1, t2 = st.tabs(["STATISTICS", "DATA & EXPORT"])
    with t1:
        r1c1, r1c2 = st.columns(2)
        with r1c1:
            st.subheader("Trend")
            trend = df_filtered.groupby(year_col).size().reset_index(name='count')
            fig_l = px.line(trend, x=year_col, y='count', template="plotly_dark", color_discrete_sequence=['#FFFFFF'])
            st.plotly_chart(fig_l, use_container_width=True)
        with r1c2:
            st.subheader("Top Groups")
            top_groups = df_filtered[group_col].value_counts().head(10).reset_index()
            fig_g = px.bar(top_groups, x='count', y=group_col, orientation='h', template="plotly_dark", color_discrete_sequence=['#FFFFFF'])
            st.plotly_chart(fig_g, use_container_width=True)

        r2c1, r2c2 = st.columns(2)
        with r2c1:
            st.subheader("Attack Types")
            fig_p = px.pie(df_filtered, names=type_col, template="plotly_dark", hole=0.4)
            st.plotly_chart(fig_p, use_container_width=True)
        with r2c2:
            st.subheader("Target Types")
            top_targets = df_filtered[target_col].value_counts().head(10).reset_index()
            fig_t = px.bar(top_targets, x='count', y=target_col, orientation='h', template="plotly_dark", color_discrete_sequence=['#FFFFFF'])
            st.plotly_chart(fig_t, use_container_width=True)

    with t2:
        st.dataframe(df_filtered, use_container_width=True)

else:
    st.info("Loading dataset...")

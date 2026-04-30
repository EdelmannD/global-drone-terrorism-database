import streamlit as st
import pandas as pd
import plotly.express as px

# --- 1. Page Config & Styling ---
st.set_page_config(page_title="GDTD Dashboard", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    .stApp { background-color: #121417; color: #E0E0E0; }
    [data-testid="stSidebar"] { background-color: #1a1d21; border-right: 1px solid #333; }
    .small-citation { font-size: 0.7rem; color: #999999; line-height: 1.3; margin-bottom: 20px; }
    [data-testid="stSidebar"] label, [data-testid="stSidebar"] .stMarkdown h3 { 
        color: #CCCCCC !important; font-weight: normal !important; text-transform: uppercase; font-size: 0.85rem !important;
    }
    div[data-baseweb="slider"] > div > div { background-color: #00E5FF !important; } 
    div[data-baseweb="slider"] [role="slider"] { background-color: #00E5FF !important; border: 1px solid #00E5FF !important; }
    div[data-testid="stThumbValue"] { color: #00E5FF !important; }
    span[data-baseweb="tag"] { background-color: #00E5FF !important; color: #000 !important; }
    .main-title { font-size: 1.4rem; font-weight: bold; line-height: 1.1; color: #FFFFFF; margin-top: 0px; }
    [data-testid="stMetric"] { background-color: #1e2124; padding: 5px 10px; border-radius: 4px; border-left: 3px solid #00E5FF; }
    [data-testid="stMetricLabel"] { color: #999999 !important; font-size: 0.75rem !important; }
    [data-testid="stMetricValue"] { color: #FFFFFF !important; font-size: 1.2rem !important; }
    header[data-testid="stHeader"] { background-color: rgba(0,0,0,0) !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. Data Loading (Fixed for sep=; row) ---
@st.cache_data
def load_data():
    filename = "Acled_GTD_Drone_Database_20260429.csv"
    try:
        # Megnézzük az első sort. Ha "sep=", akkor a másodiktól olvassuk.
        with open(filename, 'r', encoding='utf-8-sig') as f:
            first_line = f.readline()
        
        skip = 1 if "sep=" in first_line else 0
        
        df = pd.read_csv(filename, sep=';', skiprows=skip, engine='python', encoding='utf-8-sig')
        df.columns = df.columns.str.strip().str.lower()
        
        # Oszlop átnevezése angolra a kérésed szerint
        if 'adatforras' in df.columns:
            df.rename(columns={'adatforras': 'data_source'}, inplace=True)
            
        return df
    except Exception as e:
        st.error(f"Error: {e}")
        return pd.DataFrame()

df_raw = load_data()

if not df_raw.empty:
    # A te CSV-d alapján ezek a pontos oszlopnevek (kisbetűsítve):
    lat_col = 'latitude'
    lon_col = 'longitude'
    year_col = 'year'
    country_col = 'country_txt'
    fatal_col = 'nkill'
    source_col = 'data_source'
    group_col = 'gname'
    type_col = 'attacktype1_txt'

    # --- 3. Sidebar ---
    with st.sidebar:
        st.markdown(f"""
        <div class="small-citation">
        CITATION<br>
        J. Besenyő, D. Edelmann: Global Drone Terrorism Database (GDTD)<br>
        Source: Figshare database<br>
        DOI: <a href="https://doi.org/10.6084/m9.figshare.21381312" style="color:#00E5FF; text-decoration:none;">10.6084/m9.figshare.21381312</a><br>
        License: CC-BY 4.0
        </div>
        """, unsafe_allow_html=True)
        st.markdown("### Filters")
        
        # Data Source Filter
        sources = sorted(df_raw[source_col].unique()) if source_col in df_raw.columns else []
        selected_sources = st.multiselect("Data Source", sources, default=sources)
        df_filtered = df_raw[df_raw[source_col].isin(selected_sources)]

        # Time Slider
        if year_col in df_filtered.columns:
            years = sorted(df_filtered[year_col].dropna().unique().astype(int))
            yr_range = st.select_slider("Time Period", options=years, value=(min(years), max(years)))
            df_filtered = df_filtered[(df_filtered[year_col] >= yr_range[0]) & (df_filtered[year_col] <= yr_range[1])]

    # --- 4. Main Header Row ---
    title_col, m1, m2, m3 = st.columns([1.8, 1, 1, 1])
    with title_col:
        st.markdown('<p class="main-title">Global Drone<br>Terrorism Database</p>', unsafe_allow_html=True)
    with m1:
        st.metric("INCIDENTS", len(df_filtered))
    with m2:
        st.metric("COUNTRIES", df_filtered[country_col].nunique())
    with m3:
        f_val = pd.to_numeric(df_filtered[fatal_col], errors='coerce').sum()
        st.metric("FATALITIES", int(f_val))

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
        zoom=1.2, height=500, mapbox_style="carto-darkmatter"
    )
    fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, paper_bgcolor='rgba(0,0,0,0)', legend=dict(font=dict(color="white")))
    st.plotly_chart(fig_map, use_container_width=True)

    # --- 6. Extended Analytics ---
    t1, t2 = st.tabs(["STATISTICS", "DATA & EXPORT"])
    with t1:
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Incident Trend")
            trend = df_filtered.groupby(year_col).size().reset_index(name='count')
            fig_l = px.line(trend, x=year_col, y='count', template="plotly_dark", color_discrete_sequence=['#00E5FF'])
            st.plotly_chart(fig_l, use_container_width=True)
        with c2:
            st.subheader("Top 10 Perpetrator Groups")
            top_groups = df_filtered[group_col].value_counts().head(10).reset_index()
            fig_g = px.bar(top_groups, x='count', y=group_col, orientation='h', template="plotly_dark", color_discrete_sequence=['#00E5FF'])
            fig_g.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_g, use_container_width=True)

        c3, c4 = st.columns(2)
        with c3:
            st.subheader("Attack Types")
            fig_p = px.pie(df_filtered, names=type_col, template="plotly_dark", hole=0.4)
            st.plotly_chart(fig_p, use_container_width=True)
        with c4:
            st.subheader("Fatalities by Country (Top 10)")
            fat_country = df_filtered.groupby(country_col)[fatal_col].sum().sort_values(ascending=False).head(10).reset_index()
            fig_fc = px.bar(fat_country, x=country_col, y=fatal_col, template="plotly_dark", color_discrete_sequence=['#00FF41'])
            st.plotly_chart(fig_fc, use_container_width=True)

    with t2:
        st.dataframe(df_filtered, use_container_width=True)
        csv = df_filtered.to_csv(index=False).encode('utf-8')
        st.download_button("Download Data (CSV)", csv, "gdtd_export.csv", "text/csv")

else:
    st.info("Loading or empty dataset...")

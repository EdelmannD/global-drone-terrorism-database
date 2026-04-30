import streamlit as st
import pandas as pd
import plotly.express as px
import io

# --- 1. Page Config & Professional Dark Theme ---
st.set_page_config(page_title="GDTD Dashboard", layout="wide")

st.markdown("""
    <style>
    /* Background and main text */
    .stApp { background-color: #121417; color: #E0E0E0; }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] { background-color: #1a1d21; border-right: 1px solid #333; }
    [data-testid="stSidebar"] .stMarkdown p, [data-testid="stSidebar"] label { color: #E0E0E0 !important; }
    
    /* FIX: Make the sidebar collapse button visible and white */
    [data-testid="stSidebarCollapsedControl"] {
        color: #FFFFFF !important;
        background-color: rgba(255, 255, 255, 0.1);
        border-radius: 0 5px 5px 0;
    }

    /* Metric Cards - Minimalist */
    [data-testid="stMetric"] {
        background-color: #1e2124;
        padding: 10px 15px;
        border-radius: 4px;
        border-left: 4px solid #808080;
    }
    [data-testid="stMetricLabel"] { color: #AAAAAA !important; font-size: 0.9rem !important; }
    [data-testid="stMetricValue"] { color: #FFFFFF !important; font-size: 1.5rem !important; }
    
    /* Clean top spacing without hiding the menu button */
    .block-container { padding-top: 2rem; padding-bottom: 0rem; }
    
    /* Gray alert for errors/warnings */
    .stAlert { background-color: #2b2e32; color: #E0E0E0; border: 1px solid #444; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. Data Loading ---
@st.cache_data
def load_data():
    filename = "Acled_GTD_Drone_Database_20260429.csv"
    try:
        with open(filename, 'r', encoding='utf-8-sig') as f:
            first_line = f.readline().strip()
        skip = 1 if 'sep=' in first_line else 0
        df = pd.read_csv(filename, sep=';', skiprows=skip, engine='python', encoding='utf-8-sig')
        df.columns = df.columns.str.strip().str.lower()
        return df
    except Exception as e:
        st.sidebar.error(f"Data loading error: {e}")
        return pd.DataFrame()

df_raw = load_data()

if not df_raw.empty:
    # Column mapping
    year_col = 'year' if 'year' in df_raw.columns else 'iyear'
    lat_col = 'latitude'
    lon_col = 'longitude'
    country_col = 'country_txt'
    fatal_col = 'nkill'
    group_col = 'gname'
    source_col = 'adatforras'

    # --- 3. Sidebar (Filters) ---
    st.sidebar.title("FILTERS")
    
    if source_col in df_raw.columns:
        sources = sorted(df_raw[source_col].unique())
        selected_sources = st.sidebar.multiselect("DATA SOURCE", sources, default=sources)
        df_filtered = df_raw[df_raw[source_col].isin(selected_sources)]
    else:
        df_filtered = df_raw

    if year_col in df_filtered.columns:
        years = sorted(df_filtered[year_col].dropna().unique().astype(int))
        yr_range = st.sidebar.select_slider("TIME PERIOD", options=years, value=(min(years), max(years)))
        df_filtered = df_filtered[(df_filtered[year_col] >= yr_range[0]) & (df_filtered[year_col] <= yr_range[1])]

    if country_col in df_filtered.columns:
        countries = sorted(df_filtered[country_col].dropna().unique())
        sel_countries = st.sidebar.multiselect("COUNTRY", countries)
        if sel_countries:
            df_filtered = df_filtered[df_filtered[country_col].isin(sel_countries)]

    # --- 4. Main Display ---
    head_col, m1, m2, m3 = st.columns([2, 1, 1, 1])
    
    with head_col:
        st.subheader("Global Drone Terrorism Database")
    
    with m1:
        st.metric("INCIDENTS", len(df_filtered))
    with m2:
        st.metric("COUNTRIES", df_filtered[country_col].nunique() if country_col in df_filtered.columns else "N/A")
    with m3:
        f_sum = int(pd.to_numeric(df_filtered[fatal_col], errors='coerce').sum()) if fatal_col in df_filtered.columns else 0
        st.metric("FATALITIES", f"{f_sum}")

    # --- 5. Map ---
    if lat_col in df_filtered.columns and lon_col in df_filtered.columns:
        df_filtered[lat_col] = pd.to_numeric(df_filtered[lat_col], errors='coerce')
        df_filtered[lon_col] = pd.to_numeric(df_filtered[lon_col], errors='coerce')
        df_map = df_filtered.dropna(subset=[lat_col, lon_col])

        fig_map = px.scatter_mapbox(
            df_map, lat=lat_col, lon=lon_col, 
            size=pd.to_numeric(df_map[fatal_col], errors='coerce').fillna(0) + 3,
            color=source_col,
            color_discrete_map={'GTD': '#FF8C00', 'ACLED': '#00FF41'},
            hover_name=country_col,
            zoom=1.4, height=600, mapbox_style="carto-darkmatter"
        )
        fig_map.update_layout(
            margin={"r":0,"t":0,"l":0,"b":0}, 
            paper_bgcolor='rgba(0,0,0,0)',
            legend=dict(font=dict(color="#E0E0E0"), bgcolor="rgba(0,0,0,0.5)")
        )
        st.plotly_chart(fig_map, use_container_width=True)

    # --- 6. Tabs ---
    t1, t2 = st.tabs(["STATISTICS", "DATA & EXPORT"])
    
    with t1:
        if year_col in df_filtered.columns:
            trend = df_filtered.groupby(year_col).size().reset_index(name='incidents')
            fig_trend = px.line(trend, x=year_col, y='incidents', template="plotly_dark")
            fig_trend.update_traces(line_color='#00FF41')
            st.plotly_chart(fig_trend, use_container_width=True)

    with t2:
        st.dataframe(df_filtered, use_container_width=True)
        csv = df_filtered.to_csv(index=False).encode('utf-8')
        st.download_button("Download Data (CSV)", csv, "gdtd_export.csv", "text/csv")

else:
    st.info("Waiting for data source...")

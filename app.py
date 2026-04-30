import streamlit as st
import pandas as pd
import plotly.express as px
import io

# --- 1. Konfiguráció és Letisztult Design ---
st.set_page_config(page_title="GDTD Dashboard", layout="wide")

# CSS a sötét témához és a fehér betűkhöz a sidebarban
st.markdown("""
    <style>
    .stApp { background-color: #121417; color: #FFFFFF; }
    [data-testid="stSidebar"] { background-color: #1a1d21; border-right: 1px solid #333; }
    /* Sidebar feliratok fehérítése */
    [data-testid="stSidebar"] .stMarkdown p, [data-testid="stSidebar"] label { color: #FFFFFF !important; }
    /* KPI kártyák stílusa ikonok nélkül */
    [data-testid="stMetric"] {
        background-color: #1e2124;
        padding: 15px;
        border-radius: 5px;
        border-left: 5px solid #FF8C00;
    }
    [data-testid="stMetricLabel"] { color: #FFFFFF !important; font-weight: normal; }
    /* Menüsor elrejtése a tetején (opcionális, de tisztább) */
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- 2. Adatbetöltés ---
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
        st.error(f"Hiba az adatok beolvasásakor: {e}")
        return pd.DataFrame()

df_raw = load_data()

if not df_raw.empty:
    # Oszlopok beállítása
    year_col = 'year' if 'year' in df_raw.columns else 'iyear'
    lat_col = 'latitude'
    lon_col = 'longitude'
    country_col = 'country_txt'
    fatal_col = 'nkill'
    group_col = 'gname'
    source_col = 'adatforras'

    # --- 3. Bal oldali menüsáv (Fehér betűkkel) ---
    st.sidebar.title("SZŰRŐK")
    
    # Adatforrás szűrő (ÚJ: Itt választható a GTD vs ACLED)
    if source_col in df_raw.columns:
        sources = sorted(df_raw[source_col].unique())
        selected_sources = st.sidebar.multiselect("ADATFORRÁS", sources, default=sources)
        df_filtered = df_raw[df_raw[source_col].isin(selected_sources)]
    else:
        df_filtered = df_raw

    # Időszak szűrő
    if year_col in df_filtered.columns:
        years = sorted(df_filtered[year_col].dropna().unique().astype(int))
        yr_range = st.sidebar.select_slider("IDŐSZAK", options=years, value=(min(years), max(years)))
        df_filtered = df_filtered[(df_filtered[year_col] >= yr_range[0]) & (df_filtered[year_col] <= yr_range[1])]

    # Ország szűrő
    if country_col in df_filtered.columns:
        countries = sorted(df_filtered[country_col].dropna().unique())
        sel_countries = st.sidebar.multiselect("ORSZÁG", countries)
        if sel_countries:
            df_filtered = df_filtered[df_filtered[country_col].isin(sel_countries)]

    # --- 4. Főoldal megjelenítése ---
    st.title("Global Drone Terrorism Database")
    
    # KPI adatok (ikonok nélkül)
    m1, m2, m3 = st.columns(3)
    m1.metric("ÖSSZES INCIDENS", len(df_filtered))
    m2.metric("ORSZÁGOK", df_filtered[country_col].nunique() if country_col in df_filtered.columns else "N/A")
    f_sum = int(pd.to_numeric(df_filtered[fatal_col], errors='coerce').sum()) if fatal_col in df_filtered.columns else 0
    m3.metric("ÁLDOZATOK", f"{f_sum} fő")

    st.markdown("---")

    # TÉRKÉP
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
            zoom=1.5, height=650, mapbox_style="carto-darkmatter"
        )
        fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_map, use_container_width=True)

    # ANALITIKA ÉS EXPORT (Itt kaptak helyet a gombok a sáv helyett)
    t1, t2 = st.tabs(["STATISZTIKA", "ADATOK ÉS EXPORT"])
    
    with t1:
        if year_col in df_filtered.columns:
            trend = df_filtered.groupby(year_col).size().reset_index(name='esemény')
            st.plotly_chart(px.line(trend, x=year_col, y='esemény', template="plotly_dark"), use_container_width=True)

    with t2:
        st.dataframe(df_filtered, use_container_width=True)
        # Itt vannak a gombok lejjebb hozva
        csv = df_filtered.to_csv(index=False).encode('utf-8')
        st.download_button("Adatok letöltése (CSV)", csv, "gdtd_export.csv", "text/csv")

else:
    st.error("Adatforrás nem található.")

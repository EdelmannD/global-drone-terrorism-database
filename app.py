import streamlit as st
import pandas as pd
import plotly.express as px
import io

# --- 1. Konfiguráció ---
st.set_page_config(page_title="GDTD Pro Dashboard", page_icon="🛸", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #121417; color: #FFFFFF; }
    [data-testid="stSidebar"] { background-color: #1a1d21; border-right: 1px solid #333; }
    [data-testid="stMetric"] {
        background-color: #1e2124;
        padding: 20px;
        border-radius: 10px;
        border-bottom: 4px solid #FF8C00;
    }
    [data-testid="stMetricLabel"] { color: #00FF41 !important; font-weight: bold; }
    .stTabs [aria-selected="true"] { color: #00FF41 !important; border-bottom-color: #00FF41 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. Adatbetöltés és Tisztítás ---
@st.cache_data
def load_data():
    filename = "Acled_GTD_Drone_Database_20260429.csv"
    try:
        # Próbáljuk meg kitalálni a szeparátort és kezelni az encodingot
        df = pd.read_csv(filename, sep=None, engine='python', encoding='utf-8-sig')
        
        # KRITIKUS LÉPÉS: Oszlopnevek megtisztítása a láthatatlan karakterektől
        df.columns = df.columns.str.strip().str.lower()
        
        return df
    except Exception as e:
        st.error(f"Hiba az adatok beolvasásakor: {e}")
        return pd.DataFrame()

df_raw = load_data()

if not df_raw.empty:
    # --- Rugalmas Oszlop Detektálás (KeyError kivédése) ---
    def get_col(options, default):
        for opt in options:
            if opt in df_raw.columns:
                return opt
        return default

    # Megkeressük a tényleges oszlopneveket (kisbetűsítve)
    year_col = get_col(['year', 'iyear', 'év'], 'year')
    lat_col = get_col(['latitude', 'lat'], 'latitude')
    lon_col = get_col(['longitude', 'lon', 'lng'], 'longitude')
    country_col = get_col(['country_txt', 'country', 'ország'], 'country_txt')
    fatal_col = get_col(['nkill', 'fatalities', 'fatal'], 'nkill')
    group_col = get_col(['gname', 'group_name', 'elkövető'], 'gname')
    source_col = get_col(['adatforras', 'source', 'dbsource'], 'adatforras')

    # --- 3. Szűrés (Hibatűrő módon) ---
    st.sidebar.title("🛸 SZŰRŐK")
    
    # Csak akkor szűrünk évre, ha tényleg megvan az oszlop
    if year_col in df_raw.columns:
        years = sorted(df_raw[year_col].dropna().unique().astype(int))
        yr_range = st.sidebar.select_slider("IDŐSZAK", options=years, value=(min(years), max(years)))
        df = df_raw[(df_raw[year_col] >= yr_range[0]) & (df_raw[year_col] <= yr_range[1])]
    else:
        st.error(f"Hiba: Nem találom az év oszlopot! Elérhető: {list(df_raw.columns)}")
        df = df_raw

    if country_col in df.columns:
        countries = sorted(df[country_col].dropna().unique())
        sel = st.sidebar.multiselect("ORSZÁGOK", countries)
        if sel:
            df = df[df[country_col].isin(sel)]

    # --- 4. Dashboard Megjelenítés ---
    st.title("🛸 Global Drone Terrorism Database")
    
    m1, m2, m3 = st.columns(3)
    m1.metric("INCIDENSEK", len(df))
    m2.metric("ORSZÁGOK", df[country_col].nunique() if country_col in df.columns else "N/A")
    f_sum = int(pd.to_numeric(df[fatal_col], errors='coerce').sum()) if fatal_col in df.columns else 0
    m3.metric("ÁLDOZATOK", f"{f_sum} fő")

    # --- TÉRKÉP ---
    st.subheader("📍 Globális Hotspotok")
    if lat_col in df.columns and lon_col in df.columns:
        df[lat_col] = pd.to_numeric(df[lat_col], errors='coerce')
        df[lon_col] = pd.to_numeric(df[lon_col], errors='coerce')
        df_map = df.dropna(subset=[lat_col, lon_col])

        fig_map = px.scatter_mapbox(
            df_map, lat=lat_col, lon=lon_col, 
            size=pd.to_numeric(df_map[fatal_col], errors='coerce').fillna(0) + 3 if fatal_col in df.columns else None,
            color=source_col if source_col in df.columns else None,
            color_discrete_map={'GTD': '#FF8C00', 'ACLED': '#00FF41'},
            hover_name=country_col if country_col in df.columns else None,
            zoom=1.2, height=650, mapbox_style="carto-darkmatter"
        )
        fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_map, use_container_width=True)
    else:
        st.warning("A koordináta oszlopok nem találhatók.")

    # --- Trendek és Export ---
    tab1, tab2 = st.tabs(["📊 TRENDEK", "📥 EXPORT"])
    with tab1:
        if year_col in df.columns:
            trend = df.groupby(year_col).size().reset_index(name='count')
            st.plotly_chart(px.line(trend, x=year_col, y='count', color_discrete_sequence=['#00FF41']).update_layout(template="plotly_dark"), use_container_width=True)

    with tab2:
        st.dataframe(df)
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 CSV Letöltése", csv, "gdtd_data.csv", "text/csv")
        
        try:
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine='xlsxwriter') as wr:
                df.to_excel(wr, index=False)
            st.download_button("📊 Excel Letöltése", buf.getvalue(), "gdtd_data.xlsx")
        except:
            st.info("Excel exportáláshoz 'xlsxwriter' telepítése szükséges.")

else:
    st.error("Nincs beolvasható adat!")

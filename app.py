import streamlit as st
import pandas as pd
import plotly.express as px
import io

# --- 1. Konfiguráció és Publikáció-stílusú Design ---
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
        box-shadow: 0px 10px 20px rgba(0,0,0,0.4);
    }
    [data-testid="stMetricValue"] { color: #FFFFFF !important; font-size: 1.8rem !important; }
    [data-testid="stMetricLabel"] { color: #00FF41 !important; font-weight: bold; }
    .stTabs [aria-selected="true"] { color: #00FF41 !important; border-bottom-color: #00FF41 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. Adatbetöltés (Kezeli a 'sep=;' sort és a pontosvesszőt) ---
@st.cache_data
def load_data():
    filename = "Acled_GTD_Drone_Database_20260429.csv"
    try:
        # Ellenőrizzük az első sort a 'sep=' jelzés miatt
        with open(filename, 'r', encoding='utf-8-sig') as f:
            first_line = f.readline().strip()
        
        # Beolvasás: ha van sep= sor, átugorjuk, egyébként maradunk az elején
        skip = 1 if 'sep=' in first_line else 0
        df = pd.read_csv(filename, sep=';', skiprows=skip, engine='python', encoding='utf-8-sig')
        
        # Oszlopnevek tisztítása (szóközök le, kisbetű)
        df.columns = df.columns.str.strip().str.lower()
        return df
    except Exception as e:
        st.error(f"Hiba az adatok beolvasásakor: {e}")
        return pd.DataFrame()

df_raw = load_data()

if not df_raw.empty:
    # --- Rugalmas Oszlop Detektálás ---
    def get_col(options, default):
        for opt in options:
            if opt in df_raw.columns:
                return opt
        return default

    # Oszlopok megfeleltetése a mintád alapján
    year_col = get_col(['year', 'iyear'], 'year')
    lat_col = get_col(['latitude', 'lat'], 'latitude')
    lon_col = get_col(['longitude', 'lon'], 'longitude')
    country_col = get_col(['country_txt', 'country'], 'country_txt')
    fatal_col = get_col(['nkill', 'fatalities'], 'nkill')
    group_col = get_col(['gname', 'group'], 'gname')
    source_col = get_col(['adatforras', 'dbsource'], 'adatforras')

    # --- 3. Sidebar Szűrők ---
    st.sidebar.markdown("## 🛸 SZŰRŐK")
    
    # Időszak szűrő (csak ha van év oszlop)
    if year_col in df_raw.columns:
        years = sorted(df_raw[year_col].dropna().unique().astype(int))
        yr_range = st.sidebar.select_slider("IDŐSZAK", options=years, value=(min(years), max(years)))
        df = df_raw[(df_raw[year_col] >= yr_range[0]) & (df_raw[year_col] <= yr_range[1])]
    else:
        df = df_raw

    # Ország szűrő
    if country_col in df.columns:
        countries = sorted(df[country_col].dropna().unique())
        selected_countries = st.sidebar.multiselect("ORSZÁG KIVÁLASZTÁSA", countries)
        if selected_countries:
            df = df[df[country_col].isin(selected_countries)]

    # --- 4. KPI Szekció ---
    st.title("🛸 Global Drone Terrorism Database")
    k1, k2, k3 = st.columns(3)
    k1.metric("ÖSSZES INCIDENS", f"{len(df)} db")
    k2.metric("ÉRINTETT ORSZÁGOK", f"{df[country_col].nunique() if country_col in df.columns else 'N/A'} ország")
    
    # Áldozatok összege (biztonságos konverzióval)
    f_sum = 0
    if fatal_col in df.columns:
        f_sum = int(pd.to_numeric(df[fatal_col], errors='coerce').sum())
    k3.metric("ÖSSZES ÁLDOZAT", f"{f_sum} fő")

    st.markdown("---")

    # --- 5. TÉRKÉP (A Dashboard lelke) ---
    st.subheader("📍 Globális Hotspot Térkép")
    
    if lat_col in df.columns and lon_col in df.columns:
        # Koordináták számmá alakítása (hibás sorok eldobása)
        df[lat_col] = pd.to_numeric(df[lat_col], errors='coerce')
        df[lon_col] = pd.to_numeric(df[lon_col], errors='coerce')
        df_map = df.dropna(subset=[lat_col, lon_col])

        if not df_map.empty:
            fig_map = px.scatter_mapbox(
                df_map, 
                lat=lat_col, 
                lon=lon_col, 
                size=pd.to_numeric(df_map[fatal_col], errors='coerce').fillna(0) + 3 if fatal_col in df_map.columns else None,
                color=source_col if source_col in df_map.columns else None,
                color_discrete_map={'GTD': '#FF8C00', 'ACLED': '#00FF41'},
                hover_name=country_col if country_col in df_map.columns else None,
                hover_data={year_col: True, fatal_col: True},
                zoom=1.5, 
                height=700,
                mapbox_style="carto-darkmatter"
            )
            fig_map.update_layout(
                margin={"r":0,"t":0,"l":0,"b":0},
                paper_bgcolor='rgba(0,0,0,0)',
                legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01, font=dict(color="white"))
            )
            st.plotly_chart(fig_map, use_container_width=True)
        else:
            st.warning("Nincs érvényes koordináta a szűrt adatokban!")
    else:
        st.error(f"Nem találom a koordináta oszlopokat! Elérhető: {list(df_raw.columns)}")

    # --- 6. Analitika és Export ---
    tab1, tab2 = st.tabs(["📊 ANALITIKA", "📥 EXPORT"])

    with tab1:
        col_a, col_b = st.columns(2)
        with col_a:
            if year_col in df.columns:
                st.subheader("Időbeli trend")
                trend = df.groupby(year_col).size().reset_index(name='esemény')
                fig_l = px.line(trend, x=year_col, y='esemény', color_discrete_sequence=['#00FF41'])
                fig_l.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_l, use_container_width=True)
        with col_b:
            if group_col in df.columns:
                st.subheader("Top 10 Elkövető Csoport")
                top10 = df[group_col].value_counts().head(10).reset_index()
                fig_b = px.bar(top10, x='count', y=group_col, orientation='h',
                                 color='count', color_continuous_scale=['#FF8C00', '#00FF41'])
                fig_b.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_b, use_container_width=True)

    with tab2:
        st.subheader("Adattábla és Letöltés")
        st.dataframe(df, use_container_width=True)
        
        csv_data = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Adatok Mentése (CSV)", csv_data, "gdtd_export.csv", "text/csv")

else:
    st.info("Kérlek, ellenőrizd a CSV fájl elérhetőségét!")

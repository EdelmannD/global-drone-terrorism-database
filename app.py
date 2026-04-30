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

# --- 2. Adatbetöltés ---
@st.cache_data
def load_data():
    filename = "Acled_GTD_Drone_Database_20260429.csv"
    try:
        # A fájlstruktúrád alapján betöltjük
        df = pd.read_csv(filename, sep=None, engine='python', encoding='utf-8-sig')
        # Oszlopnevek tisztítása
        df.columns = [str(c).strip().lower() for c in df.columns]
        return df
    except Exception as e:
        st.error(f"Hiba az adatok beolvasásakor: {e}")
        return pd.DataFrame()

df_raw = load_data()

if not df_raw.empty:
    # --- Oszlopok fixálása a beküldött minta alapján ---
    # Szélesség/Hosszúság a mintádból: latitude, longitude
    lat_col = 'latitude'
    lon_col = 'longitude'
    year_col = 'year'
    country_col = 'country_txt'
    fatal_col = 'nkill'
    group_col = 'gname'
    source_col = 'adatforras' # Ez az oszlop tartalmazza a GTD/ACLED értéket

    # --- Sidebar Szűrők ---
    st.sidebar.markdown("## 🛸 SZŰRŐK")
    
    # Időszak
    years = sorted(df_raw[year_col].dropna().unique().astype(int))
    yr_range = st.sidebar.select_slider("IDŐSZAK", options=years, value=(min(years), max(years)))
    df = df_raw[(df_raw[year_col] >= yr_range[0]) & (df_raw[year_col] <= yr_range[1])]

    # Ország
    countries = sorted(df[country_col].dropna().unique())
    selected_countries = st.sidebar.multiselect("ORSZÁG KIVÁLASZTÁSA", countries)
    if selected_countries:
        df = df[df[country_col].isin(selected_countries)]

    # --- KPI Szekció ---
    st.title("🛸 Global Drone Terrorism Database")
    k1, k2, k3 = st.columns(3)
    k1.metric("ÖSSZES INCIDENS", f"{len(df)} db")
    k2.metric("ÉRINTETT ORSZÁGOK", f"{df[country_col].nunique()} ország")
    f_sum = int(pd.to_numeric(df[fatal_col], errors='coerce').sum())
    k3.metric("ÖSSZES ÁLDOZAT", f"{f_sum} fő")

    st.markdown("---")

    # --- TÉRKÉP ELŐRE ---
    st.subheader("📍 Globális Hotspot Térkép")
    
    # Koordináták számmá alakítása és NaN szűrése a térképhez
    df[lat_col] = pd.to_numeric(df[lat_col], errors='coerce')
    df[lon_col] = pd.to_numeric(df[lon_col], errors='coerce')
    df_map = df.dropna(subset=[lat_col, lon_col])

    if not df_map.empty:
        fig_map = px.scatter_mapbox(
            df_map, 
            lat=lat_col, 
            lon=lon_col, 
            # Pontméret az áldozatok (nkill) alapján
            size=pd.to_numeric(df_map[fatal_col], errors='coerce').fillna(0) + 3,
            # Szín az adatforras alapján (GTD=Narancs, ACLED=Zöld)
            color=source_col if source_col in df_map.columns else None,
            color_discrete_map={'GTD': '#FF8C00', 'ACLED': '#00FF41'},
            hover_name=country_col,
            hover_data={lat_col:False, lon_col:False, year_col:True, fatal_col:True},
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
        st.warning("Nincs megjeleníthető koordináta a szűrt adatokban!")

    # --- Analitika és Export ---
    tab1, tab2 = st.tabs(["📊 ANALITIKA", "📥 EXPORT"])

    with tab1:
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Időbeli trend")
            trend = df.groupby(year_col).size().reset_index(name='esemény')
            fig_l = px.line(trend, x=year_col, y='esemény', color_discrete_sequence=['#00FF41'])
            fig_l.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_l, use_container_width=True)
        with c2:
            st.subheader("Top 10 Elkövető")
            top10 = df[group_col].value_counts().head(10).reset_index()
            fig_b = px.bar(top10, x='count', y=group_col, orientation='h',
                             color='count', color_continuous_scale=['#FF8C00', '#00FF41'])
            fig_b.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_b, use_container_width=True)

    with tab2:
        st.subheader("Adatok letöltése")
        st.dataframe(df, use_container_width=True)
        
        btn1, btn2 = st.columns(2)
        with btn1:
            st.download_button("📥 CSV Mentése", df.to_csv(index=False).encode('utf-8'), "gdtd_data.csv", "text/csv")
        with btn2:
            try:
                buf = io.BytesIO()
                with pd.ExcelWriter(buf, engine='xlsxwriter') as wr:
                    df.to_excel(wr, index=False)
                st.download_button("📊 Excel Mentése", buf.getvalue(), "gdtd_data.xlsx")
            except:
                st.info("Excel exportáláshoz 'xlsxwriter' szükséges.")
else:
    st.error("A fájl betöltése sikertelen!")

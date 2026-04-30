import streamlit as st
import pandas as pd
import plotly.express as px
import io

# --- 1. Konfiguráció és "Cyber/Neon Dark" Stílus ---
st.set_page_config(
    page_title="GDTD Pro Dashboard", 
    page_icon="🛸", 
    layout="wide"
)

# Egyedi CSS a publikáció stílusában: antracit háttér, neon kiemelések
st.markdown("""
    <style>
    /* Fő háttér antracit */
    .stApp { background-color: #121417; color: #FFFFFF; }
    
    /* Sidebar sötétebb szürke */
    [data-testid="stSidebar"] { background-color: #1e2124; border-right: 1px solid #333; }
    
    /* Metric kártyák design */
    [data-testid="stMetric"] {
        background-color: #1e2124;
        padding: 20px;
        border-radius: 10px;
        border-bottom: 3px solid #FF8C00; /* Neon narancs alsó szegély */
        box-shadow: 0px 4px 10px rgba(0,0,0,0.3);
    }
    
    /* Fehér szövegek a kártyákon */
    [data-testid="stMetricValue"] { color: #FFFFFF !important; font-family: 'Courier New', monospace; }
    [data-testid="stMetricLabel"] { color: #00FF41 !important; } /* Neon zöld címke */
    
    /* Tab és gomb stílusok */
    .stTabs [data-baseweb="tab-list"] { background-color: transparent; }
    .stTabs [data-baseweb="tab"] { color: #FFFFFF; }
    .stTabs [aria-selected="true"] { color: #00FF41 !important; border-bottom-color: #00FF41 !important; }
    
    h1, h2, h3 { color: #FFFFFF !important; text-transform: uppercase; letter-spacing: 2px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. Adatbetöltés ---
@st.cache_data
def load_data():
    filename = "Acled_GTD_Drone_Database_20260429.csv"
    try:
        # Automatikus szeparátor és encoding felismerés
        df = pd.read_csv(filename, sep=None, engine='python', encoding='utf-8-sig')
        df.columns = [str(c).strip().lower() for c in df.columns]
        
        # Alapértelmezett oszlopnevek szinkronizálása (GTD standard iyear -> year)
        if 'iyear' in df.columns: df = df.rename(columns={'iyear': 'year'})
        if 'country_txt' in df.columns: df = df.rename(columns={'country_txt': 'country'})
        
        return df
    except Exception as e:
        st.error(f"Hiba a fájl beolvasásakor: {e}")
        return pd.DataFrame()

df = load_data()

# --- 3. Logika és Szűrés ---
if not df.empty:
    # Oszlopkeresők
    year_col = next((c for c in df.columns if 'year' in c), None)
    country_col = next((c for c in df.columns if 'country' in c), None)
    lat_col = next((c for c in df.columns if 'lat' in c), None)
    lon_col = next((c for c in df.columns if 'lon' in c), None)
    fatal_col = next((c for c in df.columns if any(x in c for x in ['nkill', 'fatal'])), None)
    group_col = next((c for c in df.columns if any(x in c for x in ['gname', 'group', 'actor'])), None)
    source_col = next((c for c in df.columns if 'source' in c or 'database' in c), None)

    # Sidebar
    st.sidebar.title("🛸 GDTD FILTERS")
    
    if year_col:
        years = sorted(df[year_col].dropna().unique().astype(int))
        yr_range = st.sidebar.select_slider("IDŐSZAK", options=years, value=(min(years), max(years)))
        df = df[(df[year_col] >= yr_range[0]) & (df[year_col] <= yr_range[1])]

    if country_col:
        countries = sorted(df[country_col].dropna().unique())
        sel_countries = st.sidebar.multiselect("ORSZÁGOK", countries)
        if sel_countries:
            df = df[df[country_col].isin(sel_countries)]

    # --- 4. Dashboard Felület ---
    st.title("🛸 Global Drone Terrorism Database")
    st.markdown(f"**Vizualizációs profil:** Neon Orange (GTD) | Neon Green (ACLED)")

    # KPI Szekció
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("ÖSSZES INCIDENS", f"{len(df)}")
    
    c_num = df[country_col].nunique() if country_col else 0
    k2.metric("ORSZÁGOK SZÁMA", f"{c_num}")
    
    f_val = int(pd.to_numeric(df[fatal_col], errors='coerce').sum()) if fatal_col else 0
    k3.metric("ÁLDOZATOK SZÁMA", f"{f_val}")
    
    k4.metric("MAX ÉV", f"{df[year_col].max() if year_col else 'N/A'}")

    st.write("---")

    tab1, tab2, tab3 = st.tabs(["📊 ANALITIKA", "🗺️ HOTSPOT TÉRKÉP", "📥 EXPORT"])

    with tab1:
        c1, c2 = st.columns(2)
        
        with c1:
            st.subheader("IDŐBELI TREND")
            # Megpróbáljuk szétválasztani forrás szerint, ha van ilyen oszlop
            if year_col:
                if source_col:
                    trend_data = df.groupby([year_col, source_col]).size().reset_index(name='count')
                    fig_line = px.line(trend_data, x=year_col, y='count', color=source_col,
                                       color_discrete_map={'GTD': '#FF8C00', 'ACLED': '#00FF41'})
                else:
                    trend_data = df.groupby(year_col).size().reset_index(name='count')
                    fig_line = px.area(trend_data, x=year_col, y='count', color_discrete_sequence=['#00FF41'])
                
                fig_line.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_line, use_container_width=True)

        with c2:
            st.subheader("TOP 10 CSOPORT")
            if group_col:
                top10 = df[group_col].value_counts().head(10).reset_index()
                top10.columns = ['Csoport', 'Esemény']
                fig_bar = px.bar(top10, x='Esemény', y='Csoport', orientation='h',
                                 color='Esemény', color_continuous_scale=['#FF8C00', '#00FF41'])
                fig_bar.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_bar, use_container_width=True)

    with tab2:
        st.subheader("INCIDENSEK GEOGRÁFIAI ELOSZLÁSA")
        if lat_col and lon_col:
            # A publikáció stílusú térkép: méret az áldozatok szerint
            fig_map = px.scatter_mapbox(
                df, lat=lat_col, lon=lon_col, 
                size=df[fatal_col].fillna(1) if fatal_col else None,
                color=source_col if source_col else None,
                color_discrete_map={'GTD': '#FF8C00', 'ACLED': '#00FF41'},
                hover_name=country_col,
                zoom=1.5, height=700,
                mapbox_style="carto-darkmatter"
            )
            fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_map, use_container_width=True)

    with tab3:
        st.subheader("ADATOK EXPORTÁLÁSA")
        st.dataframe(df, use_container_width=True)
        
        d_col1, d_col2 = st.columns(2)
        
        with d_col1:
            csv_data = df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Letöltés: CSV", data=csv_data, file_name="gdtd_data.csv", mime="text/csv", use_container_width=True)
            
        with d_col2:
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Data')
            st.download_button("📊 Letöltés: Excel (XLSX)", data=output.getvalue(), file_name="gdtd_data.xlsx", 
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)

else:
    st.error("⚠️ Nem található adat. Ellenőrizd a CSV fájlt a mappa gyökerében!")

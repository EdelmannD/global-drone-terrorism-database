import streamlit as st
import pandas as pd
import plotly.express as px
import io

# --- 1. Konfiguráció és Publikáció-stílusú Design ---
st.set_page_config(
    page_title="GDTD Pro Dashboard", 
    page_icon="🛸", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Egyedi CSS: Antracit háttér, neon narancs (GTD) és neon zöld (ACLED) színek
st.markdown("""
    <style>
    /* Fő háttér és szöveg */
    .stApp { background-color: #121417; color: #FFFFFF; }
    
    /* Oldalsáv sötétítése */
    [data-testid="stSidebar"] { background-color: #1a1d21; border-right: 1px solid #333; }
    
    /* Metric (KPI) kártyák: neon narancs alsó csíkkal */
    [data-testid="stMetric"] {
        background-color: #1e2124;
        padding: 20px;
        border-radius: 10px;
        border-bottom: 4px solid #FF8C00;
        box-shadow: 0px 10px 20px rgba(0,0,0,0.4);
    }
    
    /* Feliratok színei */
    [data-testid="stMetricValue"] { color: #FFFFFF !important; font-size: 1.8rem !important; }
    [data-testid="stMetricLabel"] { color: #00FF41 !important; font-weight: bold; }
    
    /* Tabok (Fülek) stílusa */
    .stTabs [data-baseweb="tab-list"] { background-color: transparent; gap: 10px; }
    .stTabs [data-baseweb="tab"] { 
        height: 50px; 
        background-color: #1e2124; 
        border-radius: 5px 5px 0 0; 
        color: white;
    }
    .stTabs [aria-selected="true"] { border-bottom: 3px solid #00FF41 !important; color: #00FF41 !important; }
    
    hr { border: 1px solid #333; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. Robusztus Adatbetöltés ---
@st.cache_data
def load_data():
    # A megadott fájlnév használata
    filename = "Acled_GTD_Drone_Database_20260429.csv"
    try:
        # Automatikus szeparátor és kódolás kezelése
        df = pd.read_csv(filename, sep=None, engine='python', encoding='utf-8-sig')
        
        # Oszlopnevek egységesítése (kisbetű, szóközmentes)
        df.columns = [str(c).strip().lower() for c in df.columns]
        
        # GTD specifikus oszlopok átnevezése a könnyebb kezelhetőségért
        rename_map = {
            'iyear': 'year',
            'country_txt': 'country',
            'nkill': 'fatalities',
            'gname': 'group_name'
        }
        df = df.rename(columns=rename_map)
        return df
    except Exception as e:
        st.error(f"Hiba az adatok beolvasásakor: {e}")
        return pd.DataFrame()

df_raw = load_data()

# --- 3. Dashboard Logika ---
if not df_raw.empty:
    # Intelligens oszlopkeresés (ha az átnevezés nem talált volna mindent)
    year_col = next((c for c in df_raw.columns if 'year' in c), None)
    country_col = next((c for c in df_raw.columns if 'country' in c), None)
    lat_col = next((c for c in df_raw.columns if 'lat' in c), None)
    lon_col = next((c for c in df_raw.columns if 'lon' in c), None)
    fatal_col = next((c for c in df_raw.columns if any(x in c for x in ['fatal', 'nkill', 'death'])), None)
    group_col = next((c for c in df_raw.columns if any(x in c for x in ['group', 'actor', 'gname'])), None)
    source_col = next((c for c in df_raw.columns if any(x in c for x in ['source', 'database', 'event_type'])), None)

    # --- Sidebar Szűrők ---
    st.sidebar.markdown("## 🛸 SZŰRŐK")
    
    # Időszak csúszka
    if year_col:
        years = sorted(df_raw[year_col].dropna().unique().astype(int))
        yr_range = st.sidebar.select_slider("IDŐSZAK", options=years, value=(min(years), max(years)))
        df = df_raw[(df_raw[year_col] >= yr_range[0]) & (df_raw[year_col] <= yr_range[1])]
    else:
        df = df_raw

    # Ország multiselect
    if country_col:
        countries = sorted(df[country_col].dropna().unique())
        selected = st.sidebar.multiselect("ORSZÁG KIVÁLASZTÁSA", countries)
        if selected:
            df = df[df[country_col].isin(selected)]

    # --- Főoldal KPI ---
    st.title("🛸 Global Drone Terrorism Database")
    st.markdown("---")
    
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("ÖSSZES INCIDENS", f"{len(df)} db")
    
    c_count = df[country_col].nunique() if country_col else 0
    k2.metric("ÉRINTETT ORSZÁGOK", f"{c_count}")
    
    f_sum = int(pd.to_numeric(df[fatal_col], errors='coerce').sum()) if fatal_col else 0
    k3.metric("ÁLDOZATOK SZÁMA", f"{f_sum} fő")
    
    max_year = df[year_col].max() if year_col else "N/A"
    k4.metric("UTOLSÓ ADAT", f"{max_year}")

    # --- Vizualizációs fülek ---
    tab1, tab2, tab3 = st.tabs(["📊 ANALITIKA", "🗺️ HOTSPOT TÉRKÉP", "📥 EXPORT"])

    with tab1:
        col_a, col_b = st.columns(2)
        
        with col_a:
            st.subheader("IDŐBELI TRENDEK")
            if year_col:
                # Publikáció stílus: ha van forrás, bontsuk szét (GTD vs ACLED színekkel)
                if source_col:
                    trend = df.groupby([year_col, source_col]).size().reset_index(name='db')
                    fig_line = px.line(trend, x=year_col, y='db', color=source_col,
                                       color_discrete_map={'GTD': '#FF8C00', 'ACLED': '#00FF41'})
                else:
                    trend = df.groupby(year_col).size().reset_index(name='db')
                    fig_line = px.area(trend, x=year_col, y='db', color_discrete_sequence=['#00FF41'])
                
                fig_line.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_line, use_container_width=True)

        with col_b:
            st.subheader("TOP 10 ELKÖVETŐ CSOPORT")
            if group_col:
                top10 = df[group_col].value_counts().head(10).reset_index()
                top10.columns = ['Csoport', 'Események']
                fig_bar = px.bar(top10, x='Események', y='Csoport', orientation='h',
                                 color='Események', color_continuous_scale=['#FF8C00', '#00FF41'])
                fig_bar.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig_bar, use_container_width=True)

    with tab2:
        st.subheader("GLOBÁLIS INCIDENS TÉRKÉP")
        if lat_col and lon_col:
            # Méret az áldozatok szerint, szín a forrás szerint
            fig_map = px.scatter_mapbox(
                df, lat=lat_col, lon=lon_col, 
                size=pd.to_numeric(df[fatal_col], errors='coerce').fillna(1) + 1 if fatal_col else None,
                color=source_col if source_col else None,
                color_discrete_map={'GTD': '#FF8C00', 'ACLED': '#00FF41'},
                hover_name=country_col,
                zoom=1.5, height=700,
                mapbox_style="carto-darkmatter"
            )
            fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_map, use_container_width=True)
        else:
            st.warning("A koordináták nem találhatók a térkép megjelenítéséhez.")

    with tab3:
        st.subheader("ADATOK LETÖLTÉSE")
        st.dataframe(df, use_container_width=True)
        
        d_col1, d_col2 = st.columns(2)
        
        with d_col1:
            csv_data = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Letöltés: CSV",
                data=csv_data,
                file_name="gdtd_export.csv",
                mime="text/csv",
                use_container_width=True
            )
            
        with d_col2:
            try:
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                    df.to_excel(writer, index=False, sheet_name='GDTD_Filtered')
                
                st.download_button(
                    label="📊 Letöltés: EXCEL (XLSX)",
                    data=buffer.getvalue(),
                    file_name="gdtd_export.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            except ImportError:
                st.error("Az Excel letöltéshez telepítsd az 'xlsxwriter' csomagot!")

else:
    st.error("A rendszer nem talált adatot. Ellenőrizd a CSV fájl elérhetőségét!")

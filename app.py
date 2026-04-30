import streamlit as st
import pandas as pd
import plotly.express as px
import io

# --- 1. Konfiguráció és Design ---
st.set_page_config(
    page_title="GDTD Pro Dashboard", 
    page_icon="🛸", 
    layout="wide"
)

# Egyedi Neon-Antracit stílus
st.markdown("""
    <style>
    .stApp { background-color: #121417; color: #FFFFFF; }
    [data-testid="stSidebar"] { background-color: #1a1d21; border-right: 1px solid #333; }
    
    /* KPI kártyák neon narancs szegéllyel */
    [data-testid="stMetric"] {
        background-color: #1e2124;
        padding: 20px;
        border-radius: 10px;
        border-bottom: 4px solid #FF8C00;
        box-shadow: 0px 10px 20px rgba(0,0,0,0.4);
    }
    [data-testid="stMetricValue"] { color: #FFFFFF !important; }
    [data-testid="stMetricLabel"] { color: #00FF41 !important; }
    
    /* Tabok stílusa */
    .stTabs [aria-selected="true"] { color: #00FF41 !important; border-bottom-color: #00FF41 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. Adatbetöltés ---
@st.cache_data
def load_data():
    filename = "Acled_GTD_Drone_Database_20260429.csv"
    try:
        df = pd.read_csv(filename, sep=None, engine='python', encoding='utf-8-sig')
        df.columns = [str(c).strip().lower() for c in df.columns]
        # Alapértelmezett oszlopnevek szinkronizálása
        rename_map = {'iyear': 'year', 'country_txt': 'country', 'nkill': 'fatalities', 'gname': 'group_name'}
        df = df.rename(columns=rename_map)
        return df
    except Exception as e:
        st.error(f"Hiba az adatok beolvasásakor: {e}")
        return pd.DataFrame()

df_raw = load_data()

# --- 3. Dashboard Funkcionalitás ---
if not df_raw.empty:
    # Oszlopok beazonosítása
    year_col = next((c for c in df_raw.columns if 'year' in c), None)
    country_col = next((c for c in df_raw.columns if 'country' in c), None)
    lat_col = next((c for c in df_raw.columns if 'lat' in c), None)
    lon_col = next((c for c in df_raw.columns if 'lon' in c), None)
    fatal_col = next((c for c in df_raw.columns if any(x in c for x in ['fatal', 'nkill'])), None)
    source_col = next((c for c in df_raw.columns if any(x in c for x in ['source', 'database'])), None)
    group_col = next((c for c in df_raw.columns if any(x in c for x in ['group', 'actor', 'gname'])), None)

    # Sidebar szűrők
    st.sidebar.title("🛸 SZŰRŐK")
    if year_col:
        years = sorted(df_raw[year_col].dropna().unique().astype(int))
        yr_range = st.sidebar.select_slider("IDŐSZAK", options=years, value=(min(years), max(years)))
        df = df_raw[(df_raw[year_col] >= yr_range[0]) & (df_raw[year_col] <= yr_range[1])]
    else:
        df = df_raw

    if country_col:
        countries = sorted(df[country_col].dropna().unique())
        selected = st.sidebar.multiselect("ORSZÁGOK", countries)
        if selected:
            df = df[df[country_col].isin(selected)]

    # --- Főoldal ---
    st.title("🛸 Global Drone Terrorism Database")
    
    # KPI Szekció
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("ÖSSZES INCIDENS", len(df))
    k2.metric("ORSZÁGOK", df[country_col].nunique() if country_col else 0)
    f_val = int(pd.to_numeric(df[fatal_col], errors='coerce').sum()) if fatal_col else 0
    k3.metric("ÁLDOZATOK", f_val)
    k4.metric("UTOLSÓ ÉV", df[year_col].max() if year_col else "N/A")

    st.markdown("---")

    # --- Térkép és Analitika (Sorrend megfordítva) ---
    tab1, tab2, tab3 = st.tabs(["🗺️ GLOBÁLIS HOTSPOT TÉRKÉP", "📊 RÉSZLETES ANALITIKA", "📥 ADATOK ÉS EXPORT"])

    with tab1:
        st.subheader("Incidensek földrajzi eloszlása")
        if lat_col and lon_col:
            # A körök mérete az áldozatok számától függ, a színe a forrástól (GTD/ACLED)
            fig_map = px.scatter_mapbox(
                df, 
                lat=lat_col, 
                lon=lon_col, 
                size=pd.to_numeric(df[fatal_col], errors='coerce').fillna(1) + 2 if fatal_col else None,
                color=source_col if source_col else None,
                color_discrete_map={'GTD': '#FF8C00', 'ACLED': '#00FF41'},
                hover_name=country_col,
                hover_data=[year_col] if year_col else None,
                zoom=1.8, 
                height=750,
                mapbox_style="carto-darkmatter"
            )
            fig_map.update_layout(
                margin={"r":0,"t":0,"l":0,"b":0},
                paper_bgcolor='rgba(0,0,0,0)',
                legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01, font=dict(color="white"))
            )
            st.plotly_chart(fig_map, use_container_width=True)
        else:
            st.error("Koordináta oszlopok nem találhatók a CSV-ben!")

    with tab2:
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Időbeli lefutás")
            if year_col:
                trend = df.groupby(year_col).size().reset_index(name='db')
                fig_line = px.line(trend, x=year_col, y='db', color_discrete_sequence=['#00FF41'])
                fig_line.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_line, use_container_width=True)

        with c2:
            st.subheader("Top 10 Elkövető")
            if group_col:
                top_g = df[group_col].value_counts().head(10).reset_index()
                fig_bar = px.bar(top_g, x='count', y=group_col, orientation='h',
                                 color='count', color_continuous_scale=['#FF8C00', '#00FF41'])
                fig_bar.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_bar, use_container_width=True)

    with tab3:
        st.subheader("Szűrt adathalmaz")
        st.dataframe(df, use_container_width=True)
        
        ex1, ex2 = st.columns(2)
        with ex1:
            st.download_button("📥 CSV Letöltése", df.to_csv(index=False).encode('utf-8'), "gdtd_data.csv", "text/csv")
        with ex2:
            try:
                buf = io.BytesIO()
                with pd.ExcelWriter(buf, engine='xlsxwriter') as wr:
                    df.to_excel(wr, index=False)
                st.download_button("📊 Excel Letöltése", buf.getvalue(), "gdtd_data.xlsx")
            except:
                st.warning("Excel exportáláshoz 'xlsxwriter' telepítése szükséges.")

else:
    st.error("Nincs megjeleníthető adat. Ellenőrizd a CSV fájlt!")

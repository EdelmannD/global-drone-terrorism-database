import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Oldal beállítása
st.set_page_config(
    page_title="GDTD Dashboard", 
    page_icon="🛸", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. UI Javítás: Világos feliratok sötét háttéren
st.markdown("""
    <style>
    /* Fő háttér */
    .main { background-color: #0e1117; }
    
    /* Metrika kártyák stílusa */
    [data-testid="stMetric"] {
        background-color: #1f2937;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #374151;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    /* Feliratok színeinek kényszerítése */
    [data-testid="stMetricLabel"] {
        color: #9ca3af !important; /* Világosszürke címke */
        font-size: 1rem !important;
    }
    [data-testid="stMetricValue"] {
        color: #ffffff !important; /* Hófehér érték */
        font-weight: bold !important;
    }
    
    /* Sidebar szövegek */
    .css-1d391kg { color: #ffffff; }
    </style>
    """, unsafe_allow_html=True)

st.title("🛸 Global Drone Terrorism Database (GDTD)")
st.markdown("---")

# 3. Adatbetöltő függvény (Sep=, hiba kezelésével)
@st.cache_data
def load_data():
    filename = "Acled_GTD_Drone_Database_20260429.csv"
    
    # Első sor ellenőrzése a "sep=" metaadat miatt
    with open(filename, 'r', encoding='utf-8-sig') as f:
        first_line = f.readline().strip()
    
    skip = 1 if "sep=" in first_line else 0
    
    df = pd.read_csv(
        filename, 
        skiprows=skip, 
        sep=None, 
        engine='python', 
        encoding='utf-8-sig',
        on_bad_lines='skip'
    )

    # Tisztítás
    df.columns = [str(c).strip().lower() for c in df.columns]
    df = df.loc[:, ~df.columns.str.contains('^unnamed')]
    return df

# 4. Logika és Megjelenítés
try:
    df = load_data()

    # Oszlopok beazonosítása
    year_col = next((c for c in df.columns if 'year' in c or 'év' in c), None)
    lat_col = next((c for c in df.columns if 'lat' in c or 'szélesség' in c), None)
    lon_col = next((c for c in df.columns if 'lon' in c or 'hosszúság' in c), None)
    country_col = next((c for c in df.columns if 'country' in c or 'ország' in c), None)
    fatalities_col = next((c for c in df.columns if 'fatal' in c or 'kill' in c or 'halott' in c), None)

    if year_col:
        # --- SIDEBAR ---
        st.sidebar.header("🛸 Szűrők")
        min_y, max_y = int(df[year_col].min()), int(df[year_col].max())
        year_range = st.sidebar.slider("Időszak", min_y, max_y, (min_y, max_y))

        # Szűrés
        filtered_df = df[(df[year_col] >= year_range[0]) & (df[year_col] <= year_range[1])]
        
        if country_col:
            countries = sorted(filtered_df[country_col].dropna().unique())
            selected_countries = st.sidebar.multiselect("Ország szűrés", countries)
            if selected_countries:
                filtered_df = filtered_df[filtered_df[country_col].isin(selected_countries)]

        # --- KPI KÁRTYÁK ---
        m1, m2, m3 = st.columns(3)
        m1.metric("Összes incidens", f"{len(filtered_df)} db")
        
        counts = filtered_df[country_col].nunique() if country_col else 0
        m2.metric("Érintett országok", f"{counts} ország")
        
        fats = int(filtered_df[fatalities_col].sum()) if fatalities_col else 0
        m3.metric("Összes áldozat", f"{fats} fő")

        st.markdown("<br>", unsafe_allow_html=True)

        # --- GRAFIKONOK ---
        col_left, col_right = st.columns([2, 1])

        with col_left:
            st.subheader("📍 Földrajzi eloszlás")
            if lat_col and lon_col:
                fig_map = px.scatter_mapbox(
                    filtered_df, lat=lat_col, lon=lon_col, 
                    hover_name=country_col if country_col else None,
                    color_discrete_sequence=["#ff4b4b"], zoom=1.2, height=500
                )
                fig_map.update_layout(
                    mapbox_style="carto-darkmatter", 
                    margin={"r":0,"t":0,"l":0,"b":0},
                    paper_bgcolor="rgba(0,0,0,0)"
                )
                st.plotly_chart(fig_map, use_container_width=True)

        with col_right:
            st.subheader("📈 Időbeli trend")
            trend = filtered_df.groupby(year_col).size().reset_index(name='n')
            fig_line = px.line(trend, x=year_col, y='n', template="plotly_dark")
            fig_line.update_traces(line_color='#ff4b4b', line_width=3)
            fig_line.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_line, use_container_width=True)

        # Top országok
        if country_col:
            st.subheader("🌍 Legérintettebb területek")
            top10 = filtered_df[country_col].value_counts().head(10).reset_index()
            top10.columns = ['Ország', 'Események']
            fig_bar = px.bar(top10, x='Ország', y='Események', color='Események', 
                             color_continuous_scale='Reds', template="plotly_dark")
            st.plotly_chart(fig_bar, use_container_width=True)

    else:
        st.error("Nem található 'Year' oszlop az adatokban.")

except Exception as e:
    st.error(f"Hiba történt az adatok betöltésekor: {e}")

# Adatok táblázata
if 'df' in locals() and st.checkbox("Nyers adatok megtekintése"):
    st.dataframe(df)

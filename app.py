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

# 2. UI Stílus: Világos feliratok sötét háttéren
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    [data-testid="stMetric"] {
        background-color: #1f2937;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #374151;
    }
    [data-testid="stMetricLabel"] { color: #9ca3af !important; font-size: 1rem !important; }
    [data-testid="stMetricValue"] { color: #ffffff !important; font-weight: bold !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("🛸 Global Drone Terrorism Database (GDTD)")
st.markdown("---")

# 3. Adatbetöltő függvény
@st.cache_data
def load_data():
    filename = "Acled_GTD_Drone_Database_20260429.csv"
    
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

    # Oszlopnevek tisztítása (kisbetű, szóközmentes)
    df.columns = [str(c).strip().lower() for c in df.columns]
    df = df.loc[:, ~df.columns.str.contains('^unnamed')]
    
    return df

try:
    df = load_data()

    # --- CÉLZOTT OSZLOPKERESÉS ---
    # Elsőnek a 'country_txt'-t keressük, mert abban vannak a nevek
    country_col = next((c for c in df.columns if c == 'country_txt'), 
                  next((c for c in df.columns if 'country' in c and df[c].dtype == 'object'), None))
    
    year_col = next((c for c in df.columns if 'year' in c or 'iyear' in c), None)
    lat_col = next((c for c in df.columns if 'lat' in c or 'latitude' in c), None)
    lon_col = next((c for c in df.columns if 'lon' in c or 'longitude' in c), None)
    fatalities_col = next((c for c in df.columns if 'nkill' in c or 'fatal' in c), None)

    if year_col:
        # --- SZŰRŐK ---
        st.sidebar.header("🛸 Szűrők")
        
        min_y, max_y = int(df[year_col].min()), int(df[year_col].max())
        year_range = st.sidebar.slider("Időszak", min_y, max_y, (min_y, max_y))
        filtered_df = df[(df[year_col] >= year_range[0]) & (df[year_col] <= year_range[1])]
        
        if country_col:
            # Szigorú szűrés: csak szöveges értékek, üresek nélkül
            countries = sorted(filtered_df[country_col].dropna().astype(str).unique().tolist())
            selected_countries = st.sidebar.multiselect("Országok kiválasztása", countries)
            if selected_countries:
                filtered_df = filtered_df[filtered_df[country_col].isin(selected_countries)]

        # --- KPI ---
        m1, m2, m3 = st.columns(3)
        m1.metric("Összes incidens", f"{len(filtered_df)} db")
        
        c_count = filtered_df[country_col].nunique() if country_col else 0
        m2.metric("Érintett országok", f"{c_count} ország")
        
        f_sum = int(pd.to_numeric(filtered_df[fatalities_col], errors='coerce').sum()) if fatalities_col else 0
        m3.metric("Összes áldozat", f"{f_sum} fő")

        st.markdown("<br>", unsafe_allow_html=True)

        # --- VIZUALIZÁCIÓK ---
        c1, c2 = st.columns([2, 1])

        with c1:
            st.subheader("📍 Földrajzi eloszlás")
            if lat_col and lon_col:
                fig_map = px.scatter_mapbox(
                    filtered_df, lat=lat_col, lon=lon_col, 
                    hover_name=country_col if country_col else None,
                    color_discrete_sequence=["#ff4b4b"], zoom=1.5, height=500
                )
                fig_map.update_layout(mapbox_style="carto-darkmatter", margin={"r":0,"t":0,"l":0,"b":0}, paper_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig_map, use_container_width=True)

        with c2:
            st.subheader("📈 Időbeli trend")
            trend = filtered_df.groupby(year_col).size().reset_index(name='n')
            fig_line = px.line(trend, x=year_col, y='n', template="plotly_dark")
            fig_line.update_traces(line_color='#ff4b4b', line_width=3)
            st.plotly_chart(fig_line, use_container_width=True)

        if country_col:
            st.subheader("🌍 Legérintettebb területek (Top 10)")
            top10 = filtered_df[country_col].value_counts().head(10).reset_index()
            top10.columns = ['Ország', 'Események']
            fig_bar = px.bar(top10, x='Ország', y='Események', color='Események', color_continuous_scale='Reds', template="plotly_dark")
            st.plotly_chart(fig_bar, use_container_width=True)

    else:
        st.error("Hiba: Nem találom az év oszlopot.")

except Exception as e:
    st.error(f"Hiba történt: {e}")

# Ellenőrzés gomb
if st.checkbox("Adatszerkezet ellenőrzése"):
    st.write(f"Használt ország oszlop: `{country_col}`")
    st.dataframe(df.head(20))

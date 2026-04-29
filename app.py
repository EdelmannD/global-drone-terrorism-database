import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Oldal beállítása
st.set_page_config(
    page_title="GDTD - Global Drone Terrorism Database", 
    page_icon="🛸", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Egyedi stílus (Sötét módhoz illő színek)
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1f2937; padding: 15px; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🛸 Global Drone Terrorism Database (GDTD)")
st.markdown("---")

# 2. Adatbetöltő függvény (Hibajavított verzió)
@st.cache_data
def load_data():
    filename = "Acled_GTD_Drone_Database_20260429.csv"
    
    # Először megnézzük az első sort, hogy van-e benne "sep=" metaadat
    with open(filename, 'r', encoding='utf-8-sig') as f:
        first_line = f.readline().strip()
    
    # Ha az első sor a "sep=," jelzést tartalmazza, akkor a másodiktól kezdjük az olvasást
    skip = 0
    if "sep=" in first_line:
        skip = 1
        # Ha a sep= után meg van adva a karakter, azt is kinyerhetjük (opcionális)
        detected_sep = first_line.split('=')[-1] if '=' in first_line else ','
    else:
        detected_sep = None # hagyjuk a pandas-ra a felismerést

    # Adat beolvasása
    df = pd.read_csv(
        filename, 
        skiprows=skip, 
        sep=detected_sep if detected_sep else None, 
        engine='python', 
        encoding='utf-8-sig',
        on_bad_lines='skip'
    )

    # Oszlopnevek tisztítása: kisbetű, szóközmentesítés
    df.columns = [str(c).strip().lower() for c in df.columns]
    
    # Unnamed oszlopok eltávolítása
    df = df.loc[:, ~df.columns.str.contains('^unnamed')]
    
    return df

# 3. Adatok feldolgozása
try:
    df = load_data()

    # Intelligens oszlopkeresés (ha a név nem pontosan egyezik)
    year_col = next((c for c in df.columns if 'year' in c or 'év' in c), None)
    lat_col = next((c for c in df.columns if 'lat' in c or 'szélesség' in c), None)
    lon_col = next((c for c in df.columns if 'lon' in c or 'hosszúság' in c), None)
    country_col = next((c for c in df.columns if 'country' in c or 'ország' in c), None)
    fatalities_col = next((c for c in df.columns if 'fatal' in c or 'kill' in c or 'halott' in c), None)

    if year_col:
        # --- OLDALSÁV (SZŰRŐK) ---
        st.sidebar.header("🛸 Szűrőbeállítások")
        
        # Év szűrő
        min_y, max_y = int(df[year_col].min()), int(df[year_col].max())
        year_range = st.sidebar.slider("Időszak (Év)", min_y, max_y, (min_y, max_y))

        # Ország szűrő (ha van ilyen oszlop)
        selected_countries = []
        if country_col:
            countries = sorted(df[country_col].dropna().unique())
            selected_countries = st.sidebar.multiselect("Országok kiválasztása", countries)

        # Adat szűrése
        filtered_df = df[(df[year_col] >= year_range[0]) & (df[year_col] <= year_range[1])]
        if selected_countries:
            filtered_df = filtered_df[filtered_df[country_col].isin(selected_countries)]

        # --- FŐPANEL (METRIKÁK) ---
        m1, m2, m3 = st.columns(3)
        m1.metric("Összes incidens", f"{len(filtered_df)} db")
        
        affected_countries = filtered_df[country_col].nunique() if country_col else "N/A"
        m2.metric("Érintett országok", f"{affected_countries} ország")
        
        if fatalities_col:
            total_fatalities = int(filtered_df[fatalities_col].sum())
            m3.metric("Összes áldozat", f"{total_fatalities} fő")
        else:
            m3.metric("Összes áldozat", "Nincs adat")

        st.write("") # Térköz

        # --- VIZUALIZÁCIÓK ---
        col_left, col_right = st.columns([2, 1])

        with col_left:
            if lat_col and lon_col:
                st.subheader("📍 Földrajzi eloszlás")
                fig_map = px.scatter_mapbox(
                    filtered_df, 
                    lat=lat_col, lon=lon_col, 
                    hover_name=country_col if country_col else None,
                    hover_data=[year_col] if year_col else None,
                    color_discrete_sequence=["#ff4b4b"], 
                    zoom=1.2, 
                    height=500
                )
                fig_map.update_layout(
                    mapbox_style="carto-darkmatter", 
                    margin={"r":0,"t":0,"l":0,"b":0},
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)"
                )
                st.plotly_chart(fig_map, use_container_width=True)
            else:
                st.warning("Koordináták nem találhatók a térképhez.")

        with col_right:
            st.subheader("📈 Időbeli trend")
            trend_data = filtered_df.groupby(year_col).size().reset_index(name='incidents')
            fig_trend = px.line(
                trend_data, x=year_col, y='incidents',
                labels={year_col: "Év", "incidents": "Események"},
                template="plotly_dark"
            )
            fig_trend.update_traces(line_color='#ff4b4b', line_width=3)
            st.plotly_chart(fig_trend, use_container_width=True)

        # --- ALSÓ SZEKCIÓ ---
        if country_col:
            st.subheader("🌍 Leginkább érintett országok (Top 10)")
            top_countries = filtered_df[country_col].value_counts().head(10).reset_index()
            top_countries.columns = ['Ország', 'Események']
            fig_bar = px.bar(
                top_countries, x='Ország', y='Események',
                color='Események', color_continuous_scale='Reds',
                template="plotly_dark"
            )
            st.plotly_chart(fig_bar, use_container_width=True)

    else:
        st.error(f"Hiba: Nem találom az év oszlopot! Elérhető oszlopok: {', '.join(df.columns)}")

except FileNotFoundError:
    st.error("Hiba: Az 'Acled_GTD_Drone_Database_20260429.csv' fájl nem található. Kérlek, töltsd fel a GitHub repóba!")
except Exception as e:
    st.error(f"Váratlan hiba történt: {e}")

# Nyers adatok megjelenítése
if 'df' in locals() and st.checkbox("Nyers adatok táblázatos mutatása"):
    st.dataframe(df)

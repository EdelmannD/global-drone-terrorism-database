import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="GDTD Dashboard", page_icon="🛸", layout="wide")

st.title("🛸 Global Drone Terrorism Database (GDTD)")

@st.cache_data
def load_data():
    # Atombiztos beolvasás: sep=None és engine='python' automatikusan felismeri az elválasztót (vessző vagy pontosvessző)
    df = pd.read_csv("Acled_GTD_Drone_Database_20260429.csv", sep=None, engine='python', encoding='utf-8-sig')
    
    # Oszlopnevek tisztítása: kisbetű + szóközmentesítés
    df.columns = [str(c).strip().lower() for c in df.columns]
    return df

try:
    df = load_data()
    
    # Debug: Ha még mindig baj van, kiírjuk mi van a motorháztető alatt (később törölhető)
    # st.write("Detected columns:", list(df.columns))

    # Megkeressük az oszlopokat, akkor is ha picit más a nevük
    year_col = next((c for c in df.columns if 'year' in c), None)
    lat_col = next((c for c in df.columns if 'lat' in c), None)
    lon_col = next((c for c in df.columns if 'lon' in c), None)
    country_col = next((c for c in df.columns if 'country' in c), None)

    if year_col:
        st.sidebar.header("Szűrők")
        min_y, max_y = int(df[year_col].min()), int(df[year_col].max())
        year_range = st.sidebar.slider("Évek kiválasztása", min_y, max_y, (min_y, max_y))

        filtered_df = df[(df[year_col] >= year_range[0]) & (df[year_col] <= year_range[1])]
        
        c1, c2 = st.columns(2)
        c1.metric("Összes incidens", len(filtered_df))
        c2.metric("Érintett országok", filtered_df[country_col].nunique() if country_col else "N/A")

        if lat_col and lon_col:
            st.subheader("Földrajzi eloszlás")
            fig = px.scatter_mapbox(filtered_df, 
                                    lat=lat_col, lon=lon_col, 
                                    hover_name=country_col if country_col else None,
                                    color_discrete_sequence=["red"], 
                                    zoom=1, height=600)
            fig.update_layout(mapbox_style="open-street-map", margin={"r":0,"t":0,"l":0,"b":0})
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.error(f"Hiba: Nem találom az év oszlopot! Elérhető oszlopok: {', '.join(df.columns)}")

except Exception as e:
    st.error(f"Váratlan hiba történt: {e}")

if st.checkbox("Nyers adatok mutatása"):
    st.write(df.head(20))

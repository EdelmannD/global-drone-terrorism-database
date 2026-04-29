import streamlit as st
import pandas as pd
import plotly.express as px

# Oldal címe és ikonja
st.set_page_config(page_title="GDTD Dashboard", page_icon="🛸", layout="wide")

st.title("🛸 Global Drone Terrorism Database (GDTD)")
st.markdown("Interactive analysis of drone-related incidents (1994-2024)")

# Adatok betöltése (a te CSV-d neve legyen itt!)
@st.cache_data
def load_data():
    df = pd.read_csv("Acled_GTD_Drone_Database_20260429.csv", sep=";")
    return df

df = load_data()

# Oldalsávos szűrők
st.sidebar.header("Filters")
year_range = st.sidebar.slider("Select Year Range", 
                               int(df['year'].min()), 
                               int(df['year'].max()), 
                               (2015, 2024))

# Adatok szűrése
filtered_df = df[(df['year'] >= year_range[0]) & (df['year'] <= year_range[1])]

# Fő mutatók (Metrics)
col1, col2 = st.columns(2)
col1.metric("Total Incidents", len(filtered_df))
col2.metric("Countries Affected", filtered_df['country'].nunique())

# TÉRKÉP - Ez lesz a leglátványosabb
st.subheader("Geographical Distribution")
fig = px.scatter_mapbox(filtered_df, 
                        lat="latitude", lon="longitude", 
                        hover_name="event_type", 
                        hover_data=["country", "year"],
                        color_discrete_sequence=["red"], 
                        zoom=1, height=500)

fig.update_layout(mapbox_style="open-street-map")
fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
st.plotly_chart(fig, use_container_width=True)

# Adattáblázat megtekintése
if st.checkbox("Show raw data"):
    st.write(filtered_df)

import streamlit as st
import pandas as pd
import plotly.express as px

# --- 1. Page Config & Professional Styling ---
st.set_page_config(page_title="GDTD Dashboard", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    .stApp { background-color: #121417; color: #E0E0E0; }
    [data-testid="stSidebar"] { background-color: #1a1d21; border-right: 1px solid #333; }
    
    /* Fehér stílusú csúszka és UI */
    div[data-baseweb="slider"] > div > div { background-color: #444444 !important; } 
    div[data-baseweb="slider"] [role="slider"] { background-color: #FFFFFF !important; border: 1px solid #FFFFFF !important; }
    div[data-testid="stThumbValue"] { color: #FFFFFF !important; }
    span[data-baseweb="tag"] { background-color: #FFFFFF !important; color: #000 !important; }

    .main-title {
        font-size: 2.5rem;
        font-weight: bold;
        line-height: 1.1;
        color: #FFFFFF;
        margin-bottom: 25px;
    }

    /* Metric kártyák balra */
    [data-testid="stMetric"] {
        background-color: #1e2124;
        padding: 15px;
        border-radius: 4px;
        border-left: 4px solid #FFFFFF;
        margin-bottom: 15px;
    }
    [data-testid="stMetricLabel"] { color: #999999 !important; font-size: 0.9rem !important; }
    [data-testid="stMetricValue"] { color: #FFFFFF !important; font-size: 1.8rem !important; }

    /* Grafikon keret: fehér háttér a fekete grafikonoknak */
    .chart-box {
        background-color: #FFFFFF;
        padding: 10px;
        border: 2px solid #000000;
        border-radius: 5px;
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. Data Loading ---
@st.cache_data
def load_data():
    filename = "Acled_GTD_Drone_Database_20260429.csv"
    try:
        # A 'sep=;' sor miatt skiprows=1, és kényszerítjük a pontos szeparátort
        df = pd.read_csv(filename, sep=';', skiprows=1, engine='python', encoding='utf-8-sig')
        df.columns = df.columns.str.strip().str.lower()
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()

df_raw = load_data()

if not df_raw.empty:
    # Oszlop azonosítók a mintád alapján
    lat_col, lon_col = 'latitude', 'longitude'
    year_col, country_col = 'year', 'country_txt'
    fatal_col, source_col = 'nkill', 'adatforras'
    group_col, type_col = 'gname', 'attacktype1_txt'

    # --- 3. Sidebar ---
    with st.sidebar:
        st.markdown("### FILTERS")
        sources = sorted(df_raw[source_col].dropna().unique())
        selected_sources = st.multiselect("Data Source", sources, default=sources)
        df_filtered = df_raw[df_raw[source_col].isin(selected_sources)]

        years = sorted(df_filtered[year_col].dropna().unique().astype(int))
        yr_range = st.select_slider("Period", options=years, value=(min(years), max(years)))
        df_filtered = df_filtered[(df_filtered[year_col] >= yr_range[0]) & (df_filtered[year_col] <= yr_range[1])]

    # --- 4. Main Layout (Metricák balra, Térkép jobbra) ---
    col_left, col_right = st.columns([1, 3.5])

    with col_left:
        st.markdown('<p class="main-title">Global Drone<br>Terrorism Database</p>', unsafe_allow_html=True)
        st.metric("INCIDENTS", len(df_filtered))
        st.metric("COUNTRIES", df_filtered[country_col].nunique())
        f_val = pd.to_numeric(df_filtered[fatal_col], errors='coerce').sum()
        st.metric("FATALITIES", int(f_val))

    with col_right:
        df_filtered[lat_col] = pd.to_numeric(df_filtered[lat_col], errors='coerce')
        df_filtered[lon_col] = pd.to_numeric(df_filtered[lon_col], errors='coerce')
        df_map = df_filtered.dropna(subset=[lat_col, lon_col])
        
        fig_map = px.scatter_mapbox(
            df_map, lat=lat_col, lon=lon_col, 
            size=pd.to_numeric(df_map[fatal_col], errors='coerce').fillna(0) + 3,
            color=source_col,
            color_discrete_sequence=['#FF8C00', '#00FF41'],
            hover_name=group_col,
            zoom=1.5, height=580, mapbox_style="carto-darkmatter"
        )
        fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, showlegend=True, 
                          legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01, font=dict(color="white")))
        st.plotly_chart(fig_map, use_container_width=True)

    # --- 5. Statistics (2x2 elrendezés, fekete grafikonok fehér keretben) ---
    st.markdown("---")
    
    def apply_style(fig):
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
            font_color='black', margin=dict(l=10, r=10, t=40, b=10),
            xaxis=dict(showgrid=False, linecolor='black', tickfont=dict(size=10)),
            yaxis=dict(showgrid=False, linecolor='black', tickfont=dict(size=10)),
            title_font=dict(size=14, color='black')
        )
        fig.update_xaxes(automargin=True)
        fig.update_yaxes(automargin=True)
        return fig

    r1c1, r1c2 = st.columns(2)
    r2c1, r2c2 = st.columns(2)

    with r1c1:
        st.markdown('<div class="chart-box">', unsafe_allow_html=True)
        trend = df_filtered.groupby(year_col).size().reset_index(name='count')
        fig1 = px.line(trend, x=year_col, y='count', title="Trend over Years", markers=True)
        fig1.update_traces(line_color='black', marker=dict(color='black', size=4))
        st.plotly_chart(apply_style(fig1), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with r1c2:
        st.markdown('<div class="chart-box">', unsafe_allow_html=True)
        top_groups = df_filtered[group_col].value_counts().head(7).reset_index()
        # Sortörés: <br> beillesztése 20 karakterenként
        top_groups[group_col] = top_groups[group_col].str.wrap(20).replace('\n', '<br>', regex=True)
        fig2 = px.bar(top_groups, x='count', y=group_col, orientation='h', title="Most Active Groups")
        fig2.update_traces(marker_color='black')
        st.plotly_chart(apply_style(fig2), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with r2c1:
        st.markdown('<div class="chart-box">', unsafe_allow_html=True)
        types = df_filtered[type_col].value_counts().head(7).reset_index()
        types[type_col] = types[type_col].str.wrap(20).replace('\n', '<br>', regex=True)
        fig3 = px.bar(types, x=type_col, y='count', title="Top Attack Types")
        fig3.update_traces(marker_color='black')
        st.plotly_chart(apply_style(fig3), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with r2c2:
        st.markdown('<div class="chart-box">', unsafe_allow_html=True)
        targets = df_filtered['targtype1_txt'].value_counts().head(7).reset_index()
        targets['targtype1_txt'] = targets['targtype1_txt'].str.wrap(20).replace('\n', '<br>', regex=True)
        fig4 = px.bar(targets, x='count', y='targtype1_txt', orientation='h', title="Target Types")
        fig4.update_traces(marker_color='white', marker_line_color='black', marker_line_width=1.5)
        st.plotly_chart(apply_style(fig4), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

else:
    st.warning("Please ensure the CSV file is in the same directory.")

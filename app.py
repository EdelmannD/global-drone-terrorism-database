import streamlit as st
import pandas as pd
import plotly.express as px

# --- 1. Page Config & Professional Styling ---
st.set_page_config(page_title="GDTD Dashboard", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    .stApp { background-color: #121417; color: #E0E0E0; }
    [data-testid="stSidebar"] { background-color: #1a1d21; border-right: 1px solid #333; }
    
    .small-citation {
        font-size: 0.7rem;
        color: #999999;
        line-height: 1.3;
        margin-bottom: 20px;
    }
    
    [data-testid="stSidebar"] label, 
    [data-testid="stSidebar"] .stMarkdown h3 { 
        color: #CCCCCC !important; 
        font-weight: normal !important;
        text-transform: uppercase;
        font-size: 0.85rem !important;
    }

    /* Slider és UI elemek fehérre állítása */
    div[data-baseweb="slider"] > div > div { background-color: #444444 !important; } 
    div[data-baseweb="slider"] [role="slider"] { background-color: #FFFFFF !important; border: 1px solid #FFFFFF !important; }
    div[data-testid="stThumbValue"] { color: #FFFFFF !important; }
    span[data-baseweb="tag"] { background-color: #FFFFFF !important; color: #000 !important; }

    .main-title {
        font-size: 2.5rem;
        font-weight: bold;
        line-height: 1.1;
        color: #FFFFFF;
        margin-top: 5px;
        margin-bottom: 20px;
    }

    [data-testid="stMetric"] {
        background-color: #1e2124;
        padding: 10px 15px;
        border-radius: 4px;
        border-left: 3px solid #FFFFFF;
        margin-bottom: 10px;
        width: 100%;
    }
    [data-testid="stMetricLabel"] { color: #999999 !important; font-size: 0.8rem !important; }
    [data-testid="stMetricValue"] { color: #FFFFFF !important; font-size: 1.5rem !important; }

    /* Grafikon konténer fehér háttérrel a fekete grafikonokhoz */
    .chart-container {
        background-color: #FFFFFF;
        padding: 15px;
        border-radius: 8px;
        border: 2px solid #000000;
        margin-bottom: 20px;
    }
    
    header[data-testid="stHeader"] { background-color: rgba(0,0,0,0) !important; }
    .block-container { padding-top: 1.5rem; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. Data Loading ---
@st.cache_data
def load_data():
    filename = "Acled_GTD_Drone_Database_20260429.csv"
    try:
        df = pd.read_csv(filename, sep=';', skiprows=0, engine='python', encoding='utf-8-sig')
        df.columns = df.columns.str.strip().str.lower()
        if 'adatforras' in df.columns:
            df.rename(columns={'adatforras': 'data_source'}, inplace=True)
        return df
    except Exception:
        return pd.DataFrame()

df_raw = load_data()

if not df_raw.empty:
    lat_col, lon_col = 'latitude', 'longitude'
    year_col, country_col = 'year', 'country_txt'
    fatal_col, source_col = 'nkill', 'data_source'
    group_col, type_col = 'gname', 'attacktype1_txt'

    # --- 3. Sidebar ---
    with st.sidebar:
        st.markdown(f"""
        <div class="small-citation">
        DOI: <a href="https://doi.org/10.6084/m9.figshare.21381312" style="color:#FFFFFF;">10.6084/m9.figshare.21381312</a>
        </div>
        """, unsafe_allow_html=True)
        
        sources = sorted(df_raw[source_col].unique()) if source_col in df_raw.columns else []
        selected_sources = st.multiselect("Data Source", sources, default=sources)
        df_filtered = df_raw[df_raw[source_col].isin(selected_sources)]

        if year_col in df_filtered.columns:
            years = sorted(df_filtered[year_col].dropna().unique().astype(int))
            yr_range = st.select_slider("Time Period", options=years, value=(min(years), max(years)))
            df_filtered = df_filtered[(df_filtered[year_col] >= yr_range[0]) & (df_filtered[year_col] <= yr_range[1])]

    # --- 4. Main Layout ---
    col_left, col_right = st.columns([1, 4])
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
            color_discrete_map={'GTD': '#FF8C00', 'ACLED': '#00FF41'},
            zoom=1.2, height=550, mapbox_style="carto-darkmatter"
        )
        fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
        st.plotly_chart(fig_map, use_container_width=True)

    # --- 6. Analytics Section (2x2 Grid, Black & White Style) ---
    st.markdown("### STATISTICS")
    
    # Közös stílus beállítás a grafikonokhoz
    def update_fig_style(fig):
        fig.update_layout(
            plot_bgcolor='white',
            paper_bgcolor='white',
            font_color='black',
            margin=dict(l=40, r=20, t=40, b=60),
            xaxis=dict(showgrid=False, linecolor='black', title_font=dict(size=10)),
            yaxis=dict(showgrid=False, linecolor='black', title_font=dict(size=10)),
            showlegend=False
        )
        # Sortörés kezelése a tengelyeken
        fig.update_xaxes(tickangle=0, automargin=True)
        fig.update_yaxes(automargin=True)
        return fig

    row1_col1, row1_col2 = st.columns(2)
    row2_col1, row2_col2 = st.columns(2)

    with row1_col1:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        trend = df_filtered.groupby(year_col).size().reset_index(name='count')
        fig1 = px.line(trend, x=year_col, y='count', title="Incidents over Time", markers=True)
        fig1.update_traces(line_color='black', marker=dict(color='black', size=6))
        st.plotly_chart(update_fig_style(fig1), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with row1_col2:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        top_groups = df_filtered[group_col].value_counts().head(8).reset_index()
        # Sortörés szimulálása: minden második szóköznél törjön meg a név
        top_groups[group_col] = top_groups[group_col].str.wrap(15).replace('\n', '<br>', regex=True)
        fig2 = px.bar(top_groups, x='count', y=group_col, orientation='h', title="Top Groups")
        fig2.update_traces(marker_color='white', marker_line_color='black', marker_line_width=1.5)
        st.plotly_chart(update_fig_style(fig2), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with row2_col1:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        types = df_filtered[type_col].value_counts().head(8).reset_index()
        types[type_col] = types[type_col].str.wrap(15).replace('\n', '<br>', regex=True)
        fig3 = px.bar(types, x=type_col, y='count', title="Attack Types")
        fig3.update_traces(marker_color='black')
        st.plotly_chart(update_fig_style(fig3), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with row2_col2:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        # Új grafikon: Fatalities vs Incidents (Scatter) vagy Adatforrás megoszlás
        src_dist = df_filtered[source_col].value_counts().reset_index()
        fig4 = px.pie(src_dist, names=source_col, values='count', title="Data Source Distribution", hole=0.4)
        fig4.update_traces(marker=dict(colors=['black', 'grey'], line=dict(color='black', width=2)))
        fig4.update_layout(plot_bgcolor='white', paper_bgcolor='white', font_color='black', showlegend=True)
        st.plotly_chart(fig4, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with st.expander("VIEW RAW DATA"):
        st.dataframe(df_filtered, use_container_width=True)

else:
    st.info("Loading dataset...")

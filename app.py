import streamlit as st
import pandas as pd
import plotly.express as px

# --- 1. Page Config ---
st.set_page_config(page_title="GDTD Dashboard", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    /* Alap háttér és általános világos szövegek */
    .stApp { background-color: #121417; color: #F0F2F6; }
    [data-testid="stSidebar"] { background-color: #1a1d21; border-right: 1px solid #333; }
    
    /* Minden felirat és label világosítása a sötét szürke helyett */
    p, span, label, div, h1, h2, h3, .stMetric label, [data-testid="stMarkdownContainer"] p, 
    .stMultiSelect label, .stSlider label { 
        color: #F0F2F6 !important; 
    } 

    /* Sidebar Citation stílus */
    .sidebar-cite {
        font-size: 0.85rem !important;
        background-color: #262730;
        padding: 10px;
        border-radius: 5px;
        border: 1px solid #4B4B4B;
        margin-bottom: 20px;
    }
    .sidebar-cite a { color: #00FF41 !important; text-decoration: none; }

    /* Cím stílus */
    .main-title {
        font-size: 1.6rem !important;
        font-weight: 800;
        color: #FFFFFF !important;
        line-height: 1.0;
        margin-top: -10px;
        margin-bottom: 0;
    }

    /* Metric kártyák - Beljebb húzva */
    [data-testid="stMetric"] {
        background-color: #1e2124;
        padding: 5px 12px;
        border-radius: 4px;
        border-left: 3px solid #FFFFFF;
        margin-top: -10px;
    }
    
    [data-testid="stMetricValue"] {
        color: #FFFFFF !important;
        font-size: 1.8rem !important;
    }

    .block-container { padding-top: 1rem !important; padding-bottom: 0rem !important; }
    hr { margin-top: 0.5rem !important; margin-bottom: 0.5rem !important; }

    /* Chart konténer */
    .chart-container {
        background-color: #FFFFFF;
        padding: 15px;
        border-radius: 4px;
        border: 1px solid #000000;
        margin-bottom: 20px;
    }
    
    header[data-testid="stHeader"] { background-color: rgba(0,0,0,0) !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. Data Loading ---
@st.cache_data
def load_data():
    filename = "Acled_GTD_Drone_Database_20260429.csv"
    try:
        with open(filename, 'r', encoding='utf-8-sig') as f:
            first_line = f.readline()
        skip = 1 if "sep=" in first_line else 0
        df = pd.read_csv(filename, sep=';', skiprows=skip, engine='python', encoding='utf-8-sig')
        df.columns = df.columns.str.strip().str.lower()
        if 'adatforras' in df.columns:
            df.rename(columns={'adatforras': 'data_source'}, inplace=True)
        return df
    except:
        return pd.DataFrame()

df_raw = load_data()

if not df_raw.empty:
    lat_col, lon_col = 'latitude', 'longitude'
    year_col, country_col = 'year', 'country_txt'
    fatal_col, source_col = 'nkill', 'data_source'
    group_col, type_col = 'gname', 'attacktype1_txt'

    # --- 3. Sidebar Filters & Citation ---
    with st.sidebar:
        # CITATION A SIDEBAR TETEJÉN
        st.markdown(f"""
        <div class="sidebar-cite">
        <b>Cite as:</b><br>
        Besenyő, J.; Edelmann, D. (2026): Global Drone Terrorism Database (GDTD). Figshare. <br>
        <a href="https://doi.org/10.6084/m9.figshare.32128399" target="_blank">DOI: 110.6084/m9.figshare.32128399</a><br>
        License: CC BY 4.0
        </div>
        """, unsafe_allow_html=True)

        st.markdown("### Filters")
        sources = sorted(df_raw[source_col].unique()) if source_col in df_raw.columns else []
        selected_sources = st.multiselect("Data Source", sources, default=sources)
        df_filtered = df_raw[df_raw[source_col].isin(selected_sources)]

        if year_col in df_filtered.columns:
            years = sorted(df_filtered[year_col].dropna().unique().astype(int))
            yr_range = st.select_slider("Period", options=years, value=(min(years), max(years)))
            df_filtered = df_filtered[(df_filtered[year_col] >= yr_range[0]) & (df_filtered[year_col] <= yr_range[1])]

    # --- 4. Header: Title + Metrics (spacer-rel beljebb húzva) ---
    header_col1, header_col2, header_col3, header_col4, spacer = st.columns([2.5, 1, 1, 1, 0.4])
    
    with header_col1:
        st.markdown('<p class="main-title">GLOBAL DRONE<br>TERRORISM DATABASE</p>', unsafe_allow_html=True)
    
    with header_col2:
        st.metric("INCIDENTS", len(df_filtered))
    
    with header_col3:
        st.metric("COUNTRIES", df_filtered[country_col].nunique())
    
    with header_col4:
        f_val = pd.to_numeric(df_filtered[fatal_col], errors='coerce').sum()
        st.metric("FATALITIES", int(f_val if pd.notnull(f_val) else 0))

    st.markdown("---")

    # --- 5. Main Map ---
    df_filtered[lat_col] = pd.to_numeric(df_filtered[lat_col], errors='coerce')
    df_filtered[lon_col] = pd.to_numeric(df_filtered[lon_col], errors='coerce')
    df_map = df_filtered.dropna(subset=[lat_col, lon_col])
    
    fig_map = px.scatter_mapbox(
        df_map, lat=lat_col, lon=lon_col, 
        size=pd.to_numeric(df_map[fatal_col], errors='coerce').fillna(0) + 3,
        color=source_col,
        color_discrete_map={'GTD': '#FF8C00', 'ACLED': '#00FF41'},
        zoom=1.5, height=520, mapbox_style="carto-darkmatter"
    )
    fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, paper_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig_map, use_container_width=True)

    # --- 6. Statistics Grid (2x2) ---
    st.markdown("### STATISTICS")

    def apply_bw_style(fig):
        fig.update_layout(
            plot_bgcolor='white', paper_bgcolor='white', font_color='black',
            margin=dict(l=40, r=20, t=40, b=40),
            xaxis=dict(showgrid=False, linecolor='black', ticks='inside'),
            yaxis=dict(showgrid=False, linecolor='black', ticks='inside'),
            showlegend=False
        )
        return fig

    r1c1, r1c2 = st.columns(2)
    r2c1, r2c2 = st.columns(2)

    with r1c1:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        trend = df_filtered.groupby(year_col).size().reset_index(name='count')
        fig1 = px.line(trend, x=year_col, y='count', title="Trend over Time")
        fig1.update_traces(line_color='black', line_width=2)
        st.plotly_chart(apply_bw_style(fig1), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with r1c2:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        top_g = df_filtered[group_col].value_counts().head(8).reset_index()
        top_g[group_col] = top_g[group_col].astype(str).str.wrap(25).replace('\n', '<br>', regex=True)
        fig2 = px.bar(top_g, x='count', y=group_col, orientation='h', title="Top Groups")
        fig2.update_traces(marker_color='black')
        st.plotly_chart(apply_bw_style(fig2), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with r2c1:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        top_t = df_filtered[type_col].value_counts().head(8).reset_index()
        top_t[type_col] = top_t[type_col].astype(str).str.wrap(25).replace('\n', '<br>', regex=True)
        fig3 = px.bar(top_t, x=type_col, y='count', title="Attack Types")
        fig3.update_traces(marker_color='black')
        st.plotly_chart(apply_bw_style(fig3), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with r2c2:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        src = df_filtered[source_col].value_counts().reset_index()
        fig4 = px.pie(src, names=source_col, values='count', title="Data Sources", hole=0.4)
        fig4.update_traces(marker=dict(colors=['black', '#cccccc'], line=dict(color='white', width=1)))
        fig4.update_layout(paper_bgcolor='white', font_color='black', margin=dict(t=40, b=20, l=10, r=10))
        st.plotly_chart(fig4, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
else:
    st.error("Dataset error. Please check your CSV file.")

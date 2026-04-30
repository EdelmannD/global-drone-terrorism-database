import streamlit as st
import pandas as pd
import plotly.express as px

# --- 1. Page Config & Professional Styling ---
st.set_page_config(page_title="GDTD Dashboard", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    .stApp { background-color: #121417; color: #E0E0E0; }
    [data-testid="stSidebar"] { background-color: #1a1d21; border-right: 1px solid #333; }
    
    /* Fehér UI elemek */
    div[data-baseweb="slider"] > div > div { background-color: #444444 !important; } 
    div[data-baseweb="slider"] [role="slider"] { background-color: #FFFFFF !important; border: 1px solid #FFFFFF !important; }
    div[data-testid="stThumbValue"] { color: #FFFFFF !important; }
    span[data-baseweb="tag"] { background-color: #FFFFFF !important; color: #000 !important; }

    .main-title {
        font-size: 4rem !important; /* Nagyobb méret */
        font-weight: bold;
        line-height: 0.9;
        color: #FFFFFF;
        margin-bottom: 20px;
    }

    /* Metric kártyák balra igazítva */
    [data-testid="stMetric"] {
        background-color: #1e2124;
        padding: 10px 15px;
        border-radius: 4px;
        border-left: 3px solid #FFFFFF;
        margin-bottom: 10px;
        width: 100%;
    }

    /* Fehér konténer a fekete statisztikáknak */
    .chart-container {
        background-color: #FFFFFF;
        padding: 15px;
        border-radius: 4px;
        border: 2px solid #000000;
        margin-bottom: 20px;
    }
    
    header[data-testid="stHeader"] { background-color: rgba(0,0,0,0) !important; }
    .block-container { padding-top: 1.5rem; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. Data Loading (CSV specifikus kezelés) ---
@st.cache_data
def load_data():
    filename = "Acled_GTD_Drone_Database_20260429.csv"
    try:
        # Ellenőrizzük a szeparátort (sep=;)
        with open(filename, 'r', encoding='utf-8-sig') as f:
            first_line = f.readline()
        skip = 1 if "sep=" in first_line else 0
        
        df = pd.read_csv(filename, sep=';', skiprows=skip, engine='python', encoding='utf-8-sig')
        df.columns = df.columns.str.strip().str.lower()
        if 'adatforras' in df.columns:
            df.rename(columns={'adatforras': 'data_source'}, inplace=True)
        return df
    except Exception:
        return pd.DataFrame()

df_raw = load_data()

if not df_raw.empty:
    # Oszlopnevek
    lat_col, lon_col = 'latitude', 'longitude'
    year_col, country_col = 'year', 'country_txt'
    fatal_col, source_col = 'nkill', 'data_source'
    group_col, type_col = 'gname', 'attacktype1_txt'

    # --- 3. Sidebar ---
    with st.sidebar:
        st.markdown("### Filters")
        sources = sorted(df_raw[source_col].unique()) if source_col in df_raw.columns else []
        selected_sources = st.multiselect("Data Source", sources, default=sources)
        df_filtered = df_raw[df_raw[source_col].isin(selected_sources)]

        if year_col in df_filtered.columns:
            years = sorted(df_filtered[year_col].dropna().unique().astype(int))
            yr_range = st.select_slider("Period", options=years, value=(min(years), max(years)))
            df_filtered = df_filtered[(df_filtered[year_col] >= yr_range[0]) & (df_filtered[year_col] <= yr_range[1])]

    # --- 4. Layout (Bal: Metrikák, Jobb: Térkép) ---
    col_left, col_right = st.columns([1.2, 4])

    with col_left:
        st.markdown('<p class="main-title">Global Drone<br>Terrorism Database</p>', unsafe_allow_html=True)
        st.metric("INCIDENTS", len(df_filtered))
        st.metric("COUNTRIES", df_filtered[country_col].nunique())
        f_val = pd.to_numeric(df_filtered[fatal_col], errors='coerce').sum()
        st.metric("FATALITIES", int(f_val if pd.notnull(f_val) else 0))

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
        fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_map, use_container_width=True)

    # --- 5. Statistics (2x2 Grid, Fekete-Fehér) ---
    st.markdown("### STATISTICS")

    def apply_bw_style(fig):
        fig.update_layout(
            plot_bgcolor='white', paper_bgcolor='white', font_color='black',
            margin=dict(l=50, r=20, t=40, b=50),
            xaxis=dict(showgrid=False, linecolor='black', ticks='inside', tickcolor='black'),
            yaxis=dict(showgrid=False, linecolor='black', ticks='inside', tickcolor='black'),
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
        # Sortörés alkalmazása
        top_g[group_col] = top_g[group_col].astype(str).str.wrap(20).replace('\n', '<br>', regex=True)
        fig2 = px.bar(top_g, x='count', y=group_col, orientation='h', title="Top Groups")
        fig2.update_traces(marker_color='black')
        st.plotly_chart(apply_bw_style(fig2), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with r2c1:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        top_t = df_filtered[type_col].value_counts().head(8).reset_index()
        top_t[type_col] = top_t[type_col].astype(str).str.wrap(20).replace('\n', '<br>', regex=True)
        fig3 = px.bar(top_t, x=type_col, y='count', title="Attack Types")
        fig3.update_traces(marker_color='black')
        st.plotly_chart(apply_bw_style(fig3), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with r2c2:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        # Forrás megoszlás tortadiagram, de fekete kontúrral
        src = df_filtered[source_col].value_counts().reset_index()
        fig4 = px.pie(src, names=source_col, values='count', title="Data Sources", hole=0.4)
        fig4.update_traces(marker=dict(colors=['black', '#888888'], line=dict(color='white', width=2)))
        fig4.update_layout(paper_bgcolor='white', font_color='black')
        st.plotly_chart(fig4, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

else:
    st.error("Dataset not found or empty. Please check the CSV file.")

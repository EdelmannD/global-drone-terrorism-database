import streamlit as st
import pandas as pd
import plotly.express as px

# --- 1. Page Config ---
st.set_page_config(page_title="GDTD Dashboard", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    /* Streamlit alapértelmezett elemek elrejtése (fehér sáv alul és menü fent) */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    .stApp { background-color: #121417; color: #F0F2F6; }
    [data-testid="stSidebar"] { background-color: #1a1d21; border-right: 1px solid #333; }
    
    /* Elrendezés javítása */
    .block-container { 
        padding-top: 0.5rem !important; 
        padding-bottom: 2rem !important; 
    } 
    [data-testid="stVerticalBlock"] > div:first-child { margin-top: -1.5rem !important; }

    p, span, label, div, h1, h2, h3, .stMetric label, [data-testid="stMarkdownContainer"] p, 
    .stMultiSelect label, .stSlider label { 
        color: #F0F2F6 !important; 
    } 

    /* DROPDOWN JAVÍTÁSA */
    div[data-baseweb="popover"] * { color: #000000 !important; }
    div[data-baseweb="popover"] { background-color: #ffffff !important; border-radius: 4px; }
    div[role="listbox"] li { background-color: #ffffff !important; color: #000000 !important; }
    div[role="listbox"] li:hover { background-color: #eeeeee !important; }

    .sidebar-cite {
        font-size: 0.85rem !important;
        background-color: #262730;
        padding: 10px;
        border-radius: 5px;
        border: 1px solid #4B4B4B;
        margin-bottom: 20px;
    }
    .sidebar-cite a { color: #D3D3D3 !important; text-decoration: underline; }

    div[data-baseweb="select"] > div {
        background-color: #262730 !important;
        border-color: #4B4B4B !important;
    }

    div[data-baseweb="slider"] > div > div > div { background-color: #00FF41 !important; }
    div[role="slider"] { background-color: #00FF41 !important; border: 2px solid #FFFFFF !important; }
    
    span[data-baseweb="tag"] { background-color: #444 !important; color: white !important; }

    .main-title {
        font-size: 1.6rem !important;
        font-weight: 800;
        color: #FFFFFF !important;
        line-height: 1.0;
        margin-top: 0px;
        margin-bottom: 0;
    }

    [data-testid="stMetric"] {
        background-color: #1e2124;
        padding: 5px 12px;
        border-radius: 4px;
        border-left: 3px solid #FFFFFF;
    }
    
    [data-testid="stMetricValue"] { color: #FFFFFF !important; font-size: 1.8rem !important; }

    .chart-container {
        background-color: #FFFFFF;
        padding: 10px;
        border-radius: 2px;
        border: 2px solid #000000;
        margin-bottom: 20px;
    }

    .footer-note {
        font-size: 0.75rem;
        color: #888888 !important;
        margin-top: 20px;
        border-top: 1px solid #333;
        padding-top: 10px;
        padding-bottom: 10px;
    }
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
        
        def categorize_actor(name):
            name = str(name).strip()
            if name.lower() == 'unknown':
                return 'Unknown'
            elif name.lower().startswith('unidentified'):
                return 'Unidentified'
            else:
                return 'Terrorist Organization'
        
        if 'gname' in df.columns:
            df['actor_category'] = df['gname'].apply(categorize_actor)
        else:
            df['actor_category'] = 'Unknown'
            
        return df
    except:
        return pd.DataFrame()

df_raw = load_data()

if not df_raw.empty:
    lat_col, lon_col = 'latitude', 'longitude'
    year_col, country_col = 'year', 'country_txt'
    fatal_col, source_col = 'nkill', 'data_source'
    group_col, type_col = 'gname', 'attacktype1_txt'

    # --- 3. Sidebar Filters ---
    with st.sidebar:
        st.markdown(f"""
        <div class="sidebar-cite">
        <b>Cite as:</b><br>
        Besenyő, J.; Edelmann, D. (2026): Global Drone Terrorism Database (GDTD). Figshare. <br>
        <a href="https://doi.org/10.6084/m9.figshare.32128399" target="_blank">DOI: 10.6084/m9.figshare.32128399</a><br>
        License: CC BY 4.0
        </div>
        """, unsafe_allow_html=True)

        st.markdown("### Filters")
        
        if year_col in df_raw.columns:
            years = sorted(df_raw[year_col].dropna().unique().astype(int))
            if years:
                yr_range = st.select_slider("Period", options=years, value=(min(years), max(years)))
                df_filtered = df_raw[(df_raw[year_col] >= yr_range[0]) & (df_raw[year_col] <= yr_range[1])].copy()
        else:
            df_filtered = df_raw.copy()

        sources = sorted(df_filtered[source_col].unique()) if source_col in df_filtered.columns else []
        selected_sources = st.multiselect("Data Source", sources, default=sources)
        df_filtered = df_filtered[df_filtered[source_col].isin(selected_sources)]

        actor_cats = sorted(df_filtered['actor_category'].unique())
        selected_actors = st.multiselect("Actor Type", actor_cats, default=actor_cats)
        df_filtered = df_filtered[df_filtered['actor_category'].isin(selected_actors)]

        countries = sorted(df_filtered[country_col].dropna().unique()) if country_col in df_filtered.columns else []
        selected_countries = st.multiselect("Country", countries, default=countries)
        df_filtered = df_filtered[df_filtered[country_col].isin(selected_countries)]

        if type_col in df_filtered.columns:
            df_filtered[type_col] = df_filtered[type_col].fillna("N/A")
            types = sorted(df_filtered[type_col].unique())
            selected_types = st.multiselect("Attack Type", types, default=types)
            df_filtered = df_filtered[df_filtered[type_col].isin(selected_types)]

    # --- 4. Header ---
    header_col1, header_col2, header_col3, header_col4, spacer = st.columns([2.5, 1, 1, 1, 0.4])
    with header_col1:
        st.markdown('<p class="main-title">GLOBAL DRONE<br>TERRORISM DATABASE</p>', unsafe_allow_html=True)
    with header_col2:
        st.metric("INCIDENTS", len(df_filtered))
    with header_col3:
        st.metric("COUNTRIES", df_filtered[country_col].nunique() if not df_filtered.empty else 0)
    with header_col4:
        f_val = pd.to_numeric(df_filtered[fatal_col], errors='coerce').sum()
        st.metric("FATALITIES", int(f_val if pd.notnull(f_val) else 0))

    st.markdown("<hr style='margin:10px 0px'>", unsafe_allow_html=True)

    # --- 5. Main Map ---
    if not df_filtered.empty:
        df_filtered[lat_col] = pd.to_numeric(df_filtered[lat_col], errors='coerce')
        df_filtered[lon_col] = pd.to_numeric(df_filtered[lon_col], errors='coerce')
        df_filtered[fatal_col] = pd.to_numeric(df_filtered[fatal_col], errors='coerce').fillna(0)
        
        df_filtered['lethality'] = df_filtered[fatal_col].apply(lambda x: "Fatal Attack" if x > 0 else "Non-Fatal")
        df_map = df_filtered.dropna(subset=[lat_col, lon_col])
        
        fig_map = px.scatter_mapbox(
            df_map, lat=lat_col, lon=lon_col, 
            size=df_map[fatal_col] + 3,
            color='lethality',
            color_discrete_map={'Fatal Attack': '#FF8C00', 'Non-Fatal': '#00FF41'},
            zoom=1.5, height=550, mapbox_style="carto-darkmatter",
            category_orders={"lethality": ["Fatal Attack", "Non-Fatal"]},
            hover_data={lat_col:False, lon_col:False, 'lethality':True, fatal_col:True, group_col:True}
        )
        fig_map.update_layout(
            margin={"r":0,"t":0,"l":0,"b":0}, 
            paper_bgcolor='rgba(0,0,0,0)',
            legend=dict(
                title_text="",
                yanchor="top", y=0.99, xanchor="left", x=0.01,
                bgcolor="rgba(0,0,0,0.5)", font=dict(color="white")
            )
        )
        st.plotly_chart(fig_map, use_container_width=True)

        # --- 6. Statistics Grid ---
        st.markdown("### STATISTICS")

        def apply_bw_style(fig):
            fig.update_layout(
                plot_bgcolor='white', paper_bgcolor='white', 
                font=dict(family="Arial", size=11, color="black"),
                margin=dict(l=40, r=10, t=40, b=40),
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
            fig4.update_layout(paper_bgcolor='white', font=dict(family="Arial", color='black'), margin=dict(t=40, b=10))
            st.plotly_chart(fig4, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.warning("No data available for the selected filters.")

    st.markdown("""
        <div class="footer-note">
            Data sources: <br>
            START - National Consortium for the Study of Terrorism and Responses to Terrorism, Global Terrorism Database, 1970 - 2022, 2025 database, 2025. <br>
            C. Raleigh, A. Linke, H. Hegre, J. Karlsen, Introducing ACLED: An armed conflict location and event dataset, J. Peace Res. 47, 2010.
        </div>
    """, unsafe_allow_html=True)
else:
    st.error("Dataset error. Please check your CSV file.")

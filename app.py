import streamlit as st
import pandas as pd
import plotly.express as px
import io

# --- 1. Page Config ---
st.set_page_config(page_title="GDTD Dashboard", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    .stApp { background-color: #121417; color: #F0F2F6; }
    [data-testid="stSidebar"] { background-color: #1a1d21; border-right: 1px solid #333; }
    
    /* PONT 4 JAVÍTÁS: Fenti üres tér eltüntetése */
    .block-container { 
        padding-top: 1.5rem !important; 
        padding-bottom: 2rem !important; 
    } 
    [data-testid="stVerticalBlock"] > div:first-child { margin-top: 0rem !important; }

    /* PONT 2 JAVÍTÁS: GOMBOK PIROS SZÍNÉNEK FELÜLÍRÁSA */
    /* Minden gomb típusra (elsődleges, másodlagos, letöltés) kiterjesztve */
    button, [data-testid="stBaseButton-secondary"], .stDownloadButton button {
        background-color: #262730 !important;
        color: #FFFFFF !important;
        border: 1px solid #4B4B4B !important;
        border-radius: 4px !important;
    }
    
    button:hover, [data-testid="stBaseButton-secondary"]:hover, .stDownloadButton button:hover {
        background-color: #00FF41 !important;
        color: #000000 !important;
        border-color: #00FF41 !important;
    }

    p, span, label, div, h1, h2, h3, .stMetric label, [data-testid="stMarkdownContainer"] p, 
    .stMultiSelect label, .stSlider label { 
        color: #F0F2F6 !important; 
    } 

    div[data-baseweb="popover"] * { color: #000000 !important; }
    div[data-baseweb="popover"] { background-color: #ffffff !important; }
    
    .sidebar-cite {
        font-size: 0.85rem !important;
        background-color: #262730;
        padding: 10px;
        border-radius: 5px;
        border: 1px solid #4B4B4B;
        margin-bottom: 20px;
    }
    .sidebar-cite a { color: #D3D3D3 !important; text-decoration: underline; }

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

    .debug-counter {
        font-size: 0.65rem;
        color: #444 !important;
        margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. Data Loading ---
@st.cache_data
def load_data():
    filename = "Acled_GTD_Drone_Database_20260509.csv"
    try:
        # A fájl beolvasása pontosvesszővel
        df = pd.read_csv(filename, sep=';', skiprows=0, engine='python', encoding='utf-8-sig')
        if "sep=" in str(df.iloc[0,0]):
            df = pd.read_csv(filename, sep=';', skiprows=1, engine='python', encoding='utf-8-sig')
            
        df.columns = df.columns.str.strip().str.lower()
        
        # Dátum formázás
        def create_date(row):
            try:
                return f"{int(row['year'])}-{int(row['month']):02d}-{int(row['day']):02d}"
            except:
                return str(row.get('year', ''))
        
        df['formatted_date'] = df.apply(create_date, axis=1)

        # Oszlopnév egységesítés (adatforras -> dbsource)
        if 'adatforras' in df.columns:
            df.rename(columns={'adatforras': 'dbsource'}, inplace=True)
        
        # Actor kategória
        def categorize_actor(name):
            name = str(name).strip().lower()
            if name == 'unknown': return 'Unknown'
            elif name.startswith('unidentified'): return 'Unidentified'
            else: return 'Terrorist Organization'
        
        if 'gname' in df.columns:
            df['actor_category'] = df['gname'].apply(categorize_actor)
        else:
            df['actor_category'] = 'Unknown'
            
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()

df_raw = load_data()

if not df_raw.empty:
    # --- 3. Sidebar & Filters ---
    with st.sidebar:
        # PONT 3: Teszt számláló (alig láthatóan)
        st.markdown(f'<div class="debug-counter">DEBUG: Data rows: {len(df_raw)}</div>', unsafe_allow_html=True)

        st.markdown(f"""
        <div class="sidebar-cite">
        <b>Cite as:</b><br>
        Besenyő, J.; Edelmann, D. (2026): Global Drone Terrorism Database (GDTD). Figshare. <br>
        <a href="https://doi.org/10.6084/m9.figshare.32128399" target="_blank">DOI: 10.6084/m9.figshare.32128399</a>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("### Filters")
        
        # PONT 1: Manual Filter (ON/OFF)
        manual_filter_on = st.toggle("Terrorist attacks only (Manual Filter)", value=False)
        if manual_filter_on and 'manual' in df_raw.columns:
            df_filtered = df_raw[df_raw['manual'].str.contains("terrorist attack", case=False, na=False)].copy()
        else:
            df_filtered = df_raw.copy()

        # Év szűrő
        if 'year' in df_filtered.columns:
            years = sorted(df_filtered['year'].dropna().unique().astype(int))
            yr_range = st.select_slider("Period", options=years, value=(min(years), max(years)))
            df_filtered = df_filtered[(df_filtered['year'] >= yr_range[0]) & (df_filtered['year'] <= yr_range[1])]

        # További eredeti szűrők (PONT 3)
        source_col = 'dbsource'
        if source_col in df_filtered.columns:
            sources = sorted(df_filtered[source_col].dropna().unique())
            sel_sources = st.multiselect("Data Source", sources, default=sources)
            df_filtered = df_filtered[df_filtered[source_col].isin(sel_sources)]

        if 'actor_category' in df_filtered.columns:
            actors = sorted(df_filtered['actor_category'].unique())
            sel_actors = st.multiselect("Actor Type", actors, default=actors)
            df_filtered = df_filtered[df_filtered['actor_category'].isin(sel_actors)]

        if 'country_txt' in df_filtered.columns:
            countries = sorted(df_filtered['country_txt'].dropna().unique())
            sel_countries = st.multiselect("Country", countries, default=countries)
            df_filtered = df_filtered[df_filtered['country_txt'].isin(sel_countries)]

        st.markdown("---")
        st.markdown("### Export Data")
        csv_data = df_filtered.to_csv(index=False, sep=';', encoding='utf-8-sig')
        st.download_button("Download CSV", csv_data, "GDTD_filtered.csv", "text/csv")

    # --- 4. Header & Metrics ---
    header_col1, header_col2, header_col3, header_col4 = st.columns([2.5, 1, 1, 1])
    with header_col1:
        st.markdown('<p class="main-title">GLOBAL DRONE<br>TERRORISM DATABASE</p>', unsafe_allow_html=True)
    with header_col2:
        st.metric("INCIDENTS", len(df_filtered))
    with header_col3:
        st.metric("COUNTRIES", df_filtered['country_txt'].nunique() if 'country_txt' in df_filtered.columns else 0)
    with header_col4:
        f_val = pd.to_numeric(df_filtered['nkill'], errors='coerce').sum()
        st.metric("FATALITIES", int(f_val if pd.notnull(f_val) else 0))

    st.markdown("<hr style='margin:10px 0px'>", unsafe_allow_html=True)

    # --- 5. Main Map ---
    if not df_filtered.empty:
        df_filtered['latitude'] = pd.to_numeric(df_filtered['latitude'], errors='coerce')
        df_filtered['longitude'] = pd.to_numeric(df_filtered['longitude'], errors='coerce')
        df_map = df_filtered.dropna(subset=['latitude', 'longitude'])
        
        df_map['lethality'] = pd.to_numeric(df_map['nkill'], errors='coerce').fillna(0).apply(lambda x: "Fatal Attack" if x > 0 else "Non-Fatal")

        fig_map = px.scatter_mapbox(
            df_map, lat='latitude', lon='longitude', 
            size=pd.to_numeric(df_map['nkill'], errors='coerce').fillna(0) + 3,
            color='lethality', color_discrete_map={'Fatal Attack': '#FF8C00', 'Non-Fatal': '#00FF41'},
            zoom=1.5, height=550, mapbox_style="carto-darkmatter",
            hover_name='city',
            hover_data={'formatted_date': True, 'gname': True, 'nkill': True}
        )
        fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, paper_bgcolor='rgba(0,0,0,0)', legend=dict(title_text="", yanchor="top", y=0.99, xanchor="left", x=0.01, bgcolor="rgba(0,0,0,0.5)"))
        st.plotly_chart(fig_map, use_container_width=True)

        # --- 6. Statistics Grid (PONT 3) ---
        st.markdown("### STATISTICS")
        
        def apply_bw_style(fig, x_title="", y_title="Number of Attacks"):
            fig.update_layout(
                plot_bgcolor='white', paper_bgcolor='white', 
                font=dict(family="Arial", size=11, color="black"),
                margin=dict(l=50, r=10, t=40, b=50),
                xaxis=dict(showgrid=False, linecolor='black', title=x_title),
                yaxis=dict(showgrid=False, linecolor='black', title=y_title),
                showlegend=False
            )
            return fig

        r1c1, r1c2 = st.columns(2)
        with r1c1:
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            trend = df_filtered.groupby('year').size().reset_index(name='count')
            fig1 = px.line(trend, x='year', y='count', title="Trend over Time")
            fig1.update_traces(line_color='black', line_width=2)
            st.plotly_chart(apply_bw_style(fig1, x_title="Year"), use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with r1c2:
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            top_g = df_filtered['gname'].value_counts().head(8).reset_index()
            top_g.columns = ['gname', 'count']
            fig2 = px.bar(top_g, x='count', y='gname', orientation='h', title="Top Organizations")
            fig2.update_traces(marker_color='black')
            st.plotly_chart(apply_bw_style(fig2, x_title="Number of Attacks", y_title=""), use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

    # --- FOOTER (PONT 4) ---
    st.markdown("""
        <div class="footer-note">
            Data sources: <br>
            GTD: START - National Consortium for the Study of Terrorism and Responses to Terrorism, Global Terrorism Database, 1970 - 2022, 2025 database, 2025. <br>
            ACLED: C. Raleigh, A. Linke, H. Hegre, J. Karlsen, Introducing ACLED: An armed conflict location and event dataset, J. Peace Res. 47, 2010.
        </div>
    """, unsafe_allow_html=True)
else:
    st.error("No data found or CSV error.")

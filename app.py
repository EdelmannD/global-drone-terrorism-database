import streamlit as st
import pandas as pd
import plotly.express as px

# --- 1. Page Config ---
st.set_page_config(page_title="GDTD Dashboard", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    .stApp { background-color: #121417; color: #F0F2F6; }
    [data-testid="stSidebar"] { background-color: #1a1d21; border-right: 1px solid #333; }
    
    .block-container { 
        padding-top: 1rem !important; 
        padding-bottom: 2rem !important; 
    } 
    
    /* Finomított felső margó, hogy ne vágja le a címet */
    [data-testid="stVerticalBlock"] > div:first-child { margin-top: -0.5rem !important; }

    p, span, label, div, h1, h2, h3, .stMetric label, [data-testid="stMarkdownContainer"] p, 
    .stMultiSelect label, .stSlider label { 
        color: #F0F2F6 !important; 
    } 

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

    .main-title {
        font-size: 1.6rem !important;
        font-weight: 800;
        color: #FFFFFF !important;
        line-height: 1.1;
        margin-top: 10px; /* Adtam neki egy kis helyet felül */
        margin-bottom: 0;
    }

    [data-testid="stMetric"] {
        background-color: #1e2124;
        padding: 5px 12px;
        border-radius: 4px;
        border-left: 3px solid #FFFFFF;
        margin-top: 10px;
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
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. Data Loading ---
@st.cache_data
def load_data():
    filename = "Acled_GTD_Drone_Database_20260429.csv"
    try:
        df = pd.read_csv(filename, sep=';', skiprows=0, engine='python', encoding='utf-8-sig')
        # Tisztítás: ha az első sor véletlenül a "sep=" jelölő lenne
        if df.columns[0].startswith('sep='):
            df = pd.read_csv(filename, sep=';', skiprows=1, engine='python', encoding='utf-8-sig')
            
        df.columns = df.columns.str.strip().str.lower()
        
        def create_date(row):
            try:
                return f"{int(row['year'])}-{int(row['month']):02d}-{int(row['day']):02d}"
            except:
                return str(row['year'])
        
        df['formatted_date'] = df.apply(create_date, axis=1)

        if 'adatforras' in df.columns:
            df.rename(columns={'adatforras': 'data_source'}, inplace=True)
        
        def categorize_actor(name):
            name = str(name).strip()
            if name.lower() == 'unknown': return 'Unknown'
            if name.lower().startswith('unidentified'): return 'Unidentified'
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
    city_col = 'city'

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
        
        years = sorted(df_raw[year_col].dropna().unique().astype(int))
        yr_range = st.select_slider("Period", options=years, value=(min(years), max(years)))
        df_filtered = df_raw[(df_raw[year_col] >= yr_range[0]) & (df_raw[year_col] <= yr_range[1])].copy()

        for col, label in [(source_col, "Data Source"), ('actor_category', "Actor Type"), 
                          (country_col, "Country"), ('attacktype1_txt', "Attack Type")]:
            options = sorted(df_filtered[col].fillna("N/A").unique())
            sel = st.multiselect(label, options, default=options)
            df_filtered = df_filtered[df_filtered[col].fillna("N/A").isin(sel)]

    # --- 4. Header (FIXED SPACING) ---
    header_col1, header_col2, header_col3, header_col4, _ = st.columns([2.5, 1, 1, 1, 0.4])
    with header_col1:
        st.markdown('<p class="main-title">GLOBAL DRONE<br>TERRORISM DATABASE</p>', unsafe_allow_html=True)
    with header_col2:
        st.metric("INCIDENTS", len(df_filtered))
    with header_col3:
        st.metric("COUNTRIES", df_filtered[country_col].nunique() if not df_filtered.empty else 0)
    with header_col4:
        f_val = pd.to_numeric(df_filtered[fatal_col], errors='coerce').sum()
        st.metric("FATALITIES", int(f_val if pd.notnull(f_val) else 0))

    st.markdown("<hr style='margin:10px 0px; border-color: #333;'>", unsafe_allow_html=True)

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
            hover_name='city',
            hover_data={'formatted_date': True, 'attacktype1_txt': True, 'gname': True, fatal_col: True, 'lethality': False, lat_col: False, lon_col: False}
        )
        
        fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, paper_bgcolor='rgba(0,0,0,0)',
                            legend=dict(title_text="", yanchor="top", y=0.99, xanchor="left", x=0.01, bgcolor="rgba(0,0,0,0.5)"))
        
        st.plotly_chart(fig_map, use_container_width=True)

        # --- 6. Statistics Grid ---
        st.markdown("### STATISTICS")
        
        def apply_bw_style(fig):
            fig.update_layout(plot_bgcolor='white', paper_bgcolor='white', font=dict(color="black"), margin=dict(l=40, r=10, t=40, b=40))
            return fig

        c1, c2 = st.columns(2)
        with c1:
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            trend = df_filtered.groupby('year').size().reset_index(name='count')
            st.plotly_chart(apply_bw_style(px.line(trend, x='year', y='count', title="Trend over Time")), use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        with c2:
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            top_g = df_filtered['gname'].value_counts().head(8).reset_index()
            st.plotly_chart(apply_bw_style(px.bar(top_g, x='count', y='gname', orientation='h', title="Top Groups")), use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="footer-note">Data sources: START GTD & ACLED (2026)</div>', unsafe_allow_html=True)
else:
    st.error("Adatbetöltési hiba.")

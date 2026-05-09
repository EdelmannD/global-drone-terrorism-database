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
    
    .block-container { padding-top: 1.8rem !important; padding-bottom: 2rem !important; } 
    [data-testid="stVerticalBlock"] > div:first-child { margin-top: 0rem !important; }

    p, span, label, div, h1, h2, h3, .stMetric label, [data-testid="stMarkdownContainer"] p, 
    .stMultiSelect label, .stSlider label { color: #F0F2F6 !important; } 

    div.stButton > button, [data-testid="stBaseButton-secondary"] {
        background-color: #262730 !important;
        color: #FFFFFF !important;
        border: 1px solid #4B4B4B !important;
        width: 100%;
        transition: all 0.3s ease;
    }
    
    div.stButton > button:hover, [data-testid="stBaseButton-secondary"]:hover {
        background-color: #00FF41 !important;
        color: #000000 !important;
        border-color: #00FF41 !important;
    }

    div[data-baseweb="popover"] * { color: #000000 !important; }
    div[data-baseweb="popover"] { background-color: #ffffff !important; border-radius: 4px; }
    div[role="listbox"] li { background-color: #ffffff !important; color: #000000 !important; }

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
    </style>
    """, unsafe_allow_html=True)

# --- 2. Data Loading ---
@st.cache_data
def load_data():
    # FRISSÍTETT FÁJLNÉV
    filename = "Acled_GTD_Drone_Database_20260509.csv"
    try:
        with open(filename, 'r', encoding='utf-8-sig') as f:
            first_line = f.readline()
        skip = 1 if "sep=" in first_line else 0
        df = pd.read_csv(filename, sep=';', skiprows=skip, engine='python', encoding='utf-8-sig')
        df.columns = df.columns.str.strip().str.lower()
        
        def create_date(row):
            try:
                return f"{int(row['year'])}-{int(row['month']):02d}-{int(row['day']):02d}"
            except:
                return str(row.get('year', ''))
        
        df['formatted_date'] = df.apply(create_date, axis=1)

        # Adatforrás harmonizáció
        if 'adatforras' in df.columns:
            df.rename(columns={'adatforras': 'data_source'}, inplace=True)
        
        def categorize_actor(name):
            name = str(name).strip()
            if name.lower() == 'unknown': return 'Unknown'
            elif name.lower().startswith('unidentified'): return 'Unidentified'
            else: return 'Terrorist Organization'
        
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

    # --- 3. Sidebar Filters ---
    with st.sidebar:
        st.markdown(f"""<div class="sidebar-cite"><b>Cite as:</b><br>Besenyő, J.; Edelmann, D. (2026): Global Drone Terrorism Database (GDTD). Figshare.</div>""", unsafe_allow_html=True)

        st.markdown("### Filters")
        
        # 1. Év szűrő
        years = sorted([int(x) for x in df_raw[year_col].dropna().unique()])
        yr_range = st.select_slider("Period", options=years, value=(min(years), max(years)))
        df_filtered = df_raw[(df_raw[year_col] >= yr_range[0]) & (df_raw[year_col] <= yr_range[1])].copy()

        # 2. ÚJ: Manual (Esemény jellege) szűrő
        if 'manual' in df_filtered.columns:
            manual_types = sorted([str(x) for x in df_filtered['manual'].unique() if pd.notnull(x)])
            sel_manual = st.multiselect("Incident Nature", manual_types, default=manual_types)
            df_filtered = df_filtered[df_filtered['manual'].astype(str).isin(sel_manual)]

        # 3. Forrás szűrő (HIBATŰRŐ VERZIÓ)
        sources = sorted([str(x) for x in df_filtered[source_col].unique() if pd.notnull(x)])
        sel_src = st.multiselect("Data Source", sources, default=sources)
        df_filtered = df_filtered[df_filtered[source_col].astype(str).isin(sel_src)]

        # 4. Actor szűrő
        actor_cats = sorted([str(x) for x in df_filtered['actor_category'].unique()])
        sel_act = st.multiselect("Actor Type", actor_cats, default=actor_cats)
        df_filtered = df_filtered[df_filtered['actor_category'].isin(sel_act)]

        # 5. Ország szűrő
        countries = sorted([str(x) for x in df_filtered[country_col].dropna().unique()])
        sel_cnt = st.multiselect("Country", countries, default=countries)
        df_filtered = df_filtered[df_filtered[country_col].astype(str).isin(sel_cnt)]

        # --- EXPORT ---
        st.markdown("---")
        csv_data = df_filtered.to_csv(index=False, sep=';', encoding='utf-8-sig')
        st.download_button(label="Download CSV", data=csv_data, file_name="GDTD_filtered.csv", mime="text/csv")

    # --- 4. Header ---
    c1, c2, c3, c4, _ = st.columns([2.5, 1, 1, 1, 0.4])
    with c1: st.markdown('<p class="main-title">GLOBAL DRONE<br>TERRORISM DATABASE</p>', unsafe_allow_html=True)
    with c2: st.metric("INCIDENTS", len(df_filtered))
    with c3: st.metric("COUNTRIES", df_filtered[country_col].nunique() if not df_filtered.empty else 0)
    with c4:
        f_val = pd.to_numeric(df_filtered[fatal_col], errors='coerce').sum()
        st.metric("FATALITIES", int(f_val if pd.notnull(f_val) else 0))

    # --- 5. Map ---
    if not df_filtered.empty:
        df_filtered[lat_col] = pd.to_numeric(df_filtered[lat_col], errors='coerce')
        df_filtered[lon_col] = pd.to_numeric(df_filtered[lon_col], errors='coerce')
        df_filtered[fatal_col] = pd.to_numeric(df_filtered[fatal_col], errors='coerce').fillna(0)
        df_filtered['lethality'] = df_filtered[fatal_col].apply(lambda x: "Fatal Attack" if x > 0 else "Non-Fatal")
        
        df_map = df_filtered.dropna(subset=[lat_col, lon_col])
        
        fig_map = px.scatter_mapbox(
            df_map, lat=lat_col, lon=lon_col, 
            size=df_map[fatal_col] + 3,
            color='lethality', color_discrete_map={'Fatal Attack': '#FF8C00', 'Non-Fatal': '#00FF41'},
            zoom=1.5, height=550, mapbox_style="carto-darkmatter",
            hover_name='city', hover_data=['formatted_date', 'gname', fatal_col]
        )
        fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, paper_bgcolor='rgba(0,0,0,0)', legend=dict(title_text="", yanchor="top", y=0.99, x=0.01))
        st.plotly_chart(fig_map, use_container_width=True)

        # --- 6. Statistics ---
        st.markdown("### STATISTICS")
        
        def apply_style(fig):
            fig.update_layout(plot_bgcolor='white', paper_bgcolor='white', font=dict(color="black"), showlegend=False)
            return fig

        r1, r2 = st.columns(2)
        with r1:
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            trend = df_filtered.groupby('year').size().reset_index(name='count')
            st.plotly_chart(apply_style(px.line(trend, x='year', y='count', title="Trend over Time")), use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with r2:
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            top_g = df_filtered['gname'].value_counts().head(8).reset_index()
            top_g.columns = ['gname', 'count']
            st.plotly_chart(apply_style(px.bar(top_g, x='count', y='gname', orientation='h', title="Top Organizations")), use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.warning("No data available for the selected filters.")
else:
    st.error("Dataset error. Please check your CSV file.")

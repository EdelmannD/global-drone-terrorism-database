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
    
    .block-container { 
        padding-top: 1.8rem !important; 
        padding-bottom: 2rem !important; 
    } 

    p, span, label, div, h1, h2, h3, .stMetric label, [data-testid="stMarkdownContainer"] p, 
    .stMultiSelect label, .stSlider label { 
        color: #F0F2F6 !important; 
    } 

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

    .sidebar-cite {
        font-size: 0.85rem !important;
        background-color: #262730;
        padding: 10px;
        border-radius: 5px;
        border: 1px solid #4B4B4B;
        margin-bottom: 20px;
    }

    .main-title {
        font-size: 1.6rem !important;
        font-weight: 800;
        color: #FFFFFF !important;
        line-height: 1.0;
    }

    [data-testid="stMetric"] {
        background-color: #1e2124;
        padding: 5px 12px;
        border-radius: 4px;
        border-left: 3px solid #FFFFFF;
    }

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
    # AZ ÚJ FÁJLNEVED:
    filename = "Acled_GTD_Drone_Database_20260509.csv"
    try:
        with open(filename, 'r', encoding='utf-8-sig') as f:
            first_line = f.readline()
        
        # Kezeli a sep=; jelzést az Excel-alapú CSV-nél
        skip = 1 if "sep=" in first_line else 0
        df = pd.read_csv(filename, sep=';', skiprows=skip, engine='python', encoding='utf-8-sig')
        
        # Oszlopnevek tisztítása
        df.columns = df.columns.str.strip().str.lower()
        
        # Dátum generálása
        def create_date(row):
            try:
                return f"{int(row['year'])}-{int(row['month']):02d}-{int(row['day']):02d}"
            except:
                return str(row.get('year', 'N/A'))
        
        df['formatted_date'] = df.apply(create_date, axis=1)

        # Forrás oszlop elnevezése
        if 'dbsource' in df.columns:
            df.rename(columns={'dbsource': 'data_source'}, inplace=True)
        
        # Actor kategória (régi logikád szerint)
        def categorize_actor(name):
            name = str(name).strip().lower()
            if name == 'unknown': return 'Unknown'
            elif name.startswith('unidentified'): return 'Unidentified'
            else: return 'Terrorist Organization'
        
        actor_col = 'gname' if 'gname' in df.columns else 'actor1'
        if actor_col in df.columns:
            df['actor_category'] = df[actor_col].apply(categorize_actor)
        else:
            df['actor_category'] = 'Unknown'
            
        return df
    except Exception as e:
        st.sidebar.error(f"Error loading file: {e}")
        return pd.DataFrame()

df_raw = load_data()

if not df_raw.empty:
    # Oszlopnevek fixálása
    lat_col, lon_col = 'latitude', 'longitude'
    year_col, country_col = 'year', 'country_txt'
    fatal_col, source_col = 'nkill', 'data_source'

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
        
        # Év szűrő
        if year_col in df_raw.columns:
            years = sorted(df_raw[year_col].dropna().unique().astype(int))
            yr_range = st.select_slider("Period", options=years, value=(min(years), max(years)))
            df_filtered = df_raw[(df_raw[year_col] >= yr_range[0]) & (df_raw[year_col] <= yr_range[1])].copy()
        else:
            df_filtered = df_raw.copy()

        # Dinamikus multiselect szűrők (Data Source, Actor Type, Country)
        for col, label in [(source_col, "Data Source"), ('actor_category', "Actor Type"), (country_col, "Country")]:
            if col in df_filtered.columns:
                options = sorted(df_filtered[col].dropna().unique())
                selected = st.multiselect(label, options, default=options)
                df_filtered = df_filtered[df_filtered[col].isin(selected)]

        # --- EXPORT ---
        st.markdown("---")
        csv_buffer = df_filtered.to_csv(index=False, sep=';', encoding='utf-8-sig')
        st.download_button("Download CSV", csv_buffer, "GDTD_filtered.csv", "text/csv")

    # --- 4. Header Metrics ---
    c1, c2, c3, c4 = st.columns([2.5, 1, 1, 1])
    with c1: st.markdown('<p class="main-title">GLOBAL DRONE<br>TERRORISM DATABASE</p>', unsafe_allow_html=True)
    with c2: st.metric("INCIDENTS", len(df_filtered))
    with c3: st.metric("COUNTRIES", df_filtered[country_col].nunique() if country_col in df_filtered.columns else 0)
    with c4: 
        kills = pd.to_numeric(df_filtered[fatal_col], errors='coerce').sum() if fatal_col in df_filtered.columns else 0
        st.metric("FATALITIES", int(kills))

    st.markdown("<hr style='margin:10px 0px'>", unsafe_allow_html=True)

    # --- 5. TÉRKÉP (A régi "szuper" verzió) ---
    if not df_filtered.empty and lat_col in df_filtered.columns:
        df_filtered[lat_col] = pd.to_numeric(df_filtered[lat_col], errors='coerce')
        df_filtered[lon_col] = pd.to_numeric(df_filtered[lon_col], errors='coerce')
        df_filtered[fatal_col] = pd.to_numeric(df_filtered[fatal_col], errors='coerce').fillna(0)
        
        df_filtered['lethality'] = df_filtered[fatal_col].apply(lambda x: "Fatal Attack" if x > 0 else "Non-Fatal")
        df_map = df_filtered.dropna(subset=[lat_col, lon_col])
        bubble_size = df_map[fatal_col] + 3

        fig_map = px.scatter_mapbox(
            df_map, lat=lat_col, lon=lon_col, size=bubble_size,
            color='lethality', color_discrete_map={'Fatal Attack': '#FF8C00', 'Non-Fatal': '#00FF41'},
            zoom=1.5, height=550, mapbox_style="carto-darkmatter",
            hover_name='city',
            hover_data={'formatted_date': True, 'gname': True, fatal_col: True, 'lethality': False, lat_col: False, lon_col: False}
        )
        fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, paper_bgcolor='rgba(0,0,0,0)', legend=dict(title_text="", yanchor="top", y=0.99, xanchor="left", x=0.01))
        st.plotly_chart(fig_map, use_container_width=True)

    # --- 6. STATISZTIKÁK (A régi fekete-fehér stílusban) ---
    st.markdown("### STATISTICS")

    def apply_bw_style(fig, x_title="", y_title="Number of Attacks"):
        fig.update_layout(
            plot_bgcolor='white', paper_bgcolor='white', 
            font=dict(family="Arial", size=11, color="black"),
            xaxis=dict(showgrid=False, linecolor='black', title=x_title),
            yaxis=dict(showgrid=False, linecolor='black', title=y_title),
            showlegend=False
        )
        return fig

    col_a, col_b = st.columns(2)
    
    with col_a:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        trend = df_filtered.groupby('year').size().reset_index(name='count')
        fig1 = px.line(trend, x='year', y='count', title="Trend over Time")
        fig1.update_traces(line_color='black', line_width=2)
        st.plotly_chart(apply_bw_style(fig1, "Year"), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_b:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        top_g = df_filtered['gname'].value_counts().head(8).reset_index()
        top_g.columns = ['gname', 'count']
        fig2 = px.bar(top_g, x='count', y='gname', orientation='h', title="Top 8 Organizations")
        fig2.update_traces(marker_color='black')
        st.plotly_chart(apply_bw_style(fig2, "Attacks", ""), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

else:
    st.error("Nem sikerült betölteni az adatokat. Ellenőrizd, hogy a 'Acled_GTD_Drone_Database_20260509.csv' fájl a helyén van-e!")

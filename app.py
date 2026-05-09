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
    
    /* GOMBOK DESIGN - Sötétszürke alap, fehér betű */
    button[kind="secondary"], .stDownloadButton > button {
        background-color: #262730 !important;
        color: #FFFFFF !important;
        border: 1px solid #4B4B4B !important;
        border-radius: 4px;
        width: 100%;
        height: 3em;
        transition: all 0.3s ease;
    }
    
    /* HOVER - Zöld háttér, fekete betű */
    button[kind="secondary"]:hover, .stDownloadButton > button:hover {
        background-color: #00FF41 !important;
        color: #000000 !important;
        border-color: #00FF41 !important;
    }

    /* SZÖVEGEK SZÍNE */
    p, span, label, div, h1, h2, h3, .stMetric label, [data-testid="stMarkdownContainer"] p { 
        color: #F0F2F6 !important; 
    } 

    .sidebar-cite {
        font-size: 0.85rem !important;
        background-color: #262730;
        padding: 10px;
        border-radius: 5px;
        border: 1px solid #4B4B4B;
        margin-bottom: 20px;
    }
    .sidebar-cite a { color: #00FF41 !important; }

    .main-title {
        font-size: 1.6rem !important;
        font-weight: 800;
        color: #FFFFFF !important;
        line-height: 1.0;
        margin-bottom: 0;
    }

    [data-testid="stMetric"] {
        background-color: #1e2124;
        padding: 10px;
        border-radius: 4px;
        border-left: 3px solid #FFFFFF;
    }

    .chart-container {
        background-color: #FFFFFF;
        padding: 15px;
        border-radius: 4px;
        border: 2px solid #000000;
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. Data Loading ---
@st.cache_data
def load_data():
    filename = "Acled_GTD_Drone_Database_20260509.csv"
    try:
        # Beolvassuk az első sort, hogy lássuk van-e sep=;
        with open(filename, 'r', encoding='utf-8-sig') as f:
            first_line = f.readline()
        
        skip = 1 if "sep=" in first_line else 0
        df = pd.read_csv(filename, sep=';', skiprows=skip, engine='python', encoding='utf-8-sig')
        
        # Tisztítás: szóközök eltávolítása az oszlopnevekből
        df.columns = df.columns.str.strip()
        
        # Dátum formázás a térképhez
        def create_date(row):
            try:
                return f"{int(row['year'])}-{int(row['month']):02d}-{int(row['day']):02d}"
            except:
                return str(row.get('year', 'N/A'))
        
        df['formatted_date'] = df.apply(create_date, axis=1)

        # Actor kategória meghatározása
        def categorize_actor(name):
            name = str(name).strip().lower()
            if "unknown" in name or "unidentified military" in name: return "Unknown/Military"
            elif "unidentified" in name: return "Unidentified Group"
            else: return "Terrorist Organization"
        
        if 'gname' in df.columns:
            df['actor_category'] = df['gname'].apply(categorize_actor)
            
        return df
    except Exception as e:
        st.error(f"Hiba történt a fájl beolvasásakor: {e}")
        return pd.DataFrame()

df_raw = load_data()

if not df_raw.empty:
    # --- 3. Sidebar Filters ---
    with st.sidebar:
        st.markdown(f"""
        <div class="sidebar-cite">
        <b>Cite as:</b><br>
        Besenyő, J.; Edelmann, D. (2026): Global Drone Terrorism Database (GDTD). Figshare. <br>
        <a href="https://doi.org/10.6084/m9.figshare.32128399" target="_blank">DOI: 10.6084/m9.figshare.32128399</a>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("### Filters")
        
        # 1. MANUAL FILTER (ELSŐ HELYEN)
        if 'manual' in df_raw.columns:
            man_opts = sorted(df_raw['manual'].dropna().unique())
            sel_man = st.multiselect("Manual Filter", man_opts, default=man_opts)
            df_filtered = df_raw[df_raw['manual'].isin(sel_man)].copy()
        else:
            df_filtered = df_raw.copy()

        # 2. PERIOD
        if 'year' in df_filtered.columns:
            years = sorted(df_filtered['year'].dropna().unique().astype(int))
            yr_range = st.select_slider("Period", options=years, value=(min(years), max(years)))
            df_filtered = df_filtered[(df_filtered['year'] >= yr_range[0]) & (df_filtered['year'] <= yr_range[1])]

        # 3. DATABASE SOURCE (GTD/ACLED)
        if 'dbsource' in df_filtered.columns:
            db_opts = sorted(df_filtered['dbsource'].dropna().unique())
            sel_db = st.multiselect("Database Source", db_opts, default=db_opts)
            df_filtered = df_filtered[df_filtered['dbsource'].isin(sel_db)]

        # 4. COUNTRY
        if 'country_txt' in df_filtered.columns:
            countries = sorted(df_filtered['country_txt'].dropna().unique())
            sel_countries = st.multiselect("Country", countries, default=countries)
            df_filtered = df_filtered[df_filtered['country_txt'].isin(sel_countries)]

        # 5. ACTOR TYPE
        if 'actor_category' in df_filtered.columns:
            actors = sorted(df_filtered['actor_category'].unique())
            sel_actors = st.multiselect("Actor Type", actors, default=actors)
            df_filtered = df_filtered[df_filtered['actor_category'].isin(sel_actors)]

        st.markdown("---")
        # Export Gomb
        csv_exp = df_filtered.to_csv(index=False, sep=';', encoding='utf-8-sig')
        st.download_button("Download Filtered Data", csv_exp, "GDTD_export.csv", "text/csv")

    # --- 4. Header Metrics ---
    c1, c2, c3, c4 = st.columns([2.5, 1, 1, 1])
    with c1:
        st.markdown('<p class="main-title">GLOBAL DRONE<br>TERRORISM DATABASE</p>', unsafe_allow_html=True)
    with c2:
        st.metric("INCIDENTS", len(df_filtered))
    with c3:
        st.metric("COUNTRIES", df_filtered['country_txt'].nunique() if 'country_txt' in df_filtered else 0)
    with c4:
        kills = pd.to_numeric(df_filtered['nkill'], errors='coerce').sum()
        st.metric("FATALITIES", int(kills if pd.notnull(kills) else 0))

    st.markdown("<hr style='margin:10px 0px'>", unsafe_allow_html=True)

    # --- 5. Térkép ---
    if not df_filtered.empty:
        df_filtered['latitude'] = pd.to_numeric(df_filtered['latitude'], errors='coerce')
        df_filtered['longitude'] = pd.to_numeric(df_filtered['longitude'], errors='coerce')
        df_map = df_filtered.dropna(subset=['latitude', 'longitude'])
        
        df_map['lethality'] = df_map['nkill'].apply(lambda x: "Fatal Attack" if x > 0 else "Non-Fatal")
        
        fig_map = px.scatter_mapbox(
            df_map, lat='latitude', lon='longitude', 
            size=pd.to_numeric(df_map['nkill'], errors='coerce').fillna(0) + 3,
            color='lethality', 
            color_discrete_map={'Fatal Attack': '#FF8C00', 'Non-Fatal': '#00FF41'},
            zoom=1.5, height=550, mapbox_style="carto-darkmatter",
            hover_name='city',
            hover_data={'formatted_date': True, 'gname': True, 'nkill': True, 'lethality': False, 'latitude': False, 'longitude': False}
        )
        fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, paper_bgcolor='rgba(0,0,0,0)', legend=dict(title="", yanchor="top", y=0.99, xanchor="left", x=0.01))
        st.plotly_chart(fig_map, use_container_width=True)

        # --- 6. Grafikonok ---
        st.markdown("### STATISTICS")
        
        def apply_style(fig):
            fig.update_layout(
                plot_bgcolor='white', paper_bgcolor='white',
                font=dict(color="black", family="Arial"),
                xaxis=dict(showgrid=False, linecolor='black'),
                yaxis=dict(showgrid=False, linecolor='black'),
                showlegend=False
            )
            return fig

        r1, r2 = st.columns(2)
        with r1:
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            trend = df_filtered.groupby('year').size().reset_index(name='count')
            f1 = px.line(trend, x='year', y='count', title="Incidents over Time")
            f1.update_traces(line_color='black', line_width=2)
            st.plotly_chart(apply_style(f1), use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
        with r2:
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            top_org = df_filtered['gname'].value_counts().head(8).reset_index()
            top_org.columns = ['Organization', 'Attacks']
            f2 = px.bar(top_org, x='Attacks', y='Organization', orientation='h', title="Top 8 Organizations")
            f2.update_traces(marker_color='black')
            st.plotly_chart(apply_style(f2), use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
else:
    st.warning("No data found matching the filters.")

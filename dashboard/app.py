import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st
from datetime import date

from data.connector import get_resumen_por_pais, get_campanas
from data.aurora import cargar_excel, leer_leads_nuevos
from components.charts import render_kpi_cards, render_tabla_mensual
from components.campanas import render_campanas
from components.nuevos import render_nuevos
from config import PAISES

st.set_page_config(
    page_title="Control Diario — Meta Ads",
    page_icon="📊",
    layout="wide",
)

st.markdown(
    """
    <style>
    [data-testid="stAppViewContainer"] { background-color: #0e1117; }
    [data-testid="stHeader"] { background-color: #0e1117; }
    [data-testid="stSidebar"] { background-color: #0e1117; }
    h1, h2, h3 { color: white !important; }
    .block-container { padding-top: 1.5rem; }
    [data-testid="stTabs"] button { color: #aaa !important; }
    [data-testid="stTabs"] button[aria-selected="true"] { color: white !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown("## Control diario — Meta Ads")

hoy = date.today()
_, col_fecha = st.columns([3, 1])
with col_fecha:
    rango = st.date_input("Fechas", value=(hoy, hoy), max_value=hoy, label_visibility="collapsed")

fecha_inicio, fecha_fin = (rango[0], rango[1]) if isinstance(rango, (list, tuple)) and len(rango) == 2 else (hoy, hoy)

st.divider()

# ── Pestañas ───────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["Control Diario", "Campañas por País", "Nuevos & Reingresos"])

with tab1:
    with st.spinner("Cargando datos..."):
        df_resumen = get_resumen_por_pais(fecha_inicio, fecha_fin)

    render_kpi_cards(df_resumen, fecha_fin)
    st.markdown("<br>", unsafe_allow_html=True)
    render_tabla_mensual(df_resumen, fecha_fin)

with tab2:
    col_pais, _ = st.columns([1, 3])
    with col_pais:
        pais_sel = st.selectbox("País", list(PAISES.keys()), label_visibility="collapsed")

    with st.spinner("Cargando campañas..."):
        df_campanas = get_campanas(fecha_inicio, fecha_fin)

    render_campanas(df_campanas, pais_sel)

with tab3:
    st.markdown("#### Leads Nuevos vs Reingresos")

    uploaded = st.file_uploader(
        "Sube el Excel de Leads (Leads_Mktg_General.xlsx)",
        type=["xlsx"],
        help="Pestaña 'Resumen Leads Mktg' — Display + BAU-Display",
    )
    if uploaded:
        with st.spinner("Cargando datos al Google Sheet..."):
            n, msg = cargar_excel(uploaded)
        if n > 0:
            st.success(msg)
        else:
            st.error(msg)

    st.markdown("<br>", unsafe_allow_html=True)

    with st.spinner("Leyendo histórico..."):
        df_nuevos  = leer_leads_nuevos(fecha_inicio, fecha_fin)
        df_resumen3 = get_resumen_por_pais(fecha_inicio, fecha_fin)

    render_nuevos(df_resumen3, df_nuevos, pais_sel if "pais_sel" in dir() else "Chile")

import sys
import os
import base64
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st
from datetime import date, timedelta

from data.connector import get_resumen_por_pais, get_campanas
from data.aurora import cargar_excel, leer_leads_nuevos
from components.charts import render_kpi_cards, render_tabla_mensual
from components.campanas import render_campanas
from components.nuevos import render_nuevos
from config import PAISES

st.set_page_config(
    page_title="Capitaria — Paid Media",
    page_icon="🟢",
    layout="wide",
)

st.markdown(
    """
    <style>
    [data-testid="stAppViewContainer"] { background-color: #0e1117; }
    [data-testid="stHeader"] { background-color: #0e1117; }
    [data-testid="stSidebar"] { background-color: #0e1117; }
    h1, h2, h3 { color: white !important; }
    .block-container { padding-top: 2.5rem; }
    [data-testid="stTabs"] button { color: #aaa !important; }
    [data-testid="stTabs"] button[aria-selected="true"] { color: white !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Header ─────────────────────────────────────────────────────────────────────
_logo_path    = os.path.join(os.path.dirname(__file__), "assets", "logo.png")
_favicon_path = os.path.join(os.path.dirname(__file__), "assets", "favicon.png")
_logo_b64    = base64.b64encode(open(_logo_path,    "rb").read()).decode()
_favicon_b64 = base64.b64encode(open(_favicon_path, "rb").read()).decode()

st.markdown(
    f"<link rel='shortcut icon' href='data:image/png;base64,{_favicon_b64}'>",
    unsafe_allow_html=True,
)

hoy = date.today()
col_logo, col_fecha = st.columns([3, 1])
with col_logo:
    st.markdown(
        f"<img src='data:image/png;base64,{_logo_b64}' style='height:52px;object-fit:contain;margin-top:8px;'>",
        unsafe_allow_html=True,
    )
with col_fecha:
    PRESETS = {
        "Hoy":            (hoy, hoy),
        "Ayer":           (hoy - timedelta(days=1), hoy - timedelta(days=1)),
        "Últimos 7 días": (hoy - timedelta(days=6), hoy),
        "Últimos 30 días":(hoy - timedelta(days=29), hoy),
        "Personalizado":  None,
    }
    preset = st.selectbox("Período", list(PRESETS.keys()), index=1, label_visibility="collapsed")
    if PRESETS[preset]:
        fecha_inicio, fecha_fin = PRESETS[preset]
    else:
        rango = st.date_input("Rango", value=(hoy, hoy), max_value=hoy, label_visibility="collapsed")
        fecha_inicio, fecha_fin = (rango[0], rango[1]) if isinstance(rango, (list, tuple)) and len(rango) == 2 else (hoy, hoy)

st.divider()

# ── Diagnóstico API key (temporal) ─────────────────────────────────────────────
_key_env = os.getenv("SUPERMETRICS_API_KEY", "")
_key_sec = ""
try:
    _key_sec = st.secrets.get("SUPERMETRICS_API_KEY", "")
except Exception:
    pass
_api_key_ok = bool(_key_env or _key_sec)
if not _api_key_ok:
    st.error("❌ SUPERMETRICS_API_KEY no encontrada. Configúrala en Streamlit Cloud → Settings → Secrets.")
    st.stop()

# ── Cargar datos (cacheados 5 min — solo llama a Supermetrics una vez) ─────────
@st.cache_data(ttl=300, show_spinner=False)
def _cargar_resumen(fi, ff):
    return get_resumen_por_pais(fi, ff)

@st.cache_data(ttl=300, show_spinner=False)
def _cargar_campanas(fi, ff):
    return get_campanas(fi, ff)

with st.spinner("Cargando datos de Meta Ads... (primera carga ~30s)"):
    df_resumen  = _cargar_resumen(fecha_inicio, fecha_fin)
    df_campanas = _cargar_campanas(fecha_inicio, fecha_fin)

if df_resumen.empty:
    st.warning("Sin datos para el período seleccionado. Prueba con 'Últimos 7 días'.")

# ── Pestañas ───────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["Control Diario", "Campañas por País", "Nuevos & Reingresos"])

with tab1:
    render_kpi_cards(df_resumen, fecha_fin)
    st.markdown("<br>", unsafe_allow_html=True)
    render_tabla_mensual(df_resumen, fecha_fin)

with tab2:
    col_pais, _ = st.columns([1, 3])
    with col_pais:
        pais_sel = st.selectbox("País", list(PAISES.keys()), label_visibility="collapsed")
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
        df_nuevos = leer_leads_nuevos(fecha_inicio, fecha_fin)

    render_nuevos(df_resumen, df_nuevos, pais_sel if "pais_sel" in dir() else "Chile")

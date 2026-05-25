import os
import pandas as pd
from datetime import date
from dotenv import load_dotenv

load_dotenv()


def _get_api_key() -> str:
    # Local: desde .env. Streamlit Cloud: desde st.secrets
    key = os.getenv("SUPERMETRICS_API_KEY", "")
    if not key:
        try:
            import streamlit as st
            key = st.secrets.get("SUPERMETRICS_API_KEY", "")
        except Exception:
            pass
    return key


def _empty_resumen() -> pd.DataFrame:
    return pd.DataFrame(columns=["pais", "fecha", "gasto", "leads"])


def _empty_campanas() -> pd.DataFrame:
    return pd.DataFrame(columns=["pais", "campana", "campaign_id", "gasto", "costo_lead", "leads"])


def get_meta_ads(fecha_inicio: date, fecha_fin: date) -> pd.DataFrame:
    import streamlit as st

    api_key = _get_api_key()
    if not api_key:
        st.warning("⚠️ SUPERMETRICS_API_KEY no configurada.", icon="⚠️")
        return _empty_resumen()
    try:
        from data.supermetrics import query_meta_ads
        df = query_meta_ads(fecha_inicio, fecha_fin, api_key)
        if df.empty:
            st.info("ℹ️ Sin datos para el período seleccionado.")
        return df if not df.empty else _empty_resumen()
    except Exception as e:
        st.error(f"❌ Error Supermetrics: {e}")
        return _empty_resumen()


@st.cache_data(ttl=300, show_spinner=False)
def get_resumen_por_pais(fecha_inicio: date, fecha_fin: date) -> pd.DataFrame:
    df = get_meta_ads(fecha_inicio, fecha_fin)
    if df.empty:
        return df
    return (
        df.groupby("pais")
        .agg(gasto=("gasto", "sum"), leads=("leads", "sum"))
        .reset_index()
    )


@st.cache_data(ttl=300, show_spinner=False)
def get_campanas(fecha_inicio: date, fecha_fin: date) -> pd.DataFrame:
    import streamlit as st

    api_key = _get_api_key()
    if not api_key:
        return _empty_campanas()
    try:
        from data.supermetrics import query_campanas
        df = query_campanas(fecha_inicio, fecha_fin, api_key)
        return df if not df.empty else _empty_campanas()
    except Exception as e:
        st.error(f"❌ Error campañas: {e}")
        return _empty_campanas()

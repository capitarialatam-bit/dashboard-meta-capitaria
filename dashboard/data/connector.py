import os
import pandas as pd
import streamlit as st
from datetime import date
from dotenv import load_dotenv

load_dotenv()


def _get_api_key() -> str:
    key = os.getenv("SUPERMETRICS_API_KEY", "")
    if not key:
        try:
            key = st.secrets.get("SUPERMETRICS_API_KEY", "")
        except Exception:
            pass
    return key


@st.cache_data(ttl=300, show_spinner=False)
def _query_supermetrics(fecha_inicio: date, fecha_fin: date) -> pd.DataFrame:
    """
    UNA sola llamada a Supermetrics por sesión (cacheada 5 min).
    Devuelve el DataFrame base con todas las columnas.
    Tanto get_resumen_por_pais como get_campanas consumen este cache.
    """
    api_key = _get_api_key()
    if not api_key:
        return pd.DataFrame()
    try:
        from data.supermetrics import _query_base
        return _query_base(fecha_inicio, fecha_fin, api_key)
    except Exception as e:
        print(f"[connector] Supermetrics error: {e}")
        return pd.DataFrame()


def get_resumen_por_pais(fecha_inicio: date, fecha_fin: date) -> pd.DataFrame:
    """Gasto y leads por país. Fuente: Supermetrics (cacheado)."""
    df = _query_supermetrics(fecha_inicio, fecha_fin)
    if df.empty:
        return pd.DataFrame(columns=["pais", "gasto", "leads"])
    return (df.groupby("pais")
              .agg(gasto=("gasto", "sum"), leads=("leads", "sum"))
              .reset_index())


def get_campanas(fecha_inicio: date, fecha_fin: date) -> pd.DataFrame:
    """Desglose por campaña. Fuente: Supermetrics (cacheado)."""
    df = _query_supermetrics(fecha_inicio, fecha_fin)
    if df.empty:
        return pd.DataFrame(columns=["pais", "campana", "campaign_id", "gasto", "costo_lead", "leads"])
    resultado = (
        df.groupby(["pais", "campana", "campaign_id"])
        .agg(gasto=("gasto", "sum"), leads=("leads", "sum"))
        .reset_index()
    )
    resultado["costo_lead"] = resultado.apply(
        lambda r: r["gasto"] / r["leads"] if r["leads"] > 0 else 0, axis=1
    )
    return resultado[["pais", "campana", "campaign_id", "gasto", "costo_lead", "leads"]]

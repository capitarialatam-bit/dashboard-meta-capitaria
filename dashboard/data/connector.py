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


def get_resumen_por_pais(fecha_inicio: date, fecha_fin: date) -> pd.DataFrame:
    """Gasto y leads por país para el rango de fechas. Fuente: Supermetrics."""
    api_key = _get_api_key()
    if not api_key:
        return pd.DataFrame(columns=["pais", "gasto", "leads"])
    try:
        from data.supermetrics import query_meta_ads
        df = query_meta_ads(fecha_inicio, fecha_fin, api_key)
        if df.empty:
            return pd.DataFrame(columns=["pais", "gasto", "leads"])
        return (df.groupby("pais")
                  .agg(gasto=("gasto", "sum"), leads=("leads", "sum"))
                  .reset_index())
    except Exception as e:
        print(f"[connector] Supermetrics resumen error: {e}")
        return pd.DataFrame(columns=["pais", "gasto", "leads"])


def get_campanas(fecha_inicio: date, fecha_fin: date) -> pd.DataFrame:
    """Desglose por campaña con país. Fuente: Supermetrics."""
    api_key = _get_api_key()
    if not api_key:
        return pd.DataFrame(columns=["pais", "campana", "campaign_id", "gasto", "costo_lead", "leads"])
    try:
        from data.supermetrics import query_campanas
        df = query_campanas(fecha_inicio, fecha_fin, api_key)
        return df if not df.empty else pd.DataFrame(
            columns=["pais", "campana", "campaign_id", "gasto", "costo_lead", "leads"]
        )
    except Exception as e:
        print(f"[connector] Supermetrics campanas error: {e}")
        return pd.DataFrame(columns=["pais", "campana", "campaign_id", "gasto", "costo_lead", "leads"])

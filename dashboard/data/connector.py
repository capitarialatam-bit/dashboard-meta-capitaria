import os
import pandas as pd
from datetime import date
from dotenv import load_dotenv

load_dotenv()


def _get_api_key() -> str:
    key = os.getenv("SUPERMETRICS_API_KEY", "")
    if not key:
        try:
            import streamlit as st
            key = st.secrets.get("SUPERMETRICS_API_KEY", "")
        except Exception:
            pass
    return key


def get_resumen_por_pais(fecha_inicio: date, fecha_fin: date) -> pd.DataFrame:
    api_key = _get_api_key()
    if not api_key:
        return pd.DataFrame(columns=["pais", "gasto", "leads"])
    try:
        from data.supermetrics import query_meta_ads
        df = query_meta_ads(fecha_inicio, fecha_fin, api_key)
        if df.empty:
            return pd.DataFrame(columns=["pais", "gasto", "leads"])
        return (
            df.groupby("pais")
            .agg(gasto=("gasto", "sum"), leads=("leads", "sum"))
            .reset_index()
        )
    except Exception as e:
        print(f"[connector] Error resumen: {e}")
        return pd.DataFrame(columns=["pais", "gasto", "leads"])


def get_campanas(fecha_inicio: date, fecha_fin: date) -> pd.DataFrame:
    api_key = _get_api_key()
    if not api_key:
        return pd.DataFrame(columns=["pais", "campana", "campaign_id", "gasto", "costo_lead", "leads"])
    try:
        from data.supermetrics import query_campanas
        df = query_campanas(fecha_inicio, fecha_fin, api_key)
        return df if not df.empty else pd.DataFrame(columns=["pais", "campana", "campaign_id", "gasto", "costo_lead", "leads"])
    except Exception as e:
        print(f"[connector] Error campañas: {e}")
        return pd.DataFrame(columns=["pais", "campana", "campaign_id", "gasto", "costo_lead", "leads"])

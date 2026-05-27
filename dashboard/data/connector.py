import os
import pandas as pd
import streamlit as st
from datetime import date
from dotenv import load_dotenv

load_dotenv()

SHEET_ID = "1cOz6ZfsKHl5JRvHpNNlsgENU0K14wtHwZElh75mC32I"
SCOPES   = ["https://www.googleapis.com/auth/spreadsheets",
             "https://www.googleapis.com/auth/drive"]


def _get_api_key() -> str:
    key = os.getenv("SUPERMETRICS_API_KEY", "")
    if not key:
        try:
            key = st.secrets.get("SUPERMETRICS_API_KEY", "")
        except Exception:
            pass
    return key


def _gsheet_client():
    import gspread
    from google.oauth2.service_account import Credentials
    creds = Credentials.from_service_account_info(
        dict(st.secrets["gcp_service_account"]), scopes=SCOPES
    )
    return gspread.authorize(creds)


# ── Leer desde Google Sheets (fuente principal) ────────────────────────────────

def _leer_resumen_sheets(fecha_inicio: date, fecha_fin: date) -> pd.DataFrame:
    try:
        gc = _gsheet_client()
        ws = gc.open_by_key(SHEET_ID).worksheet("meta_resumen")
        data = ws.get_all_records()
        if not data:
            return pd.DataFrame()
        df = pd.DataFrame(data)
        df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce").dt.date
        df["gasto"] = pd.to_numeric(df["gasto"], errors="coerce").fillna(0)
        df["leads"] = pd.to_numeric(df["leads"], errors="coerce").fillna(0).astype(int)
        df = df[(df["fecha"] >= fecha_inicio) & (df["fecha"] <= fecha_fin)]
        if df.empty:
            return pd.DataFrame()
        return (df.groupby("pais")
                  .agg(gasto=("gasto", "sum"), leads=("leads", "sum"))
                  .reset_index())
    except Exception as e:
        print(f"[connector] Sheets resumen error: {e}")
        return pd.DataFrame()


def _leer_campanas_sheets(fecha_inicio: date, fecha_fin: date) -> pd.DataFrame:
    try:
        gc = _gsheet_client()
        ws = gc.open_by_key(SHEET_ID).worksheet("meta_campanas")
        data = ws.get_all_records()
        if not data:
            return pd.DataFrame()
        df = pd.DataFrame(data)
        df["gasto"]      = pd.to_numeric(df["gasto"],      errors="coerce").fillna(0)
        df["leads"]      = pd.to_numeric(df["leads"],      errors="coerce").fillna(0).astype(int)
        df["costo_lead"] = pd.to_numeric(df["costo_lead"], errors="coerce").fillna(0)
        return df[["pais", "campana", "campaign_id", "gasto", "costo_lead", "leads"]]
    except Exception as e:
        print(f"[connector] Sheets campanas error: {e}")
        return pd.DataFrame()


# ── Fallback: Supermetrics directo ────────────────────────────────────────────

def _desde_supermetrics_resumen(fecha_inicio: date, fecha_fin: date) -> pd.DataFrame:
    api_key = _get_api_key()
    if not api_key:
        return pd.DataFrame(columns=["pais", "gasto", "leads"])
    try:
        from data.supermetrics import query_meta_ads
        df = query_meta_ads(fecha_inicio, fecha_fin, api_key)
        if df.empty:
            return pd.DataFrame(columns=["pais", "gasto", "leads"])
        return df.groupby("pais").agg(gasto=("gasto","sum"), leads=("leads","sum")).reset_index()
    except Exception as e:
        print(f"[connector] Supermetrics resumen error: {e}")
        return pd.DataFrame(columns=["pais", "gasto", "leads"])


def _desde_supermetrics_campanas(fecha_inicio: date, fecha_fin: date) -> pd.DataFrame:
    api_key = _get_api_key()
    if not api_key:
        return pd.DataFrame(columns=["pais", "campana", "campaign_id", "gasto", "costo_lead", "leads"])
    try:
        from data.supermetrics import query_campanas
        df = query_campanas(fecha_inicio, fecha_fin, api_key)
        return df if not df.empty else pd.DataFrame(columns=["pais", "campana", "campaign_id", "gasto", "costo_lead", "leads"])
    except Exception as e:
        print(f"[connector] Supermetrics campanas error: {e}")
        return pd.DataFrame(columns=["pais", "campana", "campaign_id", "gasto", "costo_lead", "leads"])


# ── API pública: primero Sheets, si falla → Supermetrics ──────────────────────

def get_resumen_por_pais(fecha_inicio: date, fecha_fin: date) -> pd.DataFrame:
    df = _leer_resumen_sheets(fecha_inicio, fecha_fin)
    if not df.empty:
        return df
    # Sheets vacío o sin datos para este rango → intentar Supermetrics
    return _desde_supermetrics_resumen(fecha_inicio, fecha_fin)


def get_campanas(fecha_inicio: date, fecha_fin: date) -> pd.DataFrame:
    df = _leer_campanas_sheets(fecha_inicio, fecha_fin)
    if not df.empty:
        return df
    return _desde_supermetrics_campanas(fecha_inicio, fecha_fin)

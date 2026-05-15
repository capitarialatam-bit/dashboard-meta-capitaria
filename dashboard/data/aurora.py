import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

SHEET_ID   = st.secrets.get("GSHEET_ID", "")
SHEET_NAME = "leads_nuevos"
SCOPES     = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]
UTM_META = {"display", "bau-display"}


def _client():
    creds = Credentials.from_service_account_info(
        dict(st.secrets["gcp_service_account"]), scopes=SCOPES
    )
    return gspread.authorize(creds)


def _get_or_create_sheet():
    gc = _client()
    wb = gc.open_by_key(SHEET_ID)
    try:
        return wb.worksheet(SHEET_NAME)
    except gspread.WorksheetNotFound:
        ws = wb.add_worksheet(title=SHEET_NAME, rows=10000, cols=6)
        ws.append_row(["created_at", "country", "utm_medium",
                       "utm_campaign", "diccionario_bb", "leads_nuevos"])
        return ws


def cargar_excel(file) -> tuple[int, str]:
    """Lee el Excel, filtra filas Meta, sobreescribe el Google Sheet.
    Retorna (total_filas, mensaje)."""
    try:
        df = pd.read_excel(file, sheet_name="Resumen Leads Mktg")
    except Exception as e:
        return 0, f"Error leyendo Excel: {e}"

    df.columns = [c.strip() for c in df.columns]
    df = df.rename(columns={
        "Leads Nuevos":  "leads_nuevos",
        "Diccionario BB": "diccionario_bb",
    })

    required = {"created_at", "country", "utm_medium", "utm_campaign",
                "leads_nuevos", "diccionario_bb"}
    missing = required - set(df.columns)
    if missing:
        return 0, f"Columnas faltantes en el Excel: {missing}"

    df = df[df["utm_medium"].str.lower().isin(UTM_META)].copy()
    df["created_at"]   = pd.to_datetime(df["created_at"]).dt.strftime("%Y-%m-%d")
    df["leads_nuevos"] = pd.to_numeric(df["leads_nuevos"], errors="coerce").fillna(0).astype(int)
    df["country"]      = df["country"].str.strip()
    df["utm_medium"]   = df["utm_medium"].str.lower().str.strip()
    df = df[["created_at", "country", "utm_medium",
             "utm_campaign", "diccionario_bb", "leads_nuevos"]]

    ws = _get_or_create_sheet()
    ws.clear()
    header = ["created_at", "country", "utm_medium",
              "utm_campaign", "diccionario_bb", "leads_nuevos"]
    rows = [header] + df.values.tolist()
    ws.update(rows, value_input_option="RAW")

    return len(df), f"✅ {len(df)} registros cargados correctamente."


def leer_leads_nuevos(fecha_inicio, fecha_fin) -> pd.DataFrame:
    """Lee el Google Sheet y retorna leads nuevos agrupados por fecha y país."""
    try:
        ws = _get_or_create_sheet()
        data = ws.get_all_records()
        if not data:
            return pd.DataFrame()
        df = pd.DataFrame(data)
        df["created_at"]   = pd.to_datetime(df["created_at"], errors="coerce").dt.date
        df["leads_nuevos"] = pd.to_numeric(df["leads_nuevos"], errors="coerce").fillna(0).astype(int)
        df = df[(df["created_at"] >= fecha_inicio) & (df["created_at"] <= fecha_fin)]
        return df
    except Exception:
        return pd.DataFrame()

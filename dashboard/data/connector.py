import os
import pandas as pd
import streamlit as st
from datetime import date, datetime, timedelta
from dotenv import load_dotenv
import gspread
from google.oauth2.service_account import Credentials

load_dotenv()

SHEET_ID = os.getenv("GOOGLE_SHEET_ID", "")
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


def _get_api_key() -> str:
    key = os.getenv("SUPERMETRICS_API_KEY", "")
    if not key:
        try:
            key = st.secrets.get("SUPERMETRICS_API_KEY", "")
        except Exception:
            pass
    return key


def _sheets_client():
    """Conectar a Google Sheets."""
    try:
        creds = Credentials.from_service_account_info(
            dict(st.secrets["gcp_service_account"]), scopes=SCOPES
        )
        return gspread.authorize(creds)
    except Exception as e:
        print(f"[sheets] Error al conectar: {e}")
        return None


def _get_or_create_worksheet(sheet_name: str):
    """Obtener o crear pestaña en Google Sheets."""
    if not SHEET_ID:
        return None
    try:
        gc = _sheets_client()
        if not gc:
            return None
        wb = gc.open_by_key(SHEET_ID)
        try:
            return wb.worksheet(sheet_name)
        except gspread.WorksheetNotFound:
            return wb.add_worksheet(title=sheet_name, rows=5000, cols=10)
    except Exception as e:
        print(f"[sheets] Error obteniendo pestaña {sheet_name}: {e}")
        return None


def _save_to_sheets(df: pd.DataFrame, sheet_name: str):
    """Guardar DataFrame en Google Sheets."""
    if df.empty or not SHEET_ID:
        return False
    try:
        ws = _get_or_create_worksheet(sheet_name)
        if not ws:
            return False
        ws.clear()
        rows = [df.columns.tolist()] + df.values.tolist()
        ws.append_rows(rows)
        print(f"[sheets] Guardados {len(df)} registros en {sheet_name}")
        return True
    except Exception as e:
        print(f"[sheets] Error guardando en {sheet_name}: {e}")
        return False


def _load_from_sheets(sheet_name: str) -> tuple[pd.DataFrame, str]:
    """Cargar datos desde Google Sheets. Retorna (DataFrame, timestamp_ultima_actualizacion)."""
    if not SHEET_ID:
        return pd.DataFrame(), ""
    try:
        ws = _get_or_create_worksheet(sheet_name)
        if not ws:
            return pd.DataFrame(), ""
        data = ws.get_all_values()
        if not data or len(data) < 2:
            return pd.DataFrame(), ""

        df = pd.DataFrame(data[1:], columns=data[0])

        # Obtener última actualización de la primera fila (la más reciente está abajo)
        if "updated_at" in df.columns:
            last_update = df.iloc[-1]["updated_at"] if len(df) > 0 else ""
            return df, last_update

        return df, ""
    except Exception as e:
        print(f"[sheets] Error cargando de {sheet_name}: {e}")
        return pd.DataFrame(), ""


def _is_data_stale(timestamp_str: str, hours: int = 24) -> bool:
    """Verificar si los datos tienen más de X horas."""
    if not timestamp_str:
        return True
    try:
        last_update = datetime.fromisoformat(timestamp_str)
        return datetime.now() - last_update > timedelta(hours=hours)
    except Exception:
        return True


def _append_to_sheets(df: pd.DataFrame, sheet_name: str):
    """Agregar filas a Google Sheets (append, sin clear). Agrega timestamp."""
    if df.empty or not SHEET_ID:
        return False
    try:
        ws = _get_or_create_worksheet(sheet_name)
        if not ws:
            return False

        # Agregar columna de timestamp si no existe
        if "updated_at" not in df.columns:
            df = df.copy()
            df.insert(0, "updated_at", datetime.now().isoformat())

        # Append rows (sin limpiar histórico)
        rows = df.values.tolist()
        ws.append_rows(rows)
        print(f"[sheets] Agregados {len(df)} registros a {sheet_name}")
        return True
    except Exception as e:
        print(f"[sheets] Error agregando a {sheet_name}: {e}")
        return False


@st.cache_data(ttl=300, show_spinner=False)
def _query_supermetrics(fecha_inicio: date, fecha_fin: date) -> pd.DataFrame:
    """
    UNA sola llamada a Supermetrics por sesión (cacheada 5 min).
    Devuelve el DataFrame base con todas las columnas.
    Tanto get_resumen_por_pais como get_campanas consumen este cache.
    """
    api_key = _get_api_key()
    if not api_key:
        print("❌ API KEY no encontrada en env vars ni en secrets")
        return pd.DataFrame()
    try:
        from data.supermetrics import _query_base
        result = _query_base(fecha_inicio, fecha_fin, api_key)
        if result.empty:
            print(f"⚠️ Sin datos para {fecha_inicio} a {fecha_fin}")
        return result
    except Exception as e:
        print(f"[connector] Supermetrics error: {e}")
        return pd.DataFrame()


def get_resumen_por_pais(fecha_inicio: date, fecha_fin: date) -> pd.DataFrame:
    """Gasto y leads por país. Refrescar si datos > 24h. Respaldo diario en Sheets."""
    sheet_name = "Resumen_Diario"
    hoy = date.today()

    print(f"[get_resumen] INICIO: fecha_fin={fecha_fin}, hoy={hoy}, son iguales={fecha_fin == hoy}")

    # Cargar de Sheets
    df_sheets, last_update = _load_from_sheets(sheet_name)

    # Si hay datos y son frescos (< 24h) Y corresponden a la fecha solicitada, retornar
    if not df_sheets.empty and not _is_data_stale(last_update, hours=24):
        # Validar que los datos corresponden al rango solicitado (Sheets guarda data del día)
        # Si el usuario pide rango específico (ej: 26/05 a 26/05) y es hoy, validar
        if fecha_fin == hoy:  # Si pide hoy o un rango que incluye hoy
            print(f"[get_resumen] Datos frescos de Sheets ({last_update}) - USANDO CACHE")
            df_sheets = df_sheets.drop(columns=["updated_at"], errors="ignore")
            df_sheets["gasto"] = pd.to_numeric(df_sheets["gasto"], errors="coerce").fillna(0)
            df_sheets["leads"] = pd.to_numeric(df_sheets["leads"], errors="coerce").fillna(0)
            return df_sheets
        else:
            print(f"[get_resumen] Sheets tiene data de hoy pero usuario pide {fecha_fin} - IGNORANDO CACHE")

    # Datos ausentes, stale, o no corresponden a fecha solicitada → refrescar desde Supermetrics
    print(f"[get_resumen] Refrescando desde Supermetrics para {fecha_inicio} a {fecha_fin}...")
    df = _query_supermetrics(fecha_inicio, fecha_fin)
    if df.empty:
        return pd.DataFrame(columns=["pais", "gasto", "leads"])

    resultado = (df.groupby("pais")
                  .agg(gasto=("gasto", "sum"), leads=("leads", "sum"))
                  .reset_index())

    # Guardar en Sheets SOLO si es data de hoy (para caché diario)
    if fecha_fin == date.today():
        resultado["updated_at"] = datetime.now().isoformat()
        _save_to_sheets(resultado, sheet_name)

    # Retornar sin timestamp
    return resultado[["pais", "gasto", "leads"]]


def get_campanas(fecha_inicio: date, fecha_fin: date) -> pd.DataFrame:
    """Desglose por campaña. Refrescar si datos > 24h. Respaldo diario en Sheets."""
    sheet_name = "Campanas_Diario"

    # Cargar de Sheets
    df_sheets, last_update = _load_from_sheets(sheet_name)

    # Si hay datos y son frescos (< 24h) Y corresponden a la fecha solicitada, retornar
    if not df_sheets.empty and not _is_data_stale(last_update, hours=24):
        # Validar que los datos corresponden al rango solicitado (Sheets guarda data del día)
        if fecha_fin == date.today():  # Si pide hoy o un rango que incluye hoy
            print(f"[get_campanas] Datos frescos de Sheets ({last_update})")
            df_sheets = df_sheets.drop(columns=["updated_at"], errors="ignore")
            for col in ["gasto", "costo_lead", "leads"]:
                df_sheets[col] = pd.to_numeric(df_sheets[col], errors="coerce").fillna(0)
            return df_sheets

    # Datos ausentes, stale, o no corresponden a fecha solicitada → refrescar desde Supermetrics
    print(f"[get_campanas] Refrescando desde Supermetrics para {fecha_inicio} a {fecha_fin}...")
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
    resultado = resultado[["pais", "campana", "campaign_id", "gasto", "costo_lead", "leads"]]

    # Guardar en Sheets SOLO si es data de hoy (para caché diario)
    if fecha_fin == date.today():
        resultado["updated_at"] = datetime.now().isoformat()
        _save_to_sheets(resultado, sheet_name)

    # Retornar sin timestamp
    return resultado[["pais", "campana", "campaign_id", "gasto", "costo_lead", "leads"]]

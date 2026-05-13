import os
import pandas as pd
from datetime import date
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("SUPERMETRICS_API_KEY", "")


def _mock_resumen(fecha_fin: date) -> pd.DataFrame:
    # EP campaigns excluded from these totals (same logic as real data)
    return pd.DataFrame([
        {"pais": "Chile",   "fecha": fecha_fin, "gasto": 341.38, "leads": 25},
        {"pais": "Mexico",  "fecha": fecha_fin, "gasto": 207.10, "leads": 32},
        {"pais": "Uruguay", "fecha": fecha_fin, "gasto": 25.97,  "leads": 3},
        {"pais": "Peru",    "fecha": fecha_fin, "gasto": 7.01,   "leads": 0},
    ])


def _mock_campanas() -> pd.DataFrame:
    return pd.DataFrame([
        {"pais": "Chile",  "campana": "C004L-MC001", "gasto": 838.73, "costo_lead": 11.65, "leads": 74},
        {"pais": "Chile",  "campana": "C007L-EB001", "gasto": 614.59, "costo_lead": 17.07, "leads": 36},
        {"pais": "Mexico", "campana": "C029L-MC005", "gasto": 72.36,  "costo_lead": 2.26,  "leads": 32},
    ])


def get_meta_ads(fecha_inicio: date, fecha_fin: date) -> pd.DataFrame:
    if not API_KEY:
        return _mock_resumen(fecha_fin)
    try:
        from data.supermetrics import query_meta_ads
        df = query_meta_ads(fecha_inicio, fecha_fin)
        return df if not df.empty else _mock_resumen(fecha_fin)
    except Exception as e:
        print(f"[connector] Error: {e}")
        return _mock_resumen(fecha_fin)


def get_resumen_por_pais(fecha_inicio: date, fecha_fin: date) -> pd.DataFrame:
    df = get_meta_ads(fecha_inicio, fecha_fin)
    return (
        df.groupby("pais")
        .agg(gasto=("gasto", "sum"), leads=("leads", "sum"))
        .reset_index()
    )


def get_campanas(fecha_inicio: date, fecha_fin: date) -> pd.DataFrame:
    if not API_KEY:
        return _mock_campanas()
    try:
        from data.supermetrics import query_campanas
        df = query_campanas(fecha_inicio, fecha_fin)
        return df if not df.empty else _mock_campanas()
    except Exception as e:
        print(f"[connector] Error campañas: {e}")
        return _mock_campanas()

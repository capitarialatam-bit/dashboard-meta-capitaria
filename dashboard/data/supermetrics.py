import os
import re
import time
import requests
import pandas as pd
from datetime import date
from dotenv import load_dotenv

load_dotenv()

MCP_BASE = "https://mcp.supermetrics.com/mcp"
API_KEY = os.getenv("SUPERMETRICS_API_KEY", "")
META_ACCOUNT = "act_336792180552844"  # Capitaria NEW - MKT MIX

PAIS_MAP = {
    "CL": "Chile", "Chile": "Chile",
    "MX": "Mexico", "Mexico": "Mexico",
    "UY": "Uruguay", "Uruguay": "Uruguay",
    "PE": "Peru", "Peru": "Peru",
}


def detectar_pais(campana: str, adset: str = "") -> str:
    """
    Detecta el país según la nomenclatura de campaña de Capitaria.
    Replica la lógica CASE del campo calculado de Looker Studio.
    """
    c = str(campana)
    a = str(adset)

    if re.match(r'^[A-Z][0-9]+L-', c):
        return "Chile"
    if re.match(r'^[A-Z][0-9]+X-', c):
        return "Mexico"
    if re.match(r'^[A-Z][0-9]+Y-', c):
        return "Uruguay"
    if re.match(r'^[A-Z][0-9]+E-', c):
        return "Peru"
    if re.match(r'^L[0-9]+T-', c):
        if "CL" in a.upper():
            return "Chile"
        if "MX" in a.upper():
            return "Mexico"
        if "UY" in a.upper():
            return "Uruguay"
        if "PE" in a.upper():
            return "Peru"
    if "chile" in c.lower():
        return "Chile"
    if "mexico" in c.lower() or "méxico" in c.lower():
        return "Mexico"
    if "peru" in c.lower() or "perú" in c.lower():
        return "Peru"
    if "uruguay" in c.lower():
        return "Uruguay"
    # Prefijos cortos: CL-, MX-, UY-, PE-
    if re.match(r'^CL[-_]', c):
        return "Chile"
    if re.match(r'^MX[-_]', c):
        return "Mexico"
    if re.match(r'^UY[-_]', c):
        return "Uruguay"
    if re.match(r'^PE[-_]', c):
        return "Peru"

    return "Sin identificar"


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def _post(tool: str, body: dict) -> dict:
    url = f"{MCP_BASE}/{tool}"
    resp = requests.post(url, json=body, headers=_headers(), timeout=60)
    resp.raise_for_status()
    return resp.json()


def _wait_result(schedule_id: str, max_tries: int = 30) -> list:
    for _ in range(max_tries):
        time.sleep(2)
        result = _post("get_async_query_results", {"schedule_id": schedule_id})
        data = result.get("data", {})
        if data.get("status") == "completed" or data.get("success"):
            rows = data.get("data", [])
            if rows:
                return rows
    return []


def _run_query(fields: list, fecha_inicio: date, fecha_fin: date) -> pd.DataFrame:
    payload = {
        "ds_id": "FA",
        "ds_accounts": META_ACCOUNT,
        "date_range_type": "custom",
        "start_date": fecha_inicio.strftime("%Y-%m-%d"),
        "end_date": fecha_fin.strftime("%Y-%m-%d"),
        "fields": fields,
        "max_rows": 5000,
    }
    result = _post("data_query", payload)
    schedule_id = result.get("data", {}).get("schedule_id")
    if not schedule_id:
        return pd.DataFrame()
    rows = _wait_result(schedule_id)
    if not rows or len(rows) < 2:
        return pd.DataFrame()
    return pd.DataFrame(rows[1:], columns=rows[0])


def query_meta_ads(fecha_inicio: date, fecha_fin: date) -> pd.DataFrame:
    """Resumen por país usando nomenclatura de campañas."""
    df = _run_query(
        ["Date", "adcampaign_name", "adset_name", "cost_usd", "onsite_conversion.lead_grouped"],
        fecha_inicio, fecha_fin,
    )
    if df.empty:
        return df

    df = df.rename(columns={
        "Campaign name": "campana",
        "Ad set name": "adset",
        "Cost (USD)": "gasto",
        "On-Facebook leads": "leads",
    })
    df["fecha"] = pd.to_datetime(df["Date"]).dt.date
    df["gasto"] = pd.to_numeric(df["gasto"], errors="coerce").fillna(0)
    df["leads"] = pd.to_numeric(df["leads"], errors="coerce").fillna(0).astype(int)
    df["pais"] = df.apply(lambda r: detectar_pais(r["campana"], r["adset"]), axis=1)
    df = df[~df["campana"].str.upper().str.contains("-EP", na=False)]
    return df[["fecha", "pais", "gasto", "leads"]]


def query_campanas(fecha_inicio: date, fecha_fin: date) -> pd.DataFrame:
    """Desglose por campaña con país detectado por nomenclatura."""
    df = _run_query(
        ["adcampaign_name", "adset_name", "cost_usd", "onsite_conversion.lead_grouped"],
        fecha_inicio, fecha_fin,
    )
    if df.empty:
        return df

    df = df.rename(columns={
        "Campaign name": "campana",
        "Ad set name": "adset",
        "Cost (USD)": "gasto",
        "On-Facebook leads": "leads",
    })
    df["gasto"]  = pd.to_numeric(df["gasto"],  errors="coerce").fillna(0)
    df["leads"]  = pd.to_numeric(df["leads"],  errors="coerce").fillna(0).astype(int)
    df["pais"]   = df.apply(lambda r: detectar_pais(r["campana"], r["adset"]), axis=1)

    resultado = (
        df.groupby(["pais", "campana"])
        .agg(gasto=("gasto", "sum"), leads=("leads", "sum"))
        .reset_index()
    )
    resultado["costo_lead"] = resultado.apply(
        lambda r: r["gasto"] / r["leads"] if r["leads"] > 0 else 0, axis=1
    )
    return resultado[["pais", "campana", "gasto", "costo_lead", "leads"]]


def query_rendimiento(fecha_inicio: date, fecha_fin: date) -> pd.DataFrame:
    """Rendimiento por anuncio con creativo, métricas y formato condicional."""
    df = _run_query(
        ["adcampaign_name", "adset_name", "ad_name",
         "creative_thumbnail_url", "video_asset_thumbnail_url",
         "cost_usd", "onsite_conversion.lead_grouped",
         "CPM", "unique_link_CTR", "Frequency", "impressions", "reach"],
        fecha_inicio, fecha_fin,
    )
    if df.empty:
        return df

    df = df.rename(columns={
        "Campaign name":               "campana",
        "Ad set name":                 "adset",
        "Ad name":                     "anuncio",
        "Ad creative thumbnail URL":   "thumbnail",
        "Video asset thumbnail URL":   "thumbnail_video",
        "Cost (USD)":                  "gasto",
        "On-Facebook leads":           "leads",
        "CPM (cost per 1000 impressions)": "cpm",
        "Unique CTR (link click-through rate)": "ctr",
        "Frequency":                   "frecuencia",
        "Impressions":                 "impresiones",
        "Reach":                       "alcance",
    })

    for col in ("thumbnail", "thumbnail_video"):
        if col not in df.columns:
            df[col] = ""

    df["gasto"]      = pd.to_numeric(df["gasto"],      errors="coerce").fillna(0)
    df["leads"]      = pd.to_numeric(df["leads"],      errors="coerce").fillna(0).astype(int)
    df["cpm"]        = pd.to_numeric(df["cpm"],        errors="coerce").fillna(0)
    df["ctr"]        = pd.to_numeric(df["ctr"],        errors="coerce").fillna(0)
    df["frecuencia"] = pd.to_numeric(df["frecuencia"], errors="coerce").fillna(0)
    df["impresiones"]= pd.to_numeric(df["impresiones"],errors="coerce").fillna(0)
    df["alcance"]    = pd.to_numeric(df["alcance"],    errors="coerce").fillna(0)
    df["pais"]       = df.apply(lambda r: detectar_pais(r["campana"], r["adset"]), axis=1)
    df["imagen"]     = df.apply(
        lambda r: r["thumbnail"] if str(r["thumbnail"]).startswith("http")
                  else r["thumbnail_video"], axis=1
    )
    # CTR: si viene como decimal (0.015) lo convertimos a porcentaje (1.5)
    if df["ctr"].max() <= 1:
        df["ctr"] = df["ctr"] * 100

    resultado = (
        df.groupby(["pais", "campana", "anuncio", "imagen"])
        .agg(
            gasto      =("gasto",       "sum"),
            leads      =("leads",       "sum"),
            impresiones=("impresiones", "sum"),
            alcance    =("alcance",     "sum"),
        )
        .reset_index()
    )
    resultado["costo_lead"] = resultado.apply(
        lambda r: r["gasto"] / r["leads"] if r["leads"] > 0 else 0, axis=1
    )
    resultado["cpm"] = resultado.apply(
        lambda r: (r["gasto"] / r["impresiones"]) * 1000 if r["impresiones"] > 0 else 0, axis=1
    )
    resultado["ctr"] = resultado.apply(
        lambda r: (r["leads"] / r["impresiones"]) * 100 if r["impresiones"] > 0 else 0, axis=1
    )
    resultado["frecuencia"] = resultado.apply(
        lambda r: r["impresiones"] / r["alcance"] if r["alcance"] > 0 else 0, axis=1
    )
    return resultado[["pais", "campana", "anuncio", "imagen", "leads", "costo_lead", "cpm", "ctr", "frecuencia"]]

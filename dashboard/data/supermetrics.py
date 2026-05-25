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
    cu = c.upper()
    au = a.upper()

    # Formato estándar: [Letra][Número][País]-...
    if re.match(r'^[A-Z][0-9]+L-', c):
        return "Chile"
    if re.match(r'^[A-Z][0-9]+X-', c):
        return "Mexico"
    if re.match(r'^[A-Z][0-9]+Y-', c):
        return "Uruguay"
    if re.match(r'^[A-Z][0-9]+E-', c):
        return "Peru"
    if re.match(r'^L[0-9]+T-', c):
        if "CL" in au:
            return "Chile"
        if "MX" in au:
            return "Mexico"
        if "UY" in au:
            return "Uruguay"
        if "PE" in au:
            return "Peru"

    # Nombre completo del país
    if "chile" in c.lower():
        return "Chile"
    if "mexico" in c.lower() or "méxico" in c.lower():
        return "Mexico"
    if "peru" in c.lower() or "perú" in c.lower():
        return "Peru"
    if "uruguay" in c.lower():
        return "Uruguay"

    # Prefijo corto (case-insensitive): CL-, MX-, UY-, PE-
    if re.match(r'^CL[-_]', cu):
        return "Chile"
    if re.match(r'^MX[-_]', cu):
        return "Mexico"
    if re.match(r'^UY[-_]', cu):
        return "Uruguay"
    if re.match(r'^PE[-_]', cu):
        return "Peru"

    # Código de país en medio del nombre: -CL-, -CL_fin, etc.
    if re.search(r'[-_]CL[-_]|[-_]CL$', cu):
        return "Chile"
    if re.search(r'[-_]MX[-_]|[-_]MX$', cu):
        return "Mexico"
    if re.search(r'[-_]UY[-_]|[-_]UY$', cu):
        return "Uruguay"
    if re.search(r'[-_]PE[-_]|[-_]PE$', cu):
        return "Peru"

    # Buscar en el adset si la campaña no tiene indicador
    if re.search(r'[-_]CL[-_\d]|[-_]CL$|^CL[-_]', au):
        return "Chile"
    if re.search(r'[-_]MX[-_\d]|[-_]MX$|^MX[-_]', au):
        return "Mexico"
    if re.search(r'[-_]UY[-_\d]|[-_]UY$|^UY[-_]', au):
        return "Uruguay"
    if re.search(r'[-_]PE[-_\d]|[-_]PE$|^PE[-_]', au):
        return "Peru"

    return "Sin identificar"


def _headers(api_key: str) -> dict:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def _post(tool: str, body: dict, api_key: str) -> dict:
    url = f"{MCP_BASE}/{tool}"
    resp = requests.post(url, json=body, headers=_headers(api_key), timeout=60)
    resp.raise_for_status()
    return resp.json()


def _wait_result(schedule_id: str, api_key: str, max_tries: int = 30) -> list:
    for _ in range(max_tries):
        time.sleep(2)
        result = _post("get_async_query_results", {"schedule_id": schedule_id}, api_key)
        data = result.get("data", {})
        if data.get("status") == "completed" or data.get("success"):
            rows = data.get("data", [])
            if rows:
                return rows
    return []


def _run_query(fields: list, fecha_inicio: date, fecha_fin: date, api_key: str) -> pd.DataFrame:
    payload = {
        "ds_id": "FA",
        "ds_accounts": META_ACCOUNT,
        "date_range_type": "custom",
        "start_date": fecha_inicio.strftime("%Y-%m-%d"),
        "end_date": fecha_fin.strftime("%Y-%m-%d"),
        "fields": fields,
        "max_rows": 5000,
    }
    result = _post("data_query", payload, api_key)
    schedule_id = result.get("data", {}).get("schedule_id")
    if not schedule_id:
        return pd.DataFrame()
    rows = _wait_result(schedule_id, api_key)
    if not rows or len(rows) < 2:
        return pd.DataFrame()
    return pd.DataFrame(rows[1:], columns=rows[0])


def query_meta_ads(fecha_inicio: date, fecha_fin: date, api_key: str = "") -> pd.DataFrame:
    """Resumen por país usando nomenclatura de campañas."""
    df = _run_query(
        ["Date", "adcampaign_name", "adset_name", "cost_usd",
         "onsite_conversion.lead_grouped", "offsite_conversions_fb_pixel_lead"],
        fecha_inicio, fecha_fin, api_key,
    )
    if df.empty:
        return df

    df = df.rename(columns={
        "Campaign name": "campana",
        "Ad set name": "adset",
        "Cost (USD)": "gasto",
        "On-Facebook leads": "leads_form",
        "Website leads": "leads_web",
    })
    df["fecha"] = pd.to_datetime(df["Date"]).dt.date
    df["gasto"]      = pd.to_numeric(df["gasto"],      errors="coerce").fillna(0)
    df["leads_form"] = pd.to_numeric(df["leads_form"], errors="coerce").fillna(0)
    df["leads_web"]  = pd.to_numeric(df["leads_web"],  errors="coerce").fillna(0)
    df["leads"]      = (df["leads_form"] + df["leads_web"]).astype(int)
    df["pais"] = df.apply(lambda r: detectar_pais(r["campana"], r["adset"]), axis=1)
    df = df[~df["campana"].str.upper().str.contains("-EP", na=False)]
    return df[["fecha", "pais", "gasto", "leads"]]


def query_campanas(fecha_inicio: date, fecha_fin: date, api_key: str = "") -> pd.DataFrame:
    """Desglose por campaña con país detectado por nomenclatura."""
    df = _run_query(
        ["adcampaign_id", "adcampaign_name", "adset_name", "cost_usd",
         "onsite_conversion.lead_grouped", "offsite_conversions_fb_pixel_lead"],
        fecha_inicio, fecha_fin, api_key,
    )
    if df.empty:
        return df

    df = df.rename(columns={
        "Campaign ID":      "campaign_id",
        "Campaign name":    "campana",
        "Ad set name":      "adset",
        "Cost (USD)":       "gasto",
        "On-Facebook leads": "leads_form",
        "Website leads":    "leads_web",
    })
    df["gasto"]       = pd.to_numeric(df["gasto"],      errors="coerce").fillna(0)
    df["leads_form"]  = pd.to_numeric(df["leads_form"], errors="coerce").fillna(0)
    df["leads_web"]   = pd.to_numeric(df["leads_web"],  errors="coerce").fillna(0)
    df["leads"]       = (df["leads_form"] + df["leads_web"]).astype(int)
    df["pais"]        = df.apply(lambda r: detectar_pais(r["campana"], r["adset"]), axis=1)
    df["campaign_id"] = df["campaign_id"].astype(str)

    resultado = (
        df.groupby(["pais", "campana", "campaign_id"])
        .agg(gasto=("gasto", "sum"), leads=("leads", "sum"))
        .reset_index()
    )
    resultado["costo_lead"] = resultado.apply(
        lambda r: r["gasto"] / r["leads"] if r["leads"] > 0 else 0, axis=1
    )
    return resultado[["pais", "campana", "campaign_id", "gasto", "costo_lead", "leads"]]


def query_rendimiento(fecha_inicio: date, fecha_fin: date) -> pd.DataFrame:
    """Rendimiento por anuncio con creativo, métricas y formato condicional."""
    df = _run_query(
        ["adcampaign_name", "adset_name", "ad_name",
         "creative_thumbnail_url", "video_asset_thumbnail_url",
         "cost_usd", "onsite_conversion.lead_grouped", "offsite_conversions_fb_pixel_lead",
         "impressions", "reach", "unique_link_CTR", "unique_outbound_CTR"],
        fecha_inicio, fecha_fin,
    )
    if df.empty:
        return df

    df = df.rename(columns={
        "Campaign name":             "campana",
        "Ad set name":               "adset",
        "Ad name":                   "anuncio",
        "Ad creative thumbnail URL": "thumbnail",
        "Video asset thumbnail URL": "thumbnail_video",
        "Cost (USD)":                "gasto",
        "On-Facebook leads":         "leads_form",
        "Website leads":             "leads_web",
        "Impressions":               "impresiones",
        "Reach":                     "alcance",
        "Unique CTR (link click-through rate)":     "ctr_link",
        "Unique outbound CTR":                       "ctr_outbound",
    })

    for col in ("thumbnail", "thumbnail_video", "ctr_link", "ctr_outbound"):
        if col not in df.columns:
            df[col] = "" if col in ("thumbnail", "thumbnail_video") else 0

    df["gasto"]      = pd.to_numeric(df["gasto"],      errors="coerce").fillna(0)
    df["leads_form"] = pd.to_numeric(df["leads_form"], errors="coerce").fillna(0)
    df["leads_web"]  = pd.to_numeric(df["leads_web"] if "leads_web" in df.columns else 0, errors="coerce").fillna(0)
    df["leads"]      = (df["leads_form"] + df["leads_web"]).astype(int)
    df["impresiones"]  = pd.to_numeric(df["impresiones"],  errors="coerce").fillna(0)
    df["alcance"]      = pd.to_numeric(df["alcance"],      errors="coerce").fillna(0)
    df["ctr_link"]     = pd.to_numeric(df["ctr_link"],     errors="coerce").fillna(0)
    df["ctr_outbound"] = pd.to_numeric(df["ctr_outbound"], errors="coerce").fillna(0)
    # Usar el mayor entre link CTR y outbound CTR; siempre viene como decimal → * 100
    df["ctr_raw"] = df[["ctr_link", "ctr_outbound"]].max(axis=1) * 100
    # Promedio ponderado por impresiones para el agrupado
    df["ctr_pond"] = df["ctr_raw"] * df["impresiones"]
    df["pais"]          = df.apply(lambda r: detectar_pais(r["campana"], r["adset"]), axis=1)
    df["imagen"]        = df.apply(
        lambda r: r["thumbnail"] if str(r["thumbnail"]).startswith("http")
                  else r["thumbnail_video"], axis=1
    )

    def _primera_imagen(series):
        for v in series:
            if str(v).startswith("http"):
                return v
        return ""

    agg = (
        df.groupby(["pais", "campana", "adset", "anuncio"])
        .agg(
            gasto      =("gasto",       "sum"),
            leads      =("leads",       "sum"),
            impresiones=("impresiones", "sum"),
            alcance    =("alcance",     "sum"),
            ctr_pond   =("ctr_pond",    "sum"),
            imagen     =("imagen",      _primera_imagen),
        )
        .reset_index()
    )
    agg["costo_lead"] = agg.apply(
        lambda r: r["gasto"] / r["leads"] if r["leads"] > 0 else 0, axis=1
    )
    agg["cpm"] = agg.apply(
        lambda r: (r["gasto"] / r["impresiones"]) * 1000 if r["impresiones"] > 0 else 0, axis=1
    )
    agg["ctr"] = agg.apply(
        lambda r: r["ctr_pond"] / r["impresiones"] if r["impresiones"] > 0 else 0, axis=1
    )
    agg["frecuencia"] = agg.apply(
        lambda r: r["impresiones"] / r["alcance"] if r["alcance"] > 0 else 0, axis=1
    )
    # Retornar columnas numéricas necesarias para agregar en el componente
    return agg[["pais", "campana", "adset", "anuncio", "imagen",
                "leads", "gasto", "impresiones", "alcance", "ctr_pond",
                "costo_lead", "cpm", "ctr", "frecuencia"]]

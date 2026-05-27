"""
Script local: consulta Supermetrics y guarda los datos en Google Sheets.
Correr cada mañana o cuando necesites actualizar el dashboard.

Uso:
    python dashboard/data/sync_meta_to_sheets.py
    python dashboard/data/sync_meta_to_sheets.py --dias 7
    python dashboard/data/sync_meta_to_sheets.py --desde 2026-05-01 --hasta 2026-05-27
"""
import sys
import os
import json
import argparse
import math
from datetime import date, timedelta
sys.stdout.reconfigure(encoding='utf-8')

# ── Configuración ─────────────────────────────────────────────────────────────
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

SHEET_ID    = "1cOz6ZfsKHl5JRvHpNNlsgENU0K14wtHwZElh75mC32I"
SCOPES      = ["https://www.googleapis.com/auth/spreadsheets",
               "https://www.googleapis.com/auth/drive"]
CREDS_FILE  = os.path.join(os.path.dirname(__file__), '..', 'credentials',
                            'google_service_account.json')
TAB_RESUMEN  = "meta_resumen"
TAB_CAMPANAS = "meta_campanas"


# ── Google Sheets ──────────────────────────────────────────────────────────────
def _gc():
    creds = Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
    return gspread.authorize(creds)

def _get_or_create(wb, nombre, cols):
    try:
        ws = wb.worksheet(nombre)
    except gspread.WorksheetNotFound:
        ws = wb.add_worksheet(title=nombre, rows=50000, cols=len(cols))
        ws.append_row(cols)
    return ws

def _safe(v):
    if v is None: return ""
    try:
        if isinstance(v, float) and math.isnan(v): return ""
    except: pass
    if hasattr(v, 'item'): return v.item()
    return str(v) if not isinstance(v, (int, float, str, bool)) else v

def escribir_sheet(ws, df, cols):
    ws.clear()
    rows = [cols] + [[_safe(r[c]) for c in cols] for _, r in df.iterrows()]
    ws.update(rows, value_input_option="RAW")
    print(f"  ✓ '{ws.title}': {len(rows)-1} filas escritas")


# ── Supermetrics ───────────────────────────────────────────────────────────────
def fetch_supermetrics(fecha_inicio: date, fecha_fin: date):
    from data.supermetrics import query_meta_ads, query_campanas
    api_key = os.getenv("SUPERMETRICS_API_KEY", "")
    if not api_key:
        raise ValueError("SUPERMETRICS_API_KEY no encontrada en .env")

    print(f"Consultando Supermetrics: {fecha_inicio} → {fecha_fin}")

    print("  Descargando resumen por país...")
    df_resumen = query_meta_ads(fecha_inicio, fecha_fin, api_key)

    print("  Descargando detalle de campañas...")
    df_campanas = query_campanas(fecha_inicio, fecha_fin, api_key)

    return df_resumen, df_campanas


# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dias',   type=int, default=7,
                        help='Últimos N días (default: 7)')
    parser.add_argument('--desde',  type=str, help='Fecha inicio AAAA-MM-DD')
    parser.add_argument('--hasta',  type=str, help='Fecha fin AAAA-MM-DD')
    args = parser.parse_args()

    if args.desde and args.hasta:
        fi = date.fromisoformat(args.desde)
        ff = date.fromisoformat(args.hasta)
    else:
        ff = date.today() - timedelta(days=1)   # ayer (datos completos)
        fi = ff - timedelta(days=args.dias - 1)

    print(f"\n=== Sync Meta Ads → Google Sheets ===")
    print(f"Período: {fi} → {ff}\n")

    # 1. Fetch de Supermetrics
    df_resumen, df_campanas = fetch_supermetrics(fi, ff)

    if df_resumen.empty and df_campanas.empty:
        print("❌ Supermetrics no retornó datos. Verifica fechas o API key.")
        sys.exit(1)

    # Mostrar resumen en consola
    if not df_resumen.empty:
        grp = df_resumen.groupby("pais").agg(gasto=("gasto","sum"), leads=("leads","sum")).reset_index()
        print("\nResumen por país:")
        for _, r in grp.iterrows():
            print(f"  {r['pais']:<10} ${r['gasto']:>8.2f}  {int(r['leads']):>4} leads")

    # 2. Guardar en Google Sheets
    print("\nEscribiendo en Google Sheets...")
    gc  = _gc()
    wb  = gc.open_by_key(SHEET_ID)

    if not df_resumen.empty:
        # Agregar fecha de sync
        df_resumen["fecha"] = df_resumen["fecha"].astype(str)
        ws_r = _get_or_create(wb, TAB_RESUMEN, ["fecha", "pais", "gasto", "leads"])
        escribir_sheet(ws_r, df_resumen[["fecha", "pais", "gasto", "leads"]], ["fecha", "pais", "gasto", "leads"])

    if not df_campanas.empty:
        ws_c = _get_or_create(wb, TAB_CAMPANAS,
                              ["pais", "campana", "campaign_id", "gasto", "costo_lead", "leads"])
        escribir_sheet(ws_c, df_campanas, ["pais", "campana", "campaign_id", "gasto", "costo_lead", "leads"])

    print("\n✅ Sync completado. El dashboard leerá los datos de Sheets.")
    print(f"   Sheet: https://docs.google.com/spreadsheets/d/{SHEET_ID}")


if __name__ == "__main__":
    main()

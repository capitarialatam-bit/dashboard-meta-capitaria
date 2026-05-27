import sys, json, pandas as pd, gspread
from google.oauth2.service_account import Credentials
sys.stdout.reconfigure(encoding='utf-8')

# 1. Leer Excel nuevo
df = pd.read_excel('C:/Users/AndrésArias/Downloads/Leads_Mktg_General (3).xlsx', sheet_name='Resumen Leads Mktg')
df.columns = [c.strip() for c in df.columns]
df = df.rename(columns={'Leads Nuevos': 'leads_nuevos', 'Diccionario BB': 'diccionario_bb'})
df_f = df[df['utm_medium'].str.lower().isin({'display', 'bau-display'})].copy()
print(f"Total filas Excel: {len(df)}")
print(f"Filas display+bau: {len(df_f)}")

# 2. Escribir al Sheet
SHEET_ID = '1cOz6ZfsKHl5JRvHpNNlsgENU0K14wtHwZElh75mC32I'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
creds = Credentials.from_service_account_info(
    json.load(open('C:/Users/AndrésArias/Downloads/formularios-nativos-600396fca61a.json')),
    scopes=SCOPES
)
gc = gspread.authorize(creds)
wb = gc.open_by_key(SHEET_ID)
ws = wb.worksheet('leads_nuevos')

df_f['created_at'] = pd.to_datetime(df_f['created_at']).dt.strftime('%Y-%m-%d')
df_f['leads_nuevos'] = pd.to_numeric(df_f['leads_nuevos'], errors='coerce').fillna(0).astype(int)

def safe(v):
    import math
    if v is None: return ""
    try:
        if isinstance(v, float) and math.isnan(v): return ""
    except: pass
    if hasattr(v, 'item'): return v.item()
    return str(v) if not isinstance(v, (int, float, str, bool)) else v

cols = ['created_at', 'country', 'utm_medium', 'utm_campaign', 'diccionario_bb', 'leads_nuevos']
df_f = df_f[cols]
rows = [cols] + [[safe(c) for c in row] for row in df_f.values.tolist()]

ws.clear()
ws.update(rows, value_input_option='RAW')
print(f"Escrito en Sheet: {len(rows)-1} filas")
print("OK")

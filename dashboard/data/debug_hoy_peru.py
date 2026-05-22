"""
Debug: verifica datos de Supermetrics para hoy, enfocado en Peru.
Ejecutar: python dashboard/data/debug_hoy_peru.py
"""
import sys, os, time, requests, re
sys.stdout.reconfigure(encoding='utf-8')
from dotenv import load_dotenv
from datetime import date
load_dotenv()

API_KEY      = os.getenv('SUPERMETRICS_API_KEY')
MCP_BASE     = 'https://mcp.supermetrics.com/mcp'
META_ACCOUNT = 'act_336792180552844'
from datetime import timedelta
HOY          = (date.today() - timedelta(days=1)).strftime('%Y-%m-%d')  # ayer, más confiable

print(f"API_KEY presente: {'SI' if API_KEY else 'NO ← el problema está aquí'}")
print(f"Consultando fecha: {HOY} (ayer — datos del día actual no están disponibles en Supermetrics)\n")

if not API_KEY:
    print("ERROR: SUPERMETRICS_API_KEY no encontrada en .env")
    sys.exit(1)

h = {
    'Authorization': f'Bearer {API_KEY}',
    'Content-Type': 'application/json',
    'Accept': 'application/json',
}

payload = {
    'ds_id': 'FA',
    'ds_accounts': META_ACCOUNT,
    'date_range_type': 'custom',
    'start_date': HOY,
    'end_date': HOY,
    'fields': [
        'adcampaign_name',
        'adset_name',
        'cost_usd',
        'onsite_conversion.lead_grouped',
        'offsite_conversions_fb_pixel_lead',
    ],
    'max_rows': 5000,
}

resp = requests.post(f'{MCP_BASE}/data_query', json=payload, headers=h, timeout=60)
print(f"Status HTTP: {resp.status_code}")

sid = resp.json().get('data', {}).get('schedule_id')
if not sid:
    print("ERROR: No se obtuvo schedule_id")
    print(resp.json())
    sys.exit(1)

print(f"schedule_id: {sid}")
print("Esperando resultados", end="", flush=True)

rows = []
for _ in range(40):
    time.sleep(3)
    r = requests.post(f'{MCP_BASE}/get_async_query_results',
                      json={'schedule_id': sid}, headers=h, timeout=60)
    data = r.json().get('data', {})
    if data.get('status') == 'completed' or data.get('success'):
        rows = data.get('data', [])
        print(" ✓")
        break
    print(".", end="", flush=True)
else:
    print(" TIMEOUT")
    sys.exit(1)

if not rows or len(rows) < 2:
    print("\nSupermetrics retornó VACÍO para hoy.")
    print("Posibles causas:")
    print("  - Aún no hay gasto registrado hoy")
    print("  - Las campañas no tuvieron actividad hoy")
    print("  - Supermetrics tiene delay de datos (normal: 2-4 horas)")
    sys.exit(0)

cols = rows[0]
print(f"\nColumnas: {cols}")
print(f"Total filas: {len(rows)-1}\n")

# ── Detectar país desde nombre de campaña ─────────────────────────
def detectar_pais(campana, adset=""):
    c = str(campana)
    a = str(adset)
    cu = c.upper()
    au = a.upper()

    if re.match(r'^[A-Z][0-9]+L-', c): return "Chile"
    if re.match(r'^[A-Z][0-9]+X-', c): return "Mexico"
    if re.match(r'^[A-Z][0-9]+Y-', c): return "Uruguay"
    if re.match(r'^[A-Z][0-9]+E-', c): return "Peru"

    if "chile" in c.lower():   return "Chile"
    if "mexico" in c.lower() or "méxico" in c.lower(): return "Mexico"
    if "peru" in c.lower() or "perú" in c.lower(): return "Peru"
    if "uruguay" in c.lower(): return "Uruguay"

    if re.match(r'^CL[-_]', cu): return "Chile"
    if re.match(r'^MX[-_]', cu): return "Mexico"
    if re.match(r'^UY[-_]', cu): return "Uruguay"
    if re.match(r'^PE[-_]', cu): return "Peru"

    if re.search(r'[-_]CL[-_]|[-_]CL$', cu): return "Chile"
    if re.search(r'[-_]MX[-_]|[-_]MX$', cu): return "Mexico"
    if re.search(r'[-_]UY[-_]|[-_]UY$', cu): return "Uruguay"
    if re.search(r'[-_]PE[-_]|[-_]PE$', cu): return "Peru"

    if re.search(r'[-_]CL[-_\d]|[-_]CL$|^CL[-_]', au): return "Chile"
    if re.search(r'[-_]MX[-_\d]|[-_]MX$|^MX[-_]', au): return "Mexico"
    if re.search(r'[-_]UY[-_\d]|[-_]UY$|^UY[-_]', au): return "Uruguay"
    if re.search(r'[-_]PE[-_\d]|[-_]PE$|^PE[-_]', au): return "Peru"

    return "Sin identificar"

# ── Mostrar resultados ─────────────────────────────────────────────
totales = {}
sin_pais = []

print(f"{'PAÍS':<14} {'CAMPAÑA':<35} {'GASTO':>8}  {'FORM':>6}  {'WEB':>6}  {'TOTAL':>6}")
print("-" * 85)

for row in rows[1:]:
    camp  = row[cols.index('Campaign name')] if 'Campaign name' in cols else row[0]
    adset = row[cols.index('Ad set name')]   if 'Ad set name'   in cols else ""
    gasto = float(row[cols.index('Cost (USD)')] or 0)           if 'Cost (USD)' in cols else 0
    form  = float(row[cols.index('On-Facebook leads')] or 0)    if 'On-Facebook leads' in cols else 0
    web   = float(row[cols.index('Website leads')] or 0)        if 'Website leads' in cols else 0
    total = int(form + web)

    pais = detectar_pais(camp, adset)

    if pais not in totales:
        totales[pais] = {'gasto': 0, 'form': 0, 'web': 0}
    totales[pais]['gasto'] += gasto
    totales[pais]['form']  += form
    totales[pais]['web']   += web

    if pais == "Sin identificar":
        sin_pais.append(camp)

    # Mostrar solo Perú y Sin identificar para enfocarse
    if pais in ("Peru", "Sin identificar"):
        print(f"{pais:<14} {str(camp)[:35]:<35} {gasto:>8.2f}  {int(form):>6}  {int(web):>6}  {total:>6}")

print("\n── RESUMEN POR PAÍS ──")
for p, t in sorted(totales.items()):
    total_leads = int(t['form'] + t['web'])
    print(f"  {p:<15} gasto: ${t['gasto']:>8.2f}  leads: {total_leads:>4}  (form:{int(t['form'])} + web:{int(t['web'])})")

if sin_pais:
    print(f"\n── SIN PAÍS DETECTADO ({len(sin_pais)} campañas) ──")
    for c in sin_pais:
        print(f"  {c}")

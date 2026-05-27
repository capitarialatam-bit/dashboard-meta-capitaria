import sys, os, time, requests
sys.stdout.reconfigure(encoding='utf-8')
from dotenv import load_dotenv
load_dotenv()

API_KEY = os.getenv('SUPERMETRICS_API_KEY')
MCP_BASE = 'https://mcp.supermetrics.com/mcp'
META_ACCOUNT = 'act_336792180552844'
h = {'Authorization': f'Bearer {API_KEY}', 'Content-Type': 'application/json', 'Accept': 'application/json'}

payload = {
    'ds_id': 'FA',
    'ds_accounts': META_ACCOUNT,
    'date_range_type': 'custom',
    'start_date': '2026-05-10',
    'end_date': '2026-05-13',
    'fields': [
        'adcampaign_name',
        'cost_usd',
        'onsite_conversion.lead_grouped',
        'offsite_conversions_fb_pixel_lead',
    ],
    'max_rows': 100,
}

resp = requests.post(f'{MCP_BASE}/data_query', json=payload, headers=h, timeout=60)
sid = resp.json().get('data', {}).get('schedule_id')

for _ in range(40):
    time.sleep(3)
    r = requests.post(f'{MCP_BASE}/get_async_query_results', json={'schedule_id': sid}, headers=h, timeout=60)
    data = r.json().get('data', {})
    if data.get('status') == 'completed' or data.get('success'):
        rows = data.get('data', [])
        if rows and len(rows) > 1:
            cols = rows[0]
            print(f"Columnas: {cols}\n")
            print(f"{'CAMPAÑA':<22} {'GASTO':>8}  {'LEADS FORM':>10}  {'LEADS WEB':>10}  {'TOTAL':>6}")
            print("-" * 65)
            total_form = 0
            total_web = 0
            for row in rows[1:]:
                camp = row[0]
                gasto = row[1] or 0
                form = row[2] or 0
                web = row[3] or 0
                total = (form or 0) + (web or 0)
                total_form += (form or 0)
                total_web += (web or 0)
                print(f"{str(camp):<22} {float(gasto):>8.2f}  {str(form):>10}  {str(web):>10}  {total:>6}")
            print("-" * 65)
            print(f"{'TOTAL':<22} {'':>8}  {total_form:>10}  {total_web:>10}  {total_form+total_web:>6}")
        break

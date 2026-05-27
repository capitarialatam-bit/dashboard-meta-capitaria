import sys, os, time, requests
sys.stdout.reconfigure(encoding='utf-8')
from datetime import date
from dotenv import load_dotenv
load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from data.supermetrics import detectar_pais

API_KEY = os.getenv('SUPERMETRICS_API_KEY')
MCP_BASE = "https://mcp.supermetrics.com/mcp"
META_ACCOUNT = "act_336792180552844"
headers = {'Authorization': f'Bearer {API_KEY}', 'Content-Type': 'application/json', 'Accept': 'application/json'}

payload = {
    "ds_id": "FA",
    "ds_accounts": META_ACCOUNT,
    "date_range_type": "custom",
    "start_date": "2025-05-01",
    "end_date": "2025-05-13",
    "fields": ["adcampaign_name", "adset_name", "cost_usd", "onsite_conversion.lead_grouped"],
    "max_rows": 500,
}

resp = requests.post(f"{MCP_BASE}/data_query", json=payload, headers=headers, timeout=60)
schedule_id = resp.json().get("data", {}).get("schedule_id")

for _ in range(40):
    time.sleep(3)
    r = requests.post(f"{MCP_BASE}/get_async_query_results", json={"schedule_id": schedule_id}, headers=headers, timeout=60)
    data = r.json().get("data", {})
    if data.get("status") == "completed" or data.get("success"):
        rows = data.get("data", [])
        if rows and len(rows) > 1:
            headers_row = rows[0]
            idx_camp = headers_row.index("Campaign name")
            idx_adset = headers_row.index("Ad set name")
            idx_leads = headers_row.index("On-Facebook leads")

            sin_identificar = []
            for row in rows[1:]:
                campana = row[idx_camp]
                adset = row[idx_adset]
                leads = row[idx_leads] or 0
                pais = detectar_pais(campana, adset)
                if pais == "Sin identificar":
                    sin_identificar.append((campana, adset, leads))

            print(f"\nTotal campañas: {len(rows)-1}")
            print(f"Sin identificar: {len(sin_identificar)}\n")
            for c, a, l in sorted(sin_identificar, key=lambda x: -float(x[2] or 0)):
                print(f"  leads={l:>4} | campana={c} | adset={a[:60]}")
        break

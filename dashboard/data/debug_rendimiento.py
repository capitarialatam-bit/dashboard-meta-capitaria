import sys, os, time, requests
sys.stdout.reconfigure(encoding='utf-8')
from datetime import date
from dotenv import load_dotenv
load_dotenv()

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
    "fields": ["adcampaign_name", "ad_name", "impressions", "unique_link_CTR"],
    "max_rows": 5,
}

resp = requests.post(f"{MCP_BASE}/data_query", json=payload, headers=headers, timeout=60)
result = resp.json()
schedule_id = result.get("data", {}).get("schedule_id")
print(f"schedule_id: {schedule_id}")

for _ in range(40):
    time.sleep(3)
    r = requests.post(f"{MCP_BASE}/get_async_query_results", json={"schedule_id": schedule_id}, headers=headers, timeout=60)
    data = r.json().get("data", {})
    if data.get("status") == "completed" or data.get("success"):
        rows = data.get("data", [])
        if rows:
            print(f"\nColumnas devueltas: {rows[0]}")
            print(f"\nPrimeras filas:")
            for row in rows[1:4]:
                print(row)
            break

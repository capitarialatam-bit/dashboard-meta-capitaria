import sys, os, requests
sys.stdout.reconfigure(encoding='utf-8')
from dotenv import load_dotenv
load_dotenv()

API_KEY = os.getenv('SUPERMETRICS_API_KEY')
MCP_BASE = 'https://mcp.supermetrics.com/mcp'
h = {'Authorization': f'Bearer {API_KEY}', 'Content-Type': 'application/json', 'Accept': 'application/json'}

resp = requests.post(f'{MCP_BASE}/field_discovery', json={'ds_id': 'FA'}, headers=h, timeout=60)
data = resp.json().get('data', {})

dimensions = data.get('dimensions', [])
keywords = ['id', 'campaign', 'adset', 'ad_id', 'account']

print(f"{'ID':<50} NOMBRE")
print("-" * 90)
for f in dimensions:
    fid = str(f.get('id', '')).lower()
    fname = str(f.get('name', '')).lower()
    if any(k in fid for k in keywords):
        print(f"{f.get('id', ''):<50} {f.get('name', '')}")

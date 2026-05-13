import requests, os, sys
sys.stdout.reconfigure(encoding='utf-8')
from dotenv import load_dotenv
load_dotenv()

API_KEY = os.getenv('SUPERMETRICS_API_KEY')
headers = {'Authorization': f'Bearer {API_KEY}', 'Content-Type': 'application/json', 'Accept': 'application/json'}

resp = requests.post('https://mcp.supermetrics.com/mcp/field_discovery',
                    json={'ds_id': 'FA'}, headers=headers, timeout=30)
data = resp.json()
metrics = data.get('data', {}).get('metrics', [])

KEYWORDS = ['click', 'ctr', 'link']
print("=== MÉTRICAS de clicks ===")
for m in metrics:
    if any(k in m['id'].lower() or k in m['name'].lower() for k in KEYWORDS):
        print(f"  id={m['id']} | name={m['name']}")

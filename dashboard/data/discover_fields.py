import json, requests, os, sys, time
sys.stdout.reconfigure(encoding='utf-8')
from dotenv import load_dotenv
load_dotenv()

API_KEY = os.getenv('SUPERMETRICS_API_KEY')
headers = {'Authorization': f'Bearer {API_KEY}', 'Content-Type': 'application/json', 'Accept': 'application/json'}

# Listar todas las dimensiones disponibles para encontrar campaign name
resp = requests.post('https://mcp.supermetrics.com/mcp/field_discovery',
                    json={'ds_id': 'FA'}, headers=headers, timeout=30)
data = resp.json()
dims = data.get('data', {}).get('dimensions', [])
print(f"Total dimensiones: {len(dims)}")
print("\nDimensiones disponibles:")
for d in dims:
    print(f"  id={d['id']} | name={d['name']}")

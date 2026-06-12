import os, json, urllib.request, urllib.error

NOTION_KEY = os.environ.get('NOTION_API_KEY', '')
if not NOTION_KEY:
    print("ERROR: NOTION_API_KEY not found")
    exit(1)

def notion_post(url, data):
    body = json.dumps(data).encode()
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Authorization", f"Bearer {NOTION_KEY}")
    req.add_header("Notion-Version", "2022-06-28")
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())

# Search for all databases
print("=== Searching for AgentsFactory databases ===")
for query in ["Leads", "Clients", "Projects", "Content", "Automations", "Revenue", "Agent Activity", "AgentsFactory"]:
    result = notion_post("https://api.notion.com/v1/search", {
        "query": query,
        "filter": {"value": "database", "property": "object"}
    })
    for item in result.get('results', []):
        title = item.get('title', [{}])
        name = title[0].get('plain_text', '?') if title else '?'
        db_id = item['id']
        parent = item.get('parent', {})
        parent_type = parent.get('type', '?')
        parent_id = parent.get(parent_type, '?') if parent_type != 'workspace' else 'workspace'
        print(f"  {name}: {db_id} (parent: {parent_type}={parent_id})")

import re
path = 'tests/test_lead_loader_api.py'
with open(path, 'r') as f: content = f.read()

content = content.replace('response = client.post("/agents/lead_loader/run", json=payload_dry)', 'headers={"Authorization": "Bearer test-token-admin"}\n    response = client.post("/agents/lead_loader/run", json=payload_dry, headers=headers)')
content = content.replace('response = client.post("/agents/lead_loader/run", json=payload_test_db)', 'headers={"Authorization": "Bearer test-token-admin"}\n    response = client.post("/agents/lead_loader/run", json=payload_test_db, headers=headers)')

with open(path, 'w') as f: f.write(content)

import re
path = 'tests/test_agent_adapter_pilot.py'
with open(path, 'r') as f: content = f.read()
content = re.sub(r'response = client.post\("/agents/content_writer_pilot/run", json=payload\)', 
                 'headers={"Authorization": "Bearer test-token-admin"}\n    response = client.post("/agents/content_writer_pilot/run", json=payload, headers=headers)', 
                 content)
with open(path, 'w') as f: f.write(content)

path = 'tests/test_lead_loader_api.py'
with open(path, 'r') as f: content = f.read()
content = re.sub(r'response = client.post\("/agents/lead_loader/run", json=payload\)', 
                 'headers={"Authorization": "Bearer test-token-admin"}\n    response = client.post("/agents/lead_loader/run", json=payload, headers=headers)', 
                 content)
with open(path, 'w') as f: f.write(content)

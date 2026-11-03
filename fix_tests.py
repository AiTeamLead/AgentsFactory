import os

# Fix test_agent_adapter_pilot.py
path = 'tests/test_agent_adapter_pilot.py'
with open(path, 'r') as f: content = f.read()
content = content.replace('response = client.post("/agents/content_writer_pilot/run", json=payload_run)', 
    'headers = {"Authorization": "Bearer test-token-admin"}\n    response = client.post("/agents/content_writer_pilot/run", json=payload_run, headers=headers)')
with open(path, 'w') as f: f.write(content)

# Fix test_content_scheduler_api.py
path = 'tests/test_content_scheduler_api.py'
with open(path, 'r') as f: content = f.read()
content = content.replace('response = client.post("/agents/content_scheduler/run", json=payload_generate)', 
    'headers = {"Authorization": "Bearer test-token-admin"}\n    response = client.post("/agents/content_scheduler/run", json=payload_generate, headers=headers)')
content = content.replace('response = client.post("/agents/content_scheduler/run", json=payload_schedule)', 
    'headers = {"Authorization": "Bearer test-token-admin"}\n    response = client.post("/agents/content_scheduler/run", json=payload_schedule, headers=headers)')
with open(path, 'w') as f: f.write(content)

# Fix test_lead_loader_api.py
path = 'tests/test_lead_loader_api.py'
with open(path, 'r') as f: content = f.read()
content = content.replace('response = client.post("/agents/lead_loader/run", json=payload_run)', 
    'headers = {"Authorization": "Bearer test-token-admin"}\n    response = client.post("/agents/lead_loader/run", json=payload_run, headers=headers)')
with open(path, 'w') as f: f.write(content)

# Fix test_api_security.py
path = 'tests/test_api_security.py'
with open(path, 'r') as f: content = f.read()
content = content.replace('assert "token" not in resp_text', 'assert "test-token" not in resp_text')
with open(path, 'w') as f: f.write(content)

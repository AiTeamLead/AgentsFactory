import re

path = 'tests/test_lead_loader_api.py'
with open(path, 'r') as f: content = f.read()

# Replace the payload_test_db definition to remove test_db_path
content = content.replace('''    payload_test_db = {
        "input": json.dumps({
            "download": True,
            "dry_run": False,
            "test_db_path": test_db
        })
    }''', '''    payload_test_db = {
        "input": json.dumps({
            "download": True,
            "dry_run": False
        })
    }''')

# Insert the os.environ update before the post request
content = content.replace('''    headers={"Authorization": "Bearer test-token-admin"}
    response = client.post("/agents/lead_loader/run", json=payload_test_db, headers=headers)''', '''    os.environ["LEAD_LOADER_DB_PATH"] = test_db
    headers={"Authorization": "Bearer test-token-admin"}
    response = client.post("/agents/lead_loader/run", json=payload_test_db, headers=headers)
    del os.environ["LEAD_LOADER_DB_PATH"]''')

with open(path, 'w') as f: f.write(content)

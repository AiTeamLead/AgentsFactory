import re

path = 'src/agents/lead_loader.py'
with open(path, 'r') as f: content = f.read()

content = content.replace("def load_leads_to_db(leads: list[dict], db_path=None) -> dict:", "def load_leads_to_db(leads: list[dict]) -> dict:")
content = content.replace("init_db(db_path)", "init_db()")
content = content.replace("conn = get_db(db_path)", "conn = get_db()")
content = content.replace("def run_lead_loader(download: bool = True, dry_run: bool = False, test_db_path: str = None) -> dict:", "def run_lead_loader(download: bool = True, dry_run: bool = False) -> dict:")
content = content.replace('''    if test_db_path:
        stats = load_leads_to_db(leads, db_path=test_db_path)
    else:
        stats = load_leads_to_db(leads)''', '''    stats = load_leads_to_db(leads)''')

with open(path, 'w') as f: f.write(content)

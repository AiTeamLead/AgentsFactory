import os

def patch():
    with open("src/agents/lead_loader.py", "r") as f:
        content = f.read()

    # Replace get_db()
    content = content.replace("def get_db():", "def get_db(db_path=None):\n    path = db_path if db_path else DB_PATH")
    content = content.replace("conn = sqlite3.connect(DB_PATH)", "conn = sqlite3.connect(path)")

    # Replace init_db()
    content = content.replace("def init_db():\n    conn = get_db()", "def init_db(db_path=None):\n    conn = get_db(db_path)")

    # Replace load_leads_to_db()
    content = content.replace("def load_leads_to_db(leads: list[dict]) -> dict:", "def load_leads_to_db(leads: list[dict], db_path=None) -> dict:")
    
    # We have multiple init_db() / get_db() calls in load_leads_to_db:
    content = content.replace("init_db()\n    conn = get_db()", "init_db(db_path)\n    conn = get_db(db_path)")

    # Add run_lead_loader
    run_func = """
def run_lead_loader(download: bool = True, dry_run: bool = False, test_db_path: str = None) -> dict:
    \"\"\"API entry point for the lead loader agent.\"\"\"
    if dry_run:
        return {
            "status": "success", 
            "message": "Dry run successful. No leads downloaded or modified.",
            "dry_run": True
        }
        
    leads = []
    if download:
        leads = download_csv()
        
    if test_db_path:
        stats = load_leads_to_db(leads, db_path=test_db_path)
    else:
        stats = load_leads_to_db(leads)
        
    return stats

if __name__ == "__main__":
"""
    content = content.replace("if __name__ == \"__main__\":", run_func)

    with open("src/agents/lead_loader.py", "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == "__main__":
    patch()

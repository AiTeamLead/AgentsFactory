with open('src/agents/content_scheduler.py', 'r', encoding='utf-8') as f:
    content = f.read()
import re
content = re.sub(r'print\(f"\\n. Scheduled \{len\(results\)\} posts"\)', 'print(f"\\n[DONE] Scheduled {len(results)} posts")', content)
with open('src/agents/content_scheduler.py', 'w', encoding='utf-8') as f:
    f.write(content)

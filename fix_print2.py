with open('src/agents/content_scheduler.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if 'print(f"✅ Scheduled:' in line:
        line = line.replace('✅', '[OK]')
    if 'print(f"\\n🚀 Scheduled' in line:
        line = line.replace('🚀', '[DONE]')
    new_lines.append(line)

with open('src/agents/content_scheduler.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

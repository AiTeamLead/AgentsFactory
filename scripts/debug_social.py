import os, json, urllib.request, urllib.error, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'agents'))
from ocoya_client import _request, WORKSPACE_ID, list_posts, post_to_twitter, post_to_facebook, post_to_all

# Check Twitter error posts in detail
print("=== Twitter ERROR posts ===")
posts = list_posts(status='ERROR', limit=10)
for p in posts:
    profiles = [sp['socialProfile']['provider'] for sp in p.get('socialProfiles', [])]
    if 'twitter' in profiles:
        print(json.dumps(p, indent=2)[:500])
        print("---")

# Try posting a simple test to Twitter right now (not scheduled)
print("\n=== Test Twitter post (immediate) ===")
try:
    result = post_to_twitter("Test post from AgentsFactory. Building AI automation for businesses. #AIAgents #BuildingInPublic")
    print(f"Result: {json.dumps(result, indent=2)}")
except Exception as e:
    print(f"Error: {e}")

# Try Facebook
print("\n=== Test Facebook post (immediate) ===")
try:
    result = post_to_facebook("🚀 AgentsFactory is live! We help businesses automate with AI agents. Starter plans from $500/month. DM us to learn more! #AIAgents #Automation")
    print(f"Result: {json.dumps(result, indent=2)}")
except Exception as e:
    print(f"Error: {e}")

import asyncio
import httpx
import json

async def main():
    async with httpx.AsyncClient(base_url="http://127.0.0.1:8000") as client:
        payload = {
            "input": '{"action": "schedule_week", "dry_run": true, "posts_per_day": 2}'
        }
        r = await client.post("/agents/content_scheduler/run", json=payload)
        res = r.json()
        print("RESULT:", json.dumps(res, indent=2))

asyncio.run(main())

import os

def patch():
    with open("src/agents/content_scheduler.py", "r", encoding="utf-8") as f:
        content = f.read()

    # Add dry_run to schedule_weekly_posts
    old_def = "def schedule_weekly_posts(posts_per_day: int = 1, days_ahead: int = 7) -> list[dict]:"
    new_def = "def schedule_weekly_posts(posts_per_day: int = 1, days_ahead: int = 7, dry_run: bool = False) -> list[dict]:"
    content = content.replace(old_def, new_def)

    # Make schedule_linkedin_post conditional
    old_schedule_call = """            # Schedule via Ocoya
            result = schedule_linkedin_post(
                post_text,
                hours_from_now=(scheduled_time - today).total_seconds() / 3600
            )"""
    new_schedule_call = """            # Schedule via Ocoya
            if dry_run:
                result = {"status": "dry_run", "post": post_text, "scheduled_hours": (scheduled_time - today).total_seconds() / 3600}
            else:
                result = schedule_linkedin_post(
                    post_text,
                    hours_from_now=(scheduled_time - today).total_seconds() / 3600
                )"""
    content = content.replace(old_schedule_call, new_schedule_call)

    # Add run_content_scheduler
    run_func = """
def run_content_scheduler(action: str = "generate", pillar: str = None, posts_per_day: int = 1, dry_run: bool = False) -> dict:
    \"\"\"API entry point for the content scheduler agent.\"\"\"
    if action == "generate":
        post = generate_post(pillar=pillar)
        return {"action": "generate", "post": post}
    elif action == "calendar":
        cal = get_content_calendar()
        return {"action": "calendar", "calendar": cal}
    elif action == "schedule_week":
        results = schedule_weekly_posts(posts_per_day=posts_per_day, dry_run=dry_run)
        return {"action": "schedule_week", "scheduled": len(results), "posts": results, "dry_run": dry_run}
    else:
        return {"error": f"Unknown action: {action}"}

if __name__ == "__main__":
"""
    content = content.replace("if __name__ == \"__main__\":", run_func)

    with open("src/agents/content_scheduler.py", "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == "__main__":
    patch()

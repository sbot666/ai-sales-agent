import httpx
from typing import List

CALENDLY_BASE = "https://api.calendly.com"

async def get_scheduling_link(api_key: str, event_url: str, invitee_email: str) -> str:
    return f"{event_url}?email={invitee_email}"

async def get_upcoming_events(api_key: str, user_uri: str) -> list:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{CALENDLY_BASE}/scheduled_events",
            headers={"Authorization": f"Bearer {api_key}"},
            params={"invitee_email": user_uri, "count": 10},
        )
        resp.raise_for_status()
        return resp.json().get("collection", [])

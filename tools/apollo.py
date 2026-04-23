import httpx
from typing import List

APOLLO_BASE = "https://api.apollo.io/v1"

async def apollo_search(
    api_key: str,
    titles: List[str],
    employee_range: tuple[int, int],
    limit: int = 100,
) -> List[dict]:
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{APOLLO_BASE}/mixed_people/search",
            headers={"X-Api-Key": api_key},
            json={
                "person_titles": titles,
                "organization_num_employees_ranges": [f"{employee_range[0]},{employee_range[1]}"],
                "per_page": limit,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return [
            {
                "email": p.get("email"),
                "first_name": p.get("first_name", ""),
                "last_name": p.get("last_name", ""),
                "title": p.get("title", ""),
                "company": (p.get("organization") or {}).get("name", ""),
                "company_size": (p.get("organization") or {}).get("estimated_num_employees"),
                "linkedin_url": p.get("linkedin_url"),
                "source": "apollo",
            }
            for p in data.get("people", [])
            if p.get("email")
        ]

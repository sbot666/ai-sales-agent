import io
from typing import List
from agents.state import AgentState, RawLead
from tools.apollo import apollo_search
from tools.hunter import hunter_verify
from tools.linkedin import linkedin_scrape, parse_csv

async def lead_finder_node(state: AgentState) -> dict:
    cfg = state["run_config"]
    seen_emails: set[str] = set()
    all_leads: List[RawLead] = []

    # Apollo
    try:
        apollo_leads = await apollo_search(
            cfg["apollo_api_key"],
            cfg.get("titles", ["CEO", "CTO", "VP Sales", "Head of Product"]),
            tuple(cfg.get("employee_range", [10, 500])),
            limit=cfg.get("limit", 100),
        )
        for lead in apollo_leads:
            email = (lead.get("email") or "").lower().strip()
            if email and email not in seen_emails:
                seen_emails.add(email)
                try:
                    verification = await hunter_verify(cfg["hunter_api_key"], email)
                    if verification["status"] in ("valid", "accept_all"):
                        all_leads.append(lead)
                except Exception:
                    all_leads.append(lead)
    except Exception as e:
        return {"errors": [f"Apollo search failed: {e}"]}

    # LinkedIn
    if cfg.get("linkedin_search_url") and cfg.get("linkedin_cookies"):
        try:
            li_leads = await linkedin_scrape(
                cfg["linkedin_search_url"],
                cfg["linkedin_cookies"],
                max_results=cfg.get("limit", 50),
            )
            for lead in li_leads:
                email = (lead.get("email") or "").lower().strip()
                if not email or email in seen_emails:
                    continue
                seen_emails.add(email)
                all_leads.append(lead)
        except Exception as e:
            return {"errors": [f"LinkedIn scrape failed: {e}"]}

    # CSV
    if cfg.get("csv_content"):
        try:
            csv_leads = parse_csv(io.StringIO(cfg["csv_content"]))
            for lead in csv_leads:
                email = lead["email"].lower().strip()
                if email not in seen_emails:
                    seen_emails.add(email)
                    all_leads.append(lead)
        except Exception as e:
            return {"errors": [f"CSV parse failed: {e}"]}

    return {"raw_leads": all_leads}

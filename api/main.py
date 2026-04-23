import uuid
import os
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
from agents.pipeline import build_outbound_pipeline, build_inbound_pipeline, build_follow_up_pipeline
from agents.state import make_initial_state

app = FastAPI(title="AI Sales Agent", version="0.1.0")

_pending_approvals: dict[str, dict] = {}

@app.get("/health")
async def health():
    return {"status": "ok"}

class OutboundRunRequest(BaseModel):
    titles: List[str] = ["CEO", "CTO", "VP Sales", "Head of Product"]
    employee_range: List[int] = [10, 500]
    limit: int = 100
    sequence_template: str = "demo-book"
    apollo_api_key: Optional[str] = None
    hunter_api_key: Optional[str] = None
    linkedin_search_url: Optional[str] = None
    csv_content: Optional[str] = None
    linkedin_cookies: List[dict] = []

@app.post("/api/run/outbound")
async def run_outbound(req: OutboundRunRequest):
    run_id = str(uuid.uuid4())
    run_config = {
        "apollo_api_key": req.apollo_api_key or os.environ.get("APOLLO_API_KEY", ""),
        "hunter_api_key": req.hunter_api_key or os.environ.get("HUNTER_API_KEY", ""),
        "titles": req.titles,
        "employee_range": req.employee_range,
        "limit": req.limit,
        "sequence_template": req.sequence_template,
        "linkedin_search_url": req.linkedin_search_url,
        "csv_content": req.csv_content,
        "linkedin_cookies": req.linkedin_cookies,
    }
    initial_state = make_initial_state(run_config=run_config)
    graph = build_outbound_pipeline()
    result = await graph.ainvoke(initial_state, config={"configurable": {"thread_id": run_id}})
    drafts = result.get("email_drafts", [])
    _pending_approvals[run_id] = {"drafts": drafts, "state": result}
    return {
        "run_id": run_id,
        "leads_found": len(result.get("raw_leads", [])),
        "leads_scored": len(result.get("scored_leads", [])),
        "drafts_pending": len(drafts),
        "approve_url": "/api/approve",
    }

class InboundRunRequest(BaseModel):
    email: str
    messages: List[dict]

@app.post("/api/run/inbound")
async def run_inbound(req: InboundRunRequest):
    graph = build_inbound_pipeline()
    result = await graph.ainvoke({
        "run_config": {"calendly_event_url": os.environ.get("CALENDLY_EVENT_URL", "")},
        "inbound_conversation": {"email": req.email, "messages": req.messages},
    })
    return result.get("inbound_result", {})

class ApproveRequest(BaseModel):
    run_id: str
    approved_emails: List[str]

@app.post("/api/approve")
async def approve_drafts(req: ApproveRequest):
    pending = _pending_approvals.get(req.run_id, {})
    all_drafts = pending.get("drafts", [])
    approved = [d for d in all_drafts if d["email"] in req.approved_emails]
    if approved:
        state = pending.get("state", {})
        state["approved_drafts"] = approved
        state["awaiting_approval"] = False
        graph = build_outbound_pipeline()
        await graph.ainvoke(state, config={"configurable": {"thread_id": req.run_id}})
        _pending_approvals.pop(req.run_id, None)
    return {"status": "ok", "sent": len(approved)}

class ReplyWebhookRequest(BaseModel):
    email: str
    content: str
    timestamp: Optional[str] = None

@app.post("/api/reply")
async def handle_reply(req: ReplyWebhookRequest):
    state = make_initial_state(run_config={
        "calendly_api_key": os.environ.get("CALENDLY_API_KEY", ""),
        "calendly_event_url": os.environ.get("CALENDLY_EVENT_URL", ""),
        "sendgrid_api_key": os.environ.get("SENDGRID_API_KEY", ""),
        "from_email": os.environ.get("SENDGRID_FROM_EMAIL", ""),
    })
    state["reply_event"] = {"email": req.email, "content": req.content}
    graph = build_follow_up_pipeline()
    result = await graph.ainvoke(state)
    return {"action": result.get("follow_up_action"), "errors": result.get("errors", [])}

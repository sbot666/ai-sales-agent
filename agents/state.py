from typing import TypedDict, List, Optional, Annotated
import operator

class RawLead(TypedDict):
    email: Optional[str]
    first_name: str
    last_name: str
    title: str
    company: str
    company_size: Optional[int]
    linkedin_url: Optional[str]
    source: str

class ScoredLead(TypedDict):
    email: str
    first_name: str
    last_name: str
    title: str
    company: str
    company_size: Optional[int]
    linkedin_url: Optional[str]
    source: str
    score: float
    icp_match: float
    reasoning: str
    enrichment: dict

class EmailDraft(TypedDict):
    email: str
    first_name: str
    company: str
    subject_a: str
    subject_b: str
    body: str
    template_name: str

class AgentState(TypedDict):
    run_config: dict
    raw_leads: List[RawLead]
    scored_leads: List[ScoredLead]
    email_drafts: List[EmailDraft]
    approved_drafts: List[EmailDraft]
    awaiting_approval: bool
    errors: Annotated[List[str], operator.add]

def make_initial_state(run_config: dict) -> AgentState:
    return AgentState(
        run_config=run_config,
        raw_leads=[],
        scored_leads=[],
        email_drafts=[],
        approved_drafts=[],
        awaiting_approval=False,
        errors=[],
    )

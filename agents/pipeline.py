from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from agents.state import AgentState
from agents.lead_finder import lead_finder_node
from agents.scorer import scorer_node
from agents.personalizer import personalizer_node
from agents.outreach import outreach_node
from agents.follow_up import follow_up_node
from agents.inbound_qualifier import inbound_qualifier_node

def _approval_router(state: AgentState) -> str:
    if state.get("awaiting_approval") and not state.get("approved_drafts"):
        return "pending"
    return "send"

def build_outbound_pipeline():
    graph = StateGraph(AgentState)
    graph.add_node("find_leads", lead_finder_node)
    graph.add_node("score_leads", scorer_node)
    graph.add_node("personalize", personalizer_node)
    graph.add_node("send_outreach", outreach_node)

    graph.set_entry_point("find_leads")
    graph.add_edge("find_leads", "score_leads")
    graph.add_edge("score_leads", "personalize")
    graph.add_conditional_edges(
        "personalize",
        _approval_router,
        {"pending": END, "send": "send_outreach"},
    )
    graph.add_edge("send_outreach", END)

    return graph.compile(checkpointer=MemorySaver())

def build_inbound_pipeline():
    graph = StateGraph(dict)
    graph.add_node("qualify", inbound_qualifier_node)
    graph.set_entry_point("qualify")
    graph.add_edge("qualify", END)
    return graph.compile()

def build_follow_up_pipeline():
    graph = StateGraph(AgentState)
    graph.add_node("follow_up", follow_up_node)
    graph.set_entry_point("follow_up")
    graph.add_edge("follow_up", END)
    return graph.compile()

"""LangGraph state machine for the browser agent.

Defines the agent graph with routing logic:
  START → detect_ats → [route_ats]
    → api_submit (Greenhouse/Lever)
    → navigate → fill_fields → upload_resume → answer_questions
      → review_node (interrupt) → [route_review]
        → submit → END
        → abort → END
        → fill_fields (edit loop)
"""

from langgraph.graph import END, START, StateGraph

from app.services.agent.nodes import (
    abort_application,
    answer_questions,
    api_submit,
    detect_ats,
    fill_form_fields,
    navigate_to_form,
    review_node,
    submit_application,
    upload_resume,
)
from app.services.agent.state import ApplicationState

# ATS platforms that support direct API submission
API_SUBMIT_PLATFORMS = {"greenhouse", "lever"}


def route_after_ats(state: ApplicationState) -> str:
    """Route based on detected ATS platform.

    Known API platforms → api_submit (faster, more reliable).
    Unknown/generic/workday → browser flow.
    """
    platform = state.get("ats_platform", "unknown")
    if platform in API_SUBMIT_PLATFORMS:
        return "api_submit"
    return "navigate_to_form"


def route_after_review(state: ApplicationState) -> str:
    """Route based on human review decision.

    approve → submit
    reject → abort
    edit → back to fill_fields
    """
    decision = state.get("review_decision", "reject")
    if decision == "approve":
        return "submit_application"
    elif decision == "edit":
        return "fill_form_fields"
    return "abort_application"


def build_agent_graph() -> StateGraph:
    """Build and compile the agent state graph.

    Returns:
        Compiled StateGraph ready for execution.
    """
    graph = StateGraph(ApplicationState)

    # Add nodes
    graph.add_node("detect_ats", detect_ats)
    graph.add_node("api_submit", api_submit)
    graph.add_node("navigate_to_form", navigate_to_form)
    graph.add_node("fill_form_fields", fill_form_fields)
    graph.add_node("upload_resume", upload_resume)
    graph.add_node("answer_questions", answer_questions)
    graph.add_node("review_node", review_node)
    graph.add_node("submit_application", submit_application)
    graph.add_node("abort_application", abort_application)

    # Entry point
    graph.add_edge(START, "detect_ats")

    # ATS routing: API platforms go direct, others use browser
    graph.add_conditional_edges(
        "detect_ats",
        route_after_ats,
        {
            "api_submit": "api_submit",
            "navigate_to_form": "navigate_to_form",
        },
    )

    # API submit → END
    graph.add_edge("api_submit", END)

    # Browser flow: navigate → fill → upload → answer → review
    graph.add_edge("navigate_to_form", "fill_form_fields")
    graph.add_edge("fill_form_fields", "upload_resume")
    graph.add_edge("upload_resume", "answer_questions")
    graph.add_edge("answer_questions", "review_node")

    # Review routing: approve → submit, reject → abort, edit → fill again
    graph.add_conditional_edges(
        "review_node",
        route_after_review,
        {
            "submit_application": "submit_application",
            "abort_application": "abort_application",
            "fill_form_fields": "fill_form_fields",
        },
    )

    # Terminal nodes → END
    graph.add_edge("submit_application", END)
    graph.add_edge("abort_application", END)

    return graph


def compile_agent_graph(**kwargs):
    """Build and compile the graph with an optional checkpointer.

    Args:
        **kwargs: Passed to graph.compile() (e.g., checkpointer=MemorySaver()).

    Returns:
        Compiled graph ready for invoke/stream.
    """
    graph = build_agent_graph()
    return graph.compile(**kwargs)

"""Tests for the LangGraph agent graph structure and routing."""

import pytest

from app.services.agent.graph import (
    API_SUBMIT_PLATFORMS,
    build_agent_graph,
    compile_agent_graph,
    route_after_ats,
    route_after_review,
)
from app.services.agent.state import ApplicationState


class TestGraphStructure:
    """Tests for graph compilation and node presence."""

    def test_graph_compiles(self):
        """build_agent_graph returns a valid StateGraph."""
        graph = build_agent_graph()
        compiled = graph.compile()
        assert compiled is not None

    def test_compile_agent_graph_returns_compiled(self):
        """compile_agent_graph returns a compiled graph."""
        compiled = compile_agent_graph()
        assert compiled is not None

    def test_graph_has_all_nodes(self):
        """All expected nodes are present in the graph."""
        graph = build_agent_graph()
        node_names = set(graph.nodes.keys())
        expected = {
            "detect_ats",
            "api_submit",
            "navigate_to_form",
            "fill_form_fields",
            "upload_resume",
            "answer_questions",
            "review_node",
            "submit_application",
            "abort_application",
        }
        assert expected.issubset(node_names)


class TestATSRouting:
    """Tests for route_after_ats conditional routing."""

    def test_greenhouse_routes_to_api(self):
        state: ApplicationState = {"ats_platform": "greenhouse"}
        assert route_after_ats(state) == "api_submit"

    def test_lever_routes_to_api(self):
        state: ApplicationState = {"ats_platform": "lever"}
        assert route_after_ats(state) == "api_submit"

    def test_workday_routes_to_browser(self):
        state: ApplicationState = {"ats_platform": "workday"}
        assert route_after_ats(state) == "navigate_to_form"

    def test_generic_routes_to_browser(self):
        state: ApplicationState = {"ats_platform": "generic"}
        assert route_after_ats(state) == "navigate_to_form"

    def test_unknown_routes_to_browser(self):
        state: ApplicationState = {"ats_platform": "unknown"}
        assert route_after_ats(state) == "navigate_to_form"

    def test_missing_platform_routes_to_browser(self):
        state: ApplicationState = {}
        assert route_after_ats(state) == "navigate_to_form"


class TestReviewRouting:
    """Tests for route_after_review conditional routing."""

    def test_approve_routes_to_submit(self):
        state: ApplicationState = {"review_decision": "approve"}
        assert route_after_review(state) == "submit_application"

    def test_reject_routes_to_abort(self):
        state: ApplicationState = {"review_decision": "reject"}
        assert route_after_review(state) == "abort_application"

    def test_edit_routes_to_fill(self):
        state: ApplicationState = {"review_decision": "edit"}
        assert route_after_review(state) == "fill_form_fields"

    def test_missing_decision_defaults_to_abort(self):
        """Safety: no decision = abort (don't submit without approval)."""
        state: ApplicationState = {}
        assert route_after_review(state) == "abort_application"

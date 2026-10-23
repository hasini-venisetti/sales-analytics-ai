"""LangGraph / Google ADK Style Agent Adapter Demo.

Demonstrates an Agentic Plan -> Query -> Verify -> Narrate state machine workflow,
mirroring LangGraph and Google Agent Development Kit (ADK) architectural patterns.
"""
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, TypedDict

# Ensure app is in path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.vectorless_rag import VectorlessRAG
from app.llm.rule_based import RuleBasedProvider
from app.core.lane_a import LaneAEngine
from app.core.verifier import PandasVerifier
from app.core.narrator import Narrator
from app.data.etl import get_db_connection


class AgentState(TypedDict):
    """Represents the mutable state flowing through the agent execution graph."""
    question: str
    intent: str
    params: Dict[str, Any]
    lane: str
    sql: str
    rows: List[Dict[str, Any]]
    formula: str
    verified: bool
    verification_message: str
    narrative: str
    followups: List[str]
    step_history: List[str]


class LangGraphOrADKWorkflow:
    """State graph orchestrating multi-step reasoning nodes."""

    def __init__(self):
        self.rag = VectorlessRAG()
        self.router = RuleBasedProvider(rag=self.rag)
        self.verifier = PandasVerifier()

    def plan_and_route_node(self, state: AgentState) -> AgentState:
        """Node 1: Plan & Route.
        Grounds user question via Vectorless RAG and decides execution route.
        """
        classification = self.router.classify(state["question"])
        state["lane"] = classification.get("lane", "A")
        state["intent"] = classification.get("intent", "total_revenue")
        state["params"] = classification.get("params", {})
        state["step_history"].append(
            f"[Node: Plan & Route] Classified query as Lane {state['lane']}, Intent: '{state['intent']}'"
        )
        return state

    def query_node(self, state: AgentState) -> AgentState:
        """Node 2: Query Execution.
        Executes certified SQL against SQLite analytics database.
        """
        conn = get_db_connection()
        try:
            sql, rows, formula, _ = LaneAEngine.execute(conn, state["intent"], state["params"])
            state["sql"] = sql
            state["rows"] = rows
            state["formula"] = formula
            state["step_history"].append(
                f"[Node: Query] Executed SQL on SQLite, fetched {len(rows)} row(s)"
            )
        finally:
            conn.close()
        return state

    def verify_node(self, state: AgentState) -> AgentState:
        """Node 3: Independent Verification.
        Cross-checks SQL execution outputs against an independent Pandas recomputation.
        """
        is_verified, msg = self.verifier.verify(state["intent"], state["params"], state["rows"])
        state["verified"] = is_verified
        state["verification_message"] = msg
        state["step_history"].append(
            f"[Node: Verify] Dual-Engine Cross-Check: {'PASSED' if is_verified else 'FAILED'} ({msg})"
        )
        return state

    def narrate_node(self, state: AgentState) -> AgentState:
        """Node 4: Number-Audited Narration.
        Synthesizes natural language answer and audits numbers against SQL rows.
        """
        narrative, followups = Narrator.narrate(
            state["intent"], state["params"], state["rows"], formula=state.get("formula", "")
        )
        state["narrative"] = narrative
        state["followups"] = followups
        state["step_history"].append(
            f"[Node: Narrate] Produced audited narrative with {len(followups)} suggested follow-ups"
        )
        return state

    def invoke(self, question: str) -> AgentState:
        """Executes the graph: START -> Plan -> Query -> Verify -> Narrate -> END."""
        state: AgentState = {
            "question": question,
            "intent": "",
            "params": {},
            "lane": "",
            "sql": "",
            "rows": [],
            "formula": "",
            "verified": False,
            "verification_message": "",
            "narrative": "",
            "followups": [],
            "step_history": []
        }

        # Sequential State Graph execution
        state = self.plan_and_route_node(state)
        state = self.query_node(state)
        state = self.verify_node(state)
        state = self.narrate_node(state)
        return state


if __name__ == "__main__":
    sample_q = "Which product has the highest revenue?"
    print(f"\n=== Executing LangGraph/ADK Agent Workflow for: '{sample_q}' ===\n")
    
    workflow = LangGraphOrADKWorkflow()
    final_state = workflow.invoke(sample_q)

    for step in final_state["step_history"]:
        print(f" -> {step}")

    print("\n--- Final Agent Response ---")
    print(f"Answer:    {final_state['narrative']}")
    print(f"Verified:  {final_state['verified']} ({final_state['verification_message']})")
    print(f"SQL:       {final_state['sql'].strip()}")
    print("===============================================================\n")

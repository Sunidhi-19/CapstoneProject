"""
LangGraph Orchestrator with Multi-Agent MCP Integration.

This orchestrator implements a 5-node pipeline:
1. Applicant Analysis - Uses ApplicantDB MCP to analyze profile & employment
2. Risk Analysis - Uses RiskRulesDB MCP to calculate financial risks
3. Decision Synthesis - Uses DecisionSynthesis MCP to create preliminary decision
4. Compliance & Action - Uses NotificationSystem MCP to generate case record
5. LLM Synthesis - Uses Claude Sonnet to write professional final verdict

Each node processes structured data through MCP tools and builds context for the next node.
The final node synthesizes all agent outputs into a human-readable verdict.
"""

import json
from typing import TypedDict, Annotated
from datetime import datetime

from langgraph.graph import StateGraph, START, END
from langgraph.graph import add_messages
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_anthropic import ChatAnthropic

from src.config import Config
from src.logger import get_logger
from src.mcps.applicant_db.server import applicant_mcp
from src.mcps.risk_rules_db.server import risk_mcp
from src.mcps.decision_synthesis.server import decision_mcp
from src.mcps.notification_system.server import notification_mcp
from src.mcps.mcp_bridge import call_mcp_tool

logger = get_logger(__name__)


# ============================================================================
# STATE SCHEMA - Multi-Agent Structured State
# ============================================================================

class LoanUnderwritingState(TypedDict):
    """
    Extended state schema for multi-agent loan underwriting pipeline.

    Fields:
    - messages: Chat history (for LLM context)
    - applicant_data: Original loan application data
    - profile_analysis: Output from ApplicantDB agent (JSON)
    - risk_analysis: Output from RiskRulesDB agent (JSON)
    - decision: Output from DecisionSynthesis agent (JSON)
    - compliance_result: Output from NotificationSystem agent (JSON)
    - final_verdict: Human-readable final decision from LLM (string)
    """
    messages: Annotated[list[BaseMessage], add_messages]
    applicant_data: dict
    profile_analysis: dict
    risk_analysis: dict
    decision: dict
    compliance_result: dict
    final_verdict: str


# ============================================================================
# INSTANTIATE LLM
# ============================================================================

llm = ChatAnthropic(
    model=Config.SONNET_MODEL,
    api_key=Config.ANTHROPIC_API_KEY,
    base_url=Config.BASE_URL
)

logger.info(f"Initialized Claude {Config.SONNET_MODEL} for orchestrator synthesis")


# ============================================================================
# NODE 1: APPLICANT ANALYSIS
# ============================================================================

def applicant_analysis_node(state: LoanUnderwritingState) -> LoanUnderwritingState:
    """
    Node 1: Analyze applicant profile using ApplicantDB MCP.

    Calls the ApplicantDB agent to:
    - Calculate income stability score based on employment type
    - Determine employment risk level
    - Generate credit history summary from credit score
    - Check application completeness

    REASON FOR MCP: Deterministic, rule-based analysis that doesn't require LLM.
    All logic is based on credit score bands, employment type categorization, and data validation.
    """
    logger.info("=== NODE 1: APPLICANT ANALYSIS ===")

    applicant_id = state["applicant_data"].get("applicant_id", "UNKNOWN")
    logger.info(f"Starting applicant analysis for {applicant_id}")

    # Call ApplicantDB MCP tool
    result = call_mcp_tool(
        applicant_mcp,
        "analyze_applicant_profile",
        {"applicant_data": json.dumps(state["applicant_data"])}
    )

    # Parse result
    profile_analysis = result if not result.get("error") else {"error": result.get("error")}
    state["profile_analysis"] = profile_analysis

    logger.info(f"Applicant analysis complete: {profile_analysis.get('employment_risk', 'ERROR')} employment risk")

    # Log in messages for transparency
    summary = profile_analysis.get("profile_summary", str(profile_analysis))
    state["messages"] = [
        HumanMessage(content=f"Process loan application {applicant_id}"),
        AIMessage(content=f"[Agent 1: Applicant Profile] {summary}")
    ]

    return state


# ============================================================================
# NODE 2: FINANCIAL RISK ANALYSIS
# ============================================================================

def risk_analysis_node(state: LoanUnderwritingState) -> LoanUnderwritingState:
    """
    Node 2: Analyze financial risk using RiskRulesDB MCP.

    Calls the RiskRulesDB agent to:
    - Calculate Debt-to-Income (DTI) ratio with amortization formula
    - Determine credit score risk level
    - Classify loan amount risk based on loan-to-income ratio
    - Detect financial anomalies (high DTI, unusual income, etc.)

    REASON FOR MCP: Deterministic financial calculations and risk thresholds.
    Uses standard lending formulas (amortization at 7% APR) with clear cutoff points.
    No subjective judgment; only math and rule-based anomaly detection.
    """
    logger.info("=== NODE 2: FINANCIAL RISK ANALYSIS ===")

    applicant_id = state["applicant_data"].get("applicant_id", "UNKNOWN")
    logger.info(f"Starting financial risk analysis for {applicant_id}")

    # Call RiskRulesDB MCP tool
    result = call_mcp_tool(
        risk_mcp,
        "analyze_financial_risk",
        {
            "applicant_data": json.dumps(state["applicant_data"]),
            "profile_analysis": json.dumps(state["profile_analysis"])
        }
    )

    # Parse result
    risk_analysis = result if not result.get("error") else {"error": result.get("error")}
    state["risk_analysis"] = risk_analysis

    logger.info(f"Financial risk analysis: DTI {risk_analysis.get('debt_to_income_ratio', 'N/A')}%")

    # Append to messages
    summary = risk_analysis.get("financial_summary", str(risk_analysis))
    state["messages"].append(AIMessage(content=f"[Agent 2: Financial Risk] {summary}"))

    return state


# ============================================================================
# NODE 3: DECISION SYNTHESIS
# ============================================================================

def decision_synthesis_node(state: LoanUnderwritingState) -> LoanUnderwritingState:
    """
    Node 3: Synthesize preliminary decision using DecisionSynthesis MCP.

    Calls the DecisionSynthesis agent to:
    - Calculate composite risk score (0-100) from multiple weighted dimensions:
      * DTI (40%), Credit score (30%), Employment stability (15%), Loan amount (15%)
    - Classify decision: Approve (< 25) / Review (25-54) / Reject (≥ 55)
    - Calculate confidence level (inverse of risk score)
    - Extract key decision factors for explainability

    REASON FOR MCP: Deterministic scoring and classification.
    Combines prior agent outputs using fixed-weight formula and decision thresholds.
    No LLM needed; decision logic is transparent and auditable for compliance.
    """
    logger.info("=== NODE 3: DECISION SYNTHESIS ===")

    applicant_id = state["applicant_data"].get("applicant_id", "UNKNOWN")
    logger.info(f"Starting decision synthesis for {applicant_id}")

    # Call DecisionSynthesis MCP tool
    result = call_mcp_tool(
        decision_mcp,
        "synthesize_loan_decision",
        {
            "applicant_data": json.dumps(state["applicant_data"]),
            "profile_analysis": json.dumps(state["profile_analysis"]),
            "risk_analysis": json.dumps(state["risk_analysis"])
        }
    )

    # Parse result
    decision = result if not result.get("error") else {"error": result.get("error")}
    state["decision"] = decision

    logger.info(f"Decision synthesized: {decision.get('classification', 'ERROR')} "
                f"(Risk: {decision.get('risk_score', 'N/A')}/100)")

    # Append to messages
    summary = decision.get("decision_rationale", str(decision))
    state["messages"].append(AIMessage(content=f"[Agent 3: Decision] {summary}"))

    return state


# ============================================================================
# NODE 4: COMPLIANCE & ACTION ORCHESTRATION
# ============================================================================

def compliance_action_node(state: LoanUnderwritingState) -> LoanUnderwritingState:
    """
    Node 4: Generate case record and dispatch notification using NotificationSystem MCP.

    Calls the NotificationSystem agent to:
    - Generate unique case ID for audit trail
    - Create appropriate notification (approval/rejection/review) email
    - Determine action to take (documentation team / archive / manual review)
    - Timestamp case creation for compliance logging

    REASON FOR MCP: Deterministic case generation and notification templating.
    Creates structured records and notifications based on prior decision.
    Separate from LLM so compliance can audit exactly what message each applicant receives.
    """
    logger.info("=== NODE 4: COMPLIANCE & ACTION ===")

    applicant_id = state["applicant_data"].get("applicant_id", "UNKNOWN")
    logger.info(f"Starting compliance and action dispatch for {applicant_id}")

    # Call NotificationSystem MCP tool
    result = call_mcp_tool(
        notification_mcp,
        "dispatch_notification",
        {
            "decision_data": json.dumps(state["decision"]),
            "applicant_data": json.dumps(state["applicant_data"])
        }
    )

    # Parse result
    compliance_result = result if not result.get("error") else {"error": result.get("error")}
    state["compliance_result"] = compliance_result

    logger.info(f"Case created: {compliance_result.get('case_id', 'ERROR')}")

    # Append to messages
    summary = compliance_result.get("summary", str(compliance_result))
    state["messages"].append(AIMessage(content=f"[Agent 4: Compliance] {summary}"))

    return state


# ============================================================================
# NODE 5: LLM SYNTHESIS (FINAL VERDICT)
# ============================================================================

def llm_synthesis_node(state: LoanUnderwritingState) -> LoanUnderwritingState:
    """
    Node 5: LLM synthesis to create professional final verdict.

    Uses Claude Sonnet to:
    - Take all 4 agent outputs (profile, risk, decision, compliance)
    - Write a professional, human-readable final verdict
    - Explain the decision in plain English for applicant file
    - Incorporate key decision factors for clarity

    REASON FOR LLM: Subjective communication and explanation.
    After deterministic agents produce objective data, LLM is used ONLY to:
    - Write clear prose (not make decisions)
    - Explain reasoning to stakeholders
    - Tailor language for professional context
    The decision itself (Approve/Reject/Review) comes from Agent 3, not the LLM.
    """
    logger.info("=== NODE 5: LLM SYNTHESIS (FINAL VERDICT) ===")

    applicant_id = state["applicant_data"].get("applicant_id", "UNKNOWN")
    logger.info(f"Starting LLM synthesis for {applicant_id}")

    # Build rich context for LLM
    synthesis_prompt = f"""
You are a professional loan underwriting officer. Synthesize the following analysis results
into a clear, professional final verdict for the applicant file.

APPLICANT INFORMATION:
- ID: {state['applicant_data'].get('applicant_id')}
- Name: {state['applicant_data'].get('name')}
- Age: {state['applicant_data'].get('age')}
- Employment: {state['applicant_data'].get('employment_type')}
- Loan Amount: ${state['applicant_data'].get('loan_amount', 0):,.0f}

PROFILE ANALYSIS:
{json.dumps(state['profile_analysis'], indent=2)}

FINANCIAL RISK ANALYSIS:
{json.dumps(state['risk_analysis'], indent=2)}

DECISION SYNTHESIS:
{json.dumps(state['decision'], indent=2)}

COMPLIANCE RECORD:
{json.dumps(state['compliance_result'], indent=2)}

Please write a concise (3-5 sentences) professional verdict that:
1. Confirms the decision (Approve/Reject/Review)
2. Summarizes the key risk factors or positive attributes
3. Explains what happens next
4. Maintains a professional and empathetic tone

Format the response as a single cohesive paragraph suitable for inclusion in an applicant file.
"""

    # Invoke LLM
    messages = [HumanMessage(content=synthesis_prompt)]
    response = llm.invoke(messages)

    # Extract verdict
    final_verdict = response.content
    state["final_verdict"] = final_verdict

    logger.info(f"LLM synthesis complete: {len(final_verdict)} character verdict generated")

    # Append final verdict to messages
    state["messages"].append(AIMessage(content=f"[Final Verdict]\n{final_verdict}"))

    return state


# ============================================================================
# BUILD AND COMPILE GRAPH
# ============================================================================

def _build_graph():
    """Build the 5-node sequential LangGraph pipeline."""
    graph = StateGraph(LoanUnderwritingState)

    # Add all 5 nodes
    graph.add_node("applicant_analysis", applicant_analysis_node)
    graph.add_node("risk_analysis", risk_analysis_node)
    graph.add_node("decision_synthesis", decision_synthesis_node)
    graph.add_node("compliance_action", compliance_action_node)
    graph.add_node("llm_synthesis", llm_synthesis_node)

    # Add edges - sequential pipeline
    graph.add_edge(START, "applicant_analysis")
    graph.add_edge("applicant_analysis", "risk_analysis")
    graph.add_edge("risk_analysis", "decision_synthesis")
    graph.add_edge("decision_synthesis", "compliance_action")
    graph.add_edge("compliance_action", "llm_synthesis")
    graph.add_edge("llm_synthesis", END)

    return graph.compile()


# Compile the graph
chatbot = _build_graph()
logger.info("Multi-agent LangGraph orchestrator compiled successfully")

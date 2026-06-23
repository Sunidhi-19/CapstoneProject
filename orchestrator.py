"""
Multi-Agent LangGraph Orchestrator with MCP Integration.

CHANGE SUMMARY:
The orchestrator has been upgraded from a single-node LLM call to a 5-node multi-agent pipeline:

1. APPLICANT_ANALYSIS (ApplicantDB MCP)
   - Analyzes: income stability, employment risk, credit history, completeness
   - Why MCP: Deterministic rule-based logic (employment type → stability score)

2. RISK_ANALYSIS (RiskRulesDB MCP)
   - Analyzes: DTI ratio, credit risk, loan amount risk, anomalies
   - Why MCP: Standard lending formulas (amortization, DTI calculation)

3. DECISION_SYNTHESIS (DecisionSynthesis MCP)
   - Analyzes: risk score (weighted formula), classification, confidence, key factors
   - Why MCP: Transparent, auditable scoring with clear thresholds

4. COMPLIANCE_ACTION (NotificationSystem MCP)
   - Generates: case ID, notification email, action record
   - Why MCP: Ensures compliance - same message for same decision, no variation

5. LLM_SYNTHESIS (Claude Sonnet 4.6)
   - Synthesizes: professional final verdict from all agent outputs
   - Why LLM: ONLY for explaining decisions in clear prose, NOT for making decisions

All MCP servers run in-process (via fastmcp.Client) - no extra processes needed.
Each server can also run as standalone HTTP via new 'python main.py mcp-*' commands.

KEY CHANGES TO GATEWAY:
- State now includes: applicant_data, profile_analysis, risk_analysis, decision, compliance_result, final_verdict
- Handler must pass these fields to chatbot.invoke() (see gateway.py for details)
- API contract unchanged: still returns {"verdict": string}

KEY CHANGES TO CONFIG:
- LLM model switched from Haiku to Sonnet (only for final synthesis, not for every node)
- Added MCP_*_PORT environment variables for standalone HTTP deployment
"""

import json
from typing import TypedDict, Annotated
from datetime import datetime

from langgraph.graph import StateGraph, START, END
from langgraph.graph import add_messages
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_anthropic import ChatAnthropic
from dotenv import load_dotenv
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load API key for the LLM
load_dotenv()

my_api_key = os.getenv("ANTHROPIC_API_KEY")
base_url = os.getenv("BASE_URL")

# Import MCP servers
# In-process import: all MCP servers run via fastmcp.Client in memory
from src.mcps.applicant_db.server import applicant_mcp
from src.mcps.risk_rules_db.server import risk_mcp
from src.mcps.decision_synthesis.server import decision_mcp
from src.mcps.notification_system.server import notification_mcp
from src.mcps.mcp_bridge import call_mcp_tool


# ============================================================================
# UPDATED STATE SCHEMA - Multi-Agent Structured State
# ============================================================================

class LoanUnderwritingState(TypedDict):
    """
    Extended state schema for multi-agent loan underwriting pipeline.

    CHANGE: Added 6 new fields to carry agent outputs through the graph.
    Each node reads from prior nodes and writes its results to these fields.

    Fields:
    - messages: Chat history (for LLM context and audit trail)
    - applicant_data: Original loan application (dict)
    - profile_analysis: ApplicantDB output (dict)
    - risk_analysis: RiskRulesDB output (dict)
    - decision: DecisionSynthesis output (dict)
    - compliance_result: NotificationSystem output (dict)
    - final_verdict: LLM-written final verdict (string)
    """
    messages: Annotated[list[BaseMessage], add_messages]
    applicant_data: dict
    profile_analysis: dict
    risk_analysis: dict
    decision: dict
    compliance_result: dict
    final_verdict: str


# Instantiate the LLM - now using Sonnet instead of Haiku
# REASON: Sonnet provides better reasoning for final verdict synthesis.
# Agents 1-4 use MCP (no LLM), so only the synthesis step pays for Sonnet.
llm = ChatAnthropic(
    model=os.getenv("SONNET_MODEL", "global.anthropic.claude-sonnet-4-6"),
    api_key=my_api_key,
    base_url=base_url
)

logger.info("Initialized Claude Sonnet 4.6 for multi-agent orchestrator")


# ============================================================================
# NODE 1: APPLICANT ANALYSIS
# ============================================================================

def applicant_analysis_node(state: LoanUnderwritingState) -> LoanUnderwritingState:
    """
    Node 1: Analyze applicant profile using ApplicantDB MCP.

    CHANGE: Replaced hardcoded prompt logic with MCP call to ApplicantDB.

    This node calls the ApplicantDB MCP server to:
    - Calculate income stability score (Full-Time=0.9, Contract=0.6, Freelancer=0.4)
    - Determine employment risk (Low/Medium/High)
    - Generate credit history summary (Excellent/Good/Fair/Poor)
    - Check application completeness

    WHY MCP: All logic is deterministic and rule-based:
    - Employment type → stability score (lookup table)
    - Credit score band → rating (threshold checks)
    - Required fields → completeness flag (validation)
    No LLM needed; MCP makes logic auditable and consistent.
    """
    logger.info("=== NODE 1: APPLICANT ANALYSIS ===")

    applicant_id = state["applicant_data"].get("applicant_id", "UNKNOWN")
    logger.info(f"Analyzing applicant profile for {applicant_id}")

    # Call ApplicantDB MCP tool
    result = call_mcp_tool(
        applicant_mcp,
        "analyze_applicant_profile",
        {"applicant_data": json.dumps(state["applicant_data"])}
    )

    # Store result
    state["profile_analysis"] = result if not result.get("error") else {"error": result.get("error")}

    logger.info(f"Profile analysis: {state['profile_analysis'].get('employment_risk', 'ERROR')} employment risk")

    # Add to message history for audit trail
    summary = state["profile_analysis"].get("profile_summary", str(state["profile_analysis"]))
    state["messages"] = [
        HumanMessage(content=f"Process loan application {applicant_id}"),
        AIMessage(content=f"[Agent 1: Applicant Profile]\n{summary}")
    ]

    return state


# ============================================================================
# NODE 2: FINANCIAL RISK ANALYSIS
# ============================================================================

def risk_analysis_node(state: LoanUnderwritingState) -> LoanUnderwritingState:
    """
    Node 2: Analyze financial risk using RiskRulesDB MCP.

    CHANGE: Replaced hardcoded calculations with MCP call to RiskRulesDB.

    This node calls the RiskRulesDB MCP server to:
    - Calculate DTI ratio (uses amortization formula: 7% APR, 5-year term)
    - Determine credit score risk level (Low/Medium/High)
    - Classify loan amount risk based on loan-to-income ratio
    - Detect financial anomalies (high DTI, unusual income-for-age, etc.)

    WHY MCP: All logic is financial formulas with clear thresholds:
    - DTI = (existing_liabilities + monthly_payment) / (annual_income / 12)
    - Monthly payment = amortization formula at fixed rate
    - Risk levels = predetermined thresholds (e.g., DTI > 50% = "Very High")
    MCP keeps financial logic separate, versioned, and auditable.
    """
    logger.info("=== NODE 2: FINANCIAL RISK ANALYSIS ===")

    applicant_id = state["applicant_data"].get("applicant_id", "UNKNOWN")
    logger.info(f"Analyzing financial risk for {applicant_id}")

    # Call RiskRulesDB MCP tool
    result = call_mcp_tool(
        risk_mcp,
        "analyze_financial_risk",
        {
            "applicant_data": json.dumps(state["applicant_data"]),
            "profile_analysis": json.dumps(state["profile_analysis"])
        }
    )

    # Store result
    state["risk_analysis"] = result if not result.get("error") else {"error": result.get("error")}

    logger.info(f"Financial risk: DTI {state['risk_analysis'].get('debt_to_income_ratio', 'N/A')}%")

    # Add to message history
    summary = state["risk_analysis"].get("financial_summary", str(state["risk_analysis"]))
    state["messages"].append(AIMessage(content=f"[Agent 2: Financial Risk]\n{summary}"))

    return state


# ============================================================================
# NODE 3: DECISION SYNTHESIS
# ============================================================================

def decision_synthesis_node(state: LoanUnderwritingState) -> LoanUnderwritingState:
    """
    Node 3: Synthesize preliminary decision using DecisionSynthesis MCP.

    CHANGE: Replaced ad-hoc decision logic with structured MCP-based scoring.

    This node calls the DecisionSynthesis MCP server to:
    - Calculate composite risk score (0-100) using weighted formula:
      * DTI: 40% weight → penalties based on thresholds
      * Credit score: 30% weight → Low/Medium/High risk
      * Employment stability: 15% weight → stability score
      * Loan amount risk: 15% weight → loan-to-income ratio
    - Classify decision: Approve (< 25) / Review (25-54) / Reject (≥ 55)
    - Calculate confidence level (1.0 - risk_score/100)
    - Extract key decision factors for explainability

    WHY MCP: Decision logic is deterministic and must be:
    - Transparent: auditors must understand the scoring formula
    - Consistent: same inputs always produce same decision
    - Explainable: key factors list shows why decision was made
    - Compliant: score and classification separate from LLM synthesis
    MCP ensures the decision is not influenced by LLM randomness or prompt injection.
    """
    logger.info("=== NODE 3: DECISION SYNTHESIS ===")

    applicant_id = state["applicant_data"].get("applicant_id", "UNKNOWN")
    logger.info(f"Synthesizing decision for {applicant_id}")

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

    # Store result
    state["decision"] = result if not result.get("error") else {"error": result.get("error")}

    logger.info(f"Decision: {state['decision'].get('classification', 'ERROR')} "
                f"(Risk: {state['decision'].get('risk_score', 'N/A')}/100)")

    # Add to message history
    summary = state["decision"].get("decision_rationale", str(state["decision"]))
    state["messages"].append(AIMessage(content=f"[Agent 3: Decision]\n{summary}"))

    return state


# ============================================================================
# NODE 4: COMPLIANCE & ACTION ORCHESTRATION
# ============================================================================

def compliance_action_node(state: LoanUnderwritingState) -> LoanUnderwritingState:
    """
    Node 4: Generate case record using NotificationSystem MCP.

    CHANGE: Replaced ad-hoc notification logic with MCP-based case management.

    This node calls the NotificationSystem MCP server to:
    - Generate unique case ID (CASE-XXXXXXXX) for audit trail
    - Create decision-appropriate notification email
      * Approve: congratulations + next steps
      * Reject: professional decline + appeal info
      * Review: manual review notification + SLA
    - Record action taken for compliance logging
    - Timestamp case creation

    WHY MCP: Compliance requires consistent, auditable messaging:
    - Same decision → same message template (no variation from LLM)
    - Separate from synthesis → legal team can review templates independently
    - Audit trail → case ID ties to decision and notification
    - Versioning → notification templates can be updated without code changes
    """
    logger.info("=== NODE 4: COMPLIANCE & ACTION ===")

    applicant_id = state["applicant_data"].get("applicant_id", "UNKNOWN")
    logger.info(f"Dispatching compliance action for {applicant_id}")

    # Call NotificationSystem MCP tool
    result = call_mcp_tool(
        notification_mcp,
        "dispatch_notification",
        {
            "decision_data": json.dumps(state["decision"]),
            "applicant_data": json.dumps(state["applicant_data"])
        }
    )

    # Store result
    state["compliance_result"] = result if not result.get("error") else {"error": result.get("error")}

    logger.info(f"Case created: {state['compliance_result'].get('case_id', 'ERROR')}")

    # Add to message history
    summary = state["compliance_result"].get("summary", str(state["compliance_result"]))
    state["messages"].append(AIMessage(content=f"[Agent 4: Compliance]\n{summary}"))

    return state


# ============================================================================
# NODE 5: LLM SYNTHESIS (FINAL VERDICT)
# ============================================================================

def llm_synthesis_node(state: LoanUnderwritingState) -> LoanUnderwritingState:
    """
    Node 5: LLM synthesis to write professional final verdict.

    CHANGE: Added new node specifically for LLM synthesis (Sonnet).
    LLM is called ONLY here, not in earlier nodes.

    This node uses Claude Sonnet to:
    - Read all 4 agent outputs (profile, risk, decision, compliance)
    - Write a professional, concise final verdict (3-5 sentences)
    - Explain the decision in plain English for the applicant file
    - Incorporate key factors for transparency
    - Maintain professional and empathetic tone

    WHY LLM: Subjective communication and explanation, NOT decision-making.
    After deterministic agents produce objective data:
    - LLM writes the verdict for human consumption
    - LLM explains reasoning in professional language
    - LLM tailors tone and emphasis for context
    The decision itself (Approve/Reject/Review) comes from Agent 3, not the LLM.
    This separation ensures decisions are not influenced by prompt injection or model hallucination.
    """
    logger.info("=== NODE 5: LLM SYNTHESIS (FINAL VERDICT) ===")

    applicant_id = state["applicant_data"].get("applicant_id", "UNKNOWN")
    logger.info(f"Generating final verdict for {applicant_id}")

    # Build rich context for LLM
    synthesis_prompt = f"""
You are a professional loan underwriting officer. Your task is to write a final verdict
summarizing the automated underwriting decision for the applicant file.

IMPORTANT: The decision (Approve/Reject/Review) has already been made by automated agents.
Your role is ONLY to explain the decision clearly and professionally. Do not second-guess the decision.

APPLICANT INFORMATION:
- ID: {state['applicant_data'].get('applicant_id')}
- Name: {state['applicant_data'].get('name')}
- Age: {state['applicant_data'].get('age')}
- Employment: {state['applicant_data'].get('employment_type')}
- Loan Amount: ${state['applicant_data'].get('loan_amount', 0):,.0f}
- Loan Duration: {state['applicant_data'].get('loan_duration_years')} years

AUTOMATED ANALYSIS RESULTS:

Profile Analysis:
{json.dumps(state['profile_analysis'], indent=2)}

Financial Risk Analysis:
{json.dumps(state['risk_analysis'], indent=2)}

Decision Synthesis (FINAL DECISION):
{json.dumps(state['decision'], indent=2)}

Compliance Record:
{json.dumps(state['compliance_result'], indent=2)}

WRITE A FINAL VERDICT that:
1. States the decision clearly (Approve/Reject/Review)
2. Summarizes the key factors influencing the decision
3. Explains what happens next for the applicant
4. Maintains a professional, clear, and empathetic tone

Format as a single cohesive paragraph (3-5 sentences) suitable for the applicant file.
"""

    # Invoke LLM for synthesis only
    messages = [HumanMessage(content=synthesis_prompt)]
    response = llm.invoke(messages)

    # Extract final verdict
    final_verdict = response.content
    state["final_verdict"] = final_verdict

    logger.info(f"Final verdict generated ({len(final_verdict)} characters)")

    # Add to message history
    state["messages"].append(AIMessage(content=f"[Final Verdict]\n{final_verdict}"))

    return state


# ============================================================================
# BUILD AND COMPILE GRAPH
# ============================================================================

def _build_graph():
    """
    Build the 5-node sequential LangGraph pipeline.

    CHANGE: Graph structure changed from linear 1-node to 5-node pipeline.
    Each node is specialized and can be updated independently.
    """
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
logger.info("Multi-agent LangGraph orchestrator compiled successfully (5-node pipeline)")
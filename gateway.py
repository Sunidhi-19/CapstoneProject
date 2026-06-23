from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field, StringConstraints
from typing import Annotated, Literal
from datetime import datetime

# Import HumanMessage to pass raw text safely into the LangGraph state
from langchain_core.messages import HumanMessage 
from orchestrator import chatbot

app = FastAPI(
    title="API Gateway / Validation Layer",
    description="Validates structural payload format and dispatches to LangChain Orchestrator.",
    version="1.2.0"
)

# Custom type annotations for robust data sanitization
CleanString = Annotated[str, StringConstraints(strip_whitespace=True, min_length=2)]
ApplicantIDString = Annotated[str, StringConstraints(strip_whitespace=True, pattern=r"^APP\d+$")]

class LoanApplicationSchema(BaseModel):
    applicant_id: ApplicantIDString
    name: CleanString
    age: int = Field(..., gt=20, le=50)
    location: CleanString
    employment_type: Literal["Full-Time", "Contract", "Freelancer"]
    gross_annual_income: float = Field(..., gt=0)
    existing_liabilities: float = Field(..., ge=0)
    credit_score: int = Field(..., ge=300, le=850)
    loan_amount: float = Field(..., gt=0)
    loan_duration_years: int = Field(..., ge=1, le=30)
    application_timestamp: datetime


def pass_to_orchestrator(data: dict) -> dict:
    """
    UPDATED: Passes validated application data to the multi-agent LangGraph orchestrator.

    CHANGE SUMMARY:
    The orchestrator now uses a 5-node pipeline instead of a single LLM call:
    1. ApplicantDB agent - analyzes profile (rule-based MCP)
    2. RiskRulesDB agent - calculates financial risk (formula-based MCP)
    3. DecisionSynthesis agent - synthesizes decision (scoring MCP)
    4. NotificationSystem agent - generates case record (MCP)
    5. LLM synthesis - writes final verdict (Claude Sonnet)

    IMPORTANT CHANGE TO STATE:
    The new LoanUnderwritingState schema includes structured fields for each agent:
    - applicant_data: original application
    - profile_analysis: agent 1 output
    - risk_analysis: agent 2 output
    - decision: agent 3 output
    - compliance_result: agent 4 output
    - final_verdict: agent 5 output (LLM synthesis)

    Gateway must initialize all these fields when invoking chatbot.invoke().
    The API contract remains unchanged: still returns {"verdict": string}.
    """
    # FIX: Convert datetime to string for JSON serialization
    # REASON: MCP tools use json.dumps() which cannot serialize datetime objects.
    # Pydantic validates the timestamp on input, so we just need to convert it for storage.
    if isinstance(data.get("application_timestamp"), datetime):
        data["application_timestamp"] = data["application_timestamp"].isoformat()

    # Initialize the structured state for multi-agent pipeline
    # REASON: Each node in the LangGraph reads from and writes to these fields.
    # They start empty and are populated as agents run sequentially.
    inputs = {
        "messages": [HumanMessage(content=f"Process loan application {data.get('applicant_id')}")],
        # Pass original application data to first node
        "applicant_data": data,
        # Initialize agent output fields (populated by orchestrator nodes)
        "profile_analysis": {},
        "risk_analysis": {},
        "decision": {},
        "compliance_result": {},
        "final_verdict": ""
    }

    # Invoke the 5-node orchestrator pipeline
    # Each node executes sequentially, reading and writing to the state above
    graph_output = chatbot.invoke(inputs)

    # Extract final verdict (written by node 5: llm_synthesis_node)
    # CHANGE: Previously extracted last message. Now explicitly access final_verdict field.
    final_verdict = graph_output.get("final_verdict", "Unable to generate verdict.")

    # Extract structured analysis for beautiful frontend display
    # CHANGE: Now returns full analysis so frontend can display approval/rejection prominently
    decision_data = graph_output.get("decision", {})
    risk_data = graph_output.get("risk_analysis", {})
    profile_data = graph_output.get("profile_analysis", {})

    return {
        "verdict": final_verdict,
        # NEW: Structured analysis for beautiful frontend rendering
        "analysis": {
            # Decision (most important - displayed prominently)
            "decision": {
                "classification": decision_data.get("classification", "Review"),
                "risk_score": decision_data.get("risk_score", 0),
                "risk_level": decision_data.get("risk_level", "Unknown"),
                "confidence_level": decision_data.get("confidence_level", 0),
                "key_factors": decision_data.get("key_decision_factors", []),
                "decision_reason": decision_data.get("decision_reason", "")
            },
            # Risk metrics
            "risk": {
                "debt_to_income_ratio": risk_data.get("debt_to_income_ratio", 0),
                "dti_rating": risk_data.get("dti_rating", "Unknown"),
                "credit_score_risk_level": risk_data.get("credit_score_risk_level", "Unknown"),
                "loan_amount_risk": risk_data.get("loan_amount_risk", "Unknown"),
                "anomalies_detected": risk_data.get("anomalies_detected", [])
            },
            # Profile summary
            "profile": {
                "employment_risk": profile_data.get("employment_risk", "Unknown"),
                "income_stability_score": profile_data.get("income_stability_score", 0),
                "credit_rating": profile_data.get("credit_history", {}).get("rating", "Unknown"),
                "application_completeness": profile_data.get("application_completeness", {})
            },
            # Compliance record
            "compliance": graph_output.get("compliance_result", {})
        }
    }


@app.post("/loan_approval", status_code=status.HTTP_200_OK)
async def evaluate_loan_application(application: LoanApplicationSchema):
    """
    Receives frontend payload, triggers automatic Pydantic 422 validations, 
    and hands off clean structural data to LangChain.
    """
    try:
        # Convert Pydantic object to a standard Python dictionary for LangChain compatibility
        sanitized_payload = application.model_dump()  # json request undergoes pydantic validation/transformation
        
        # Dispatch to your LangChain system
        orchestrator_response = pass_to_orchestrator(sanitized_payload)  # request passed to orchestrator
        
        return {
            "status": "Success",
            "backend_validated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "orchestrator_output": orchestrator_response
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"LangChain orchestration layer failure: {str(e)}"
        )
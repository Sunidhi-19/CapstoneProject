"""DecisionSynthesis MCP Server - Synthesizes loan decision from risk analysis."""

import json
from fastmcp import FastMCP
from src.logger import get_logger

logger = get_logger(__name__)

decision_mcp = FastMCP("DecisionSynthesis")


def calculate_risk_score(profile_analysis: dict, risk_analysis: dict) -> float:
    """
    Calculate composite risk score (0-100) from multiple dimensions.
    Weights:
    - DTI (40%): high risk if > 50%
    - Credit score (30%): high risk if < 650
    - Employment stability (15%): based on stability score
    - Loan amount risk (15%): based on loan-to-income ratio
    """
    risk_score = 0

    # DTI component (max 40 points)
    dti = risk_analysis.get("debt_to_income_ratio", 0)
    if dti > 50:
        risk_score += 40
    elif dti > 43:
        risk_score += 30
    elif dti > 36:
        risk_score += 15

    # Credit score component (max 30 points)
    credit_risk = risk_analysis.get("credit_score_risk_level", "Medium")
    if credit_risk == "High":
        risk_score += 30
    elif credit_risk == "Medium":
        risk_score += 15

    # Employment stability component (max 15 points)
    stability = profile_analysis.get("income_stability_score", 0.5)
    if stability < 0.5:
        risk_score += 15
    elif stability < 0.8:
        risk_score += 8

    # Loan amount risk component (max 15 points)
    loan_risk = risk_analysis.get("loan_amount_risk", "Low")
    if loan_risk == "High":
        risk_score += 15
    elif loan_risk == "Medium":
        risk_score += 8

    # Anomaly penalties (each anomaly adds 2 points, capped)
    anomaly_count = risk_analysis.get("anomaly_count", 0)
    anomaly_penalty = min(anomaly_count * 2, 20)
    risk_score += anomaly_penalty

    return min(risk_score, 100)  # Cap at 100


def classify_decision(risk_score: float) -> str:
    """Classify loan decision based on risk score."""
    if risk_score < 25:
        return "Approve"
    elif risk_score < 55:
        return "Review"
    else:
        return "Reject"


def calculate_confidence_level(risk_score: float) -> float:
    """Calculate confidence level (inverse of risk score)."""
    return round(1.0 - (risk_score / 100), 2)


def extract_key_factors(profile_analysis: dict, risk_analysis: dict) -> list:
    """Extract key decision factors from analysis."""
    factors = []

    # Profile factors
    employment_risk = profile_analysis.get("employment_risk", "")
    if employment_risk in ["High", "Medium"]:
        factors.append(f"Employment Risk ({employment_risk})")

    credit_rating = profile_analysis.get("credit_history", {}).get("rating", "")
    if credit_rating in ["Poor", "Fair"]:
        factors.append(f"Credit Rating ({credit_rating})")

    # Risk factors
    dti = risk_analysis.get("debt_to_income_ratio", 0)
    if dti > 43:
        factors.append(f"High DTI ({dti:.1f}%)")

    # Anomalies
    anomalies = risk_analysis.get("anomalies_detected", [])
    if anomalies:
        factors.append(f"{len(anomalies)} Financial Anomalies")

    # Positive factors
    if profile_analysis.get("income_stability_score", 0) >= 0.8:
        factors.append("Stable Income")

    if profile_analysis.get("credit_history", {}).get("rating") in ["Excellent", "Good"]:
        factors.append("Strong Credit History")

    if dti <= 36:
        factors.append("Acceptable DTI")

    return factors if factors else ["Standard Underwriting"]


@decision_mcp.tool
def synthesize_loan_decision(applicant_data: str, profile_analysis: str, risk_analysis: str) -> str:
    """
    Synthesize final loan decision from profile and risk analysis.

    Args:
        applicant_data: JSON string with applicant profile
        profile_analysis: JSON string with profile analysis results
        risk_analysis: JSON string with financial risk analysis results

    Returns:
        JSON string with decision synthesis including classification, risk score,
        confidence level, and key decision factors
    """
    try:
        data = json.loads(applicant_data) if isinstance(applicant_data, str) else applicant_data
        profile = json.loads(profile_analysis) if isinstance(profile_analysis, str) else profile_analysis
        risk = json.loads(risk_analysis) if isinstance(risk_analysis, str) else risk_analysis

        logger.info(f"Synthesizing decision for {data.get('applicant_id')}")

        # Calculate risk score
        risk_score = calculate_risk_score(profile, risk)

        # Classify decision
        classification = classify_decision(risk_score)

        # Calculate confidence
        confidence = calculate_confidence_level(risk_score)

        # Extract key factors
        key_factors = extract_key_factors(profile, risk)

        result = {
            "applicant_id": data.get("applicant_id"),
            "classification": classification,
            "risk_score": round(risk_score, 1),
            "risk_level": "Low" if risk_score < 25 else "Medium" if risk_score < 55 else "High",
            "confidence_level": confidence,
            "key_decision_factors": key_factors,
            "decision_rationale": f"{classification} - Risk Score: {risk_score:.1f}/100. Primary factors: {', '.join(key_factors[:3])}."
        }

        logger.info(f"Decision synthesized: {classification} (Risk: {risk_score:.1f}, Confidence: {confidence})")
        return json.dumps(result)

    except Exception as e:
        logger.error(f"Error synthesizing decision: {str(e)}", exc_info=True)
        return json.dumps({"error": str(e), "status": "failed"})


if __name__ == "__main__":
    # Run as standalone HTTP MCP server (for production deployment)
    decision_mcp.run(transport="streamable-http", port=8003)

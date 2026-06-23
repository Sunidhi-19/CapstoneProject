"""ApplicantDB MCP Server - Analyzes applicant profile and employment history."""

import json
from fastmcp import FastMCP
from src.logger import get_logger

logger = get_logger(__name__)

applicant_mcp = FastMCP("ApplicantDB")


def calculate_income_stability_score(employment_type: str) -> float:
    """Calculate income stability based on employment type (0.0 - 1.0)."""
    stability_map = {
        "Full-Time": 0.9,
        "Contract": 0.6,
        "Freelancer": 0.4
    }
    return stability_map.get(employment_type, 0.5)


def determine_employment_risk(stability_score: float) -> str:
    """Determine employment risk level from stability score."""
    if stability_score >= 0.8:
        return "Low"
    elif stability_score >= 0.5:
        return "Medium"
    else:
        return "High"


def get_credit_history_summary(credit_score: int) -> dict:
    """Generate credit history summary based on credit score."""
    if credit_score >= 750:
        return {
            "rating": "Excellent",
            "description": "Exceptional credit history",
            "score_range": "750+"
        }
    elif credit_score >= 700:
        return {
            "rating": "Good",
            "description": "Strong credit history with few issues",
            "score_range": "700-749"
        }
    elif credit_score >= 650:
        return {
            "rating": "Fair",
            "description": "Acceptable credit history with some concerns",
            "score_range": "650-699"
        }
    else:
        return {
            "rating": "Poor",
            "description": "Significant credit issues requiring attention",
            "score_range": "Below 650"
        }


def check_application_completeness(applicant_data: dict) -> dict:
    """Check for completeness flags in the application."""
    required_fields = [
        "applicant_id", "name", "age", "location", "employment_type",
        "gross_annual_income", "existing_liabilities", "credit_score",
        "loan_amount", "loan_duration_years"
    ]

    missing_fields = [f for f in required_fields if f not in applicant_data or applicant_data[f] is None]

    return {
        "is_complete": len(missing_fields) == 0,
        "missing_fields": missing_fields,
        "completeness_percentage": ((len(required_fields) - len(missing_fields)) / len(required_fields)) * 100
    }


@applicant_mcp.tool
def analyze_applicant_profile(applicant_data: str) -> str:
    """
    Analyze applicant profile and return income stability, employment risk,
    credit history summary, and application completeness flags.

    Args:
        applicant_data: JSON string containing applicant profile information

    Returns:
        JSON string with analysis results
    """
    try:
        data = json.loads(applicant_data) if isinstance(applicant_data, str) else applicant_data
        logger.info(f"Analyzing applicant profile for {data.get('applicant_id')}")

        # Calculate income stability
        stability_score = calculate_income_stability_score(data.get("employment_type", "Full-Time"))

        # Determine employment risk
        employment_risk = determine_employment_risk(stability_score)

        # Get credit history summary
        credit_history = get_credit_history_summary(data.get("credit_score", 650))

        # Check completeness
        completeness = check_application_completeness(data)

        result = {
            "applicant_id": data.get("applicant_id"),
            "income_stability_score": stability_score,
            "stability_rating": "Low-Risk" if stability_score >= 0.8 else "Medium-Risk" if stability_score >= 0.5 else "High-Risk",
            "employment_type": data.get("employment_type"),
            "employment_risk": employment_risk,
            "credit_history": credit_history,
            "application_completeness": completeness,
            "profile_summary": f"Applicant {data.get('name')} ({data.get('employment_type')}) with {credit_history['rating']} credit history and {employment_risk} employment risk."
        }

        logger.info(f"Profile analysis complete: {result['employment_risk']} employment risk")
        return json.dumps(result)

    except Exception as e:
        logger.error(f"Error analyzing applicant profile: {str(e)}", exc_info=True)
        return json.dumps({"error": str(e), "status": "failed"})


if __name__ == "__main__":
    # Run as standalone HTTP MCP server (for production deployment)
    applicant_mcp.run(transport="streamable-http", port=8001)

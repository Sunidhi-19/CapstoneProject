"""RiskRulesDB MCP Server - Analyzes financial risk metrics."""

import json
import math
from fastmcp import FastMCP
from src.logger import get_logger

logger = get_logger(__name__)

risk_mcp = FastMCP("RiskRulesDB")


def calculate_monthly_payment(principal: float, annual_rate: float = 0.07, years: int = 5) -> float:
    """
    Calculate estimated monthly loan payment using amortization formula.
    Default: 7% APR, 5-year term.
    """
    if years <= 0 or principal <= 0:
        return 0

    monthly_rate = annual_rate / 12
    num_payments = years * 12

    if monthly_rate == 0:
        return principal / num_payments

    monthly_payment = principal * (monthly_rate * (1 + monthly_rate) ** num_payments) / \
                      ((1 + monthly_rate) ** num_payments - 1)
    return monthly_payment


def calculate_dti_ratio(gross_annual_income: float, existing_liabilities: float, estimated_monthly_payment: float) -> float:
    """
    Calculate Debt-to-Income ratio.
    DTI = (existing_liabilities + estimated_monthly_payment) / (gross_annual_income / 12)
    """
    if gross_annual_income <= 0:
        return 999.0

    monthly_income = gross_annual_income / 12
    total_monthly_debt = existing_liabilities + estimated_monthly_payment

    return (total_monthly_debt / monthly_income) * 100


def get_credit_risk_level(credit_score: int) -> str:
    """Determine credit score risk level."""
    if credit_score >= 750:
        return "Low"
    elif credit_score >= 650:
        return "Medium"
    else:
        return "High"


def get_loan_amount_risk(loan_amount: float, gross_annual_income: float) -> str:
    """Determine loan amount risk based on loan-to-income ratio."""
    if gross_annual_income <= 0:
        return "High"

    loan_to_income = loan_amount / gross_annual_income

    if loan_to_income < 0.3:
        return "Low"
    elif loan_to_income < 0.5:
        return "Medium"
    else:
        return "High"


def detect_anomalies(data: dict) -> list:
    """Detect anomalies in applicant data that warrant attention."""
    anomalies = []

    # High DTI check
    monthly_income = data.get("gross_annual_income", 0) / 12 if data.get("gross_annual_income") else 0
    total_debt = data.get("existing_liabilities", 0) + calculate_monthly_payment(
        data.get("loan_amount", 0),
        0.07,
        data.get("loan_duration_years", 5)
    )

    dti = (total_debt / monthly_income * 100) if monthly_income > 0 else 999
    if dti > 50:
        anomalies.append(f"Very high DTI ratio: {dti:.1f}%")

    # Income-for-age check
    # TODO: Revisit age-based income validation - currently too vague
    # age = data.get("age", 30)
    # income = data.get("gross_annual_income", 0)
    # expected_income_range_min = age * 10000  # rough minimum expectation
    # expected_income_range_max = age * 50000  # rough maximum expectation
    #
    # if income < expected_income_range_min or income > expected_income_range_max:
    #     anomalies.append(f"Unusual income for age {age}: {income:,.0f}")

    # Liabilities check
    if data.get("existing_liabilities", 0) > monthly_income * 0.5:
        anomalies.append(f"Existing liabilities exceed 50% of monthly income")

    # Loan duration check
    if data.get("loan_duration_years", 0) > 25:
        anomalies.append(f"Long loan duration requested: {data.get('loan_duration_years')} years")

    return anomalies


@risk_mcp.tool
def analyze_financial_risk(applicant_data: str, profile_analysis: str = "") -> str:
    """
    Analyze financial risk metrics including DTI, credit risk, loan amount risk, and anomalies.

    Args:
        applicant_data: JSON string with applicant profile
        profile_analysis: JSON string with prior profile analysis (optional)

    Returns:
        JSON string with financial risk analysis
    """
    try:
        data = json.loads(applicant_data) if isinstance(applicant_data, str) else applicant_data
        logger.info(f"Analyzing financial risk for {data.get('applicant_id')}")

        # Calculate monthly payment
        monthly_payment = calculate_monthly_payment(
            data.get("loan_amount", 0),
            0.07,  # 7% APR
            data.get("loan_duration_years", 5)
        )

        # Calculate DTI
        dti_ratio = calculate_dti_ratio(
            data.get("gross_annual_income", 0),
            data.get("existing_liabilities", 0),
            monthly_payment
        )

        # Credit risk level
        credit_risk = get_credit_risk_level(data.get("credit_score", 650))

        # Loan amount risk
        loan_risk = get_loan_amount_risk(data.get("loan_amount", 0), data.get("gross_annual_income", 0))

        # Detect anomalies
        anomalies = detect_anomalies(data)

        result = {
            "applicant_id": data.get("applicant_id"),
            "debt_to_income_ratio": round(dti_ratio, 2),
            "dti_rating": "Acceptable" if dti_ratio <= 43 else "High" if dti_ratio <= 50 else "Very High",
            "credit_score_risk_level": credit_risk,
            "loan_amount_risk": loan_risk,
            "estimated_monthly_payment": round(monthly_payment, 2),
            "anomalies_detected": anomalies,
            "anomaly_count": len(anomalies),
            "financial_summary": f"DTI: {dti_ratio:.1f}% ({credit_risk} credit risk, {loan_risk} loan amount risk)"
        }

        logger.info(f"Financial risk analysis: DTI {dti_ratio:.1f}%, {len(anomalies)} anomalies detected")
        return json.dumps(result)

    except Exception as e:
        logger.error(f"Error analyzing financial risk: {str(e)}", exc_info=True)
        return json.dumps({"error": str(e), "status": "failed"})


if __name__ == "__main__":
    # Run as standalone HTTP MCP server (for production deployment)
    risk_mcp.run(transport="streamable-http", port=8002)

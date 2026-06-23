"""NotificationSystem MCP Server - Generates notifications and case records."""

import json
import uuid
from datetime import datetime
from fastmcp import FastMCP
from src.logger import get_logger

logger = get_logger(__name__)

notification_mcp = FastMCP("NotificationSystem")


def generate_case_id() -> str:
    """Generate unique case ID in CASE-XXXXXXXX format."""
    return f"CASE-{uuid.uuid4().hex[:8].upper()}"


def generate_notification_email(applicant_name: str, classification: str, reason: str) -> str:
    """Generate email notification text."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if classification == "Approve":
        subject = "Loan Approval - Congratulations!"
        body = f"""
Dear {applicant_name},

We are pleased to inform you that your loan application has been APPROVED.

Your application was reviewed by our automated underwriting system and meets our lending criteria.

Decision Details:
{reason}

Next Steps:
1. You will receive formal approval documents within 1-2 business days
2. Our loan officer will contact you to finalize documentation
3. Funds will be disbursed upon completion of final procedures

Thank you for choosing our services.

Generated: {timestamp}
"""
    elif classification == "Reject":
        subject = "Loan Application Status - Unable to Approve"
        body = f"""
Dear {applicant_name},

Thank you for submitting your loan application. Unfortunately, we are unable to approve your request at this time.

Decision Details:
{reason}

If you believe this decision should be reconsidered, please contact our lending team to discuss possible options.

Thank you for considering our services.

Generated: {timestamp}
"""
    else:  # Review
        subject = "Loan Application - Under Review"
        body = f"""
Dear {applicant_name},

Thank you for submitting your loan application. Your application has been marked for manual review by our underwriting team.

Review Details:
{reason}

A senior loan officer will contact you within 2-3 business days with additional information or requirements.

Thank you for your patience.

Generated: {timestamp}
"""

    return f"Subject: {subject}\n\n{body}"


@notification_mcp.tool
def dispatch_notification(decision_data: str, applicant_data: str = "") -> str:
    """
    Dispatch notification and create case record for applicant decision.

    Args:
        decision_data: JSON string with loan decision synthesis
        applicant_data: JSON string with applicant profile (optional)

    Returns:
        JSON string with notification and case record information
    """
    try:
        decision = json.loads(decision_data) if isinstance(decision_data, str) else decision_data
        applicant = json.loads(applicant_data) if isinstance(applicant_data, str) else applicant_data

        applicant_id = decision.get("applicant_id", "UNKNOWN")
        applicant_name = applicant.get("name", "Valued Customer") if applicant else "Valued Customer"
        classification = decision.get("classification", "Review")
        risk_score = decision.get("risk_score", 0)

        logger.info(f"Dispatching notification for {applicant_id}")

        # Generate case ID
        case_id = generate_case_id()

        # Generate notification
        notification_text = generate_notification_email(
            applicant_name,
            classification,
            decision.get("decision_rationale", "Application reviewed.")
        )

        # Determine action taken
        if classification == "Approve":
            action = "Approval notice generated. Case forwarded to documentation team."
        elif classification == "Reject":
            action = "Rejection letter generated. Case archived with appeal instructions provided."
        else:  # Review
            action = "Case flagged for manual review. Assigned to underwriting team for 2-3 day SLA."

        timestamp = datetime.now().isoformat()

        result = {
            "case_id": case_id,
            "applicant_id": applicant_id,
            "applicant_name": applicant_name,
            "classification": classification,
            "risk_score": risk_score,
            "action_taken": action,
            "notification_sent": True,
            "notification_type": "email",
            "notification_subject": f"Loan Application - {classification}",
            "timestamp": timestamp,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "case_status": "Active",
            "summary": f"[{case_id}] {applicant_name}: {classification} - Risk: {risk_score:.1f}/100. {action}"
        }

        logger.info(f"Notification dispatched: Case {case_id} - {classification}")
        return json.dumps(result)

    except Exception as e:
        logger.error(f"Error dispatching notification: {str(e)}", exc_info=True)
        return json.dumps({"error": str(e), "status": "failed"})


if __name__ == "__main__":
    # Run as standalone HTTP MCP server (for production deployment)
    notification_mcp.run(transport="streamable-http", port=8004)

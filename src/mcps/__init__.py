"""MCP Servers for loan underwriting agents."""

from src.mcps.applicant_db.server import applicant_mcp
from src.mcps.risk_rules_db.server import risk_mcp
from src.mcps.decision_synthesis.server import decision_mcp
from src.mcps.notification_system.server import notification_mcp

__all__ = ["applicant_mcp", "risk_mcp", "decision_mcp", "notification_mcp"]

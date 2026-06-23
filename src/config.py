"""Configuration management for the application."""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration."""

    # LLM Configuration
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    BASE_URL = os.getenv("BASE_URL")

    # Orchestrator uses Claude Sonnet 4.6 for final verdict synthesis (better reasoning than Haiku)
    # Earlier agents use deterministic rules via MCP, so only the final synthesis step needs an LLM
    SONNET_MODEL = os.getenv("SONNET_MODEL", "global.anthropic.claude-sonnet-4-6-20250514-v1:0")

    # Legacy model (deprecated - kept for backwards compatibility)
    LLM_MODEL = "global.anthropic.claude-haiku-4-5-20251001-v1:0"

    # API Configuration
    API_HOST = os.getenv("API_HOST", "127.0.0.1")
    API_PORT = int(os.getenv("API_PORT", 8000))
    API_TITLE = "Loan Underwriting - API Gateway"
    API_VERSION = "1.2.0"

    # Frontend Configuration
    FRONTEND_TITLE = "Loan Underwriting Portal"
    BACKEND_URL = f"http://{API_HOST}:{API_PORT}/loan_approval"

    # MCP Server Ports (for standalone HTTP microservice deployment)
    # In-process mode (default) uses no ports; HTTP mode uses these
    MCP_APPLICANT_DB_PORT = int(os.getenv("MCP_APPLICANT_DB_PORT", 8001))
    MCP_RISK_RULES_DB_PORT = int(os.getenv("MCP_RISK_RULES_DB_PORT", 8002))
    MCP_DECISION_SYNTHESIS_PORT = int(os.getenv("MCP_DECISION_SYNTHESIS_PORT", 8003))
    MCP_NOTIFICATION_SYSTEM_PORT = int(os.getenv("MCP_NOTIFICATION_SYSTEM_PORT", 8004))

    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

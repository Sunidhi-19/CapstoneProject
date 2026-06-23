"""
Entry point to run application services.

UPDATED: Now supports MCP server launches for production deployment.

Services:
- backend: FastAPI gateway + orchestrator
- frontend: Streamlit UI
- mcp-applicant: ApplicantDB MCP (HTTP server on port 8001)
- mcp-risk: RiskRulesDB MCP (HTTP server on port 8002)
- mcp-decision: DecisionSynthesis MCP (HTTP server on port 8003)
- mcp-notification: NotificationSystem MCP (HTTP server on port 8004)

USAGE:

Development (in-process MCP, no extra processes):
  python main.py backend
  python main.py frontend

Production (MCP as standalone HTTP microservices):
  Terminal 1: python main.py mcp-applicant
  Terminal 2: python main.py mcp-risk
  Terminal 3: python main.py mcp-decision
  Terminal 4: python main.py mcp-notification
  Terminal 5: python main.py backend
  Terminal 6: python main.py frontend
"""

import sys
import subprocess
import os
import threading
import time

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from src.config import Config
except ImportError:
    # Fallback config if src structure not available
    class Config:
        API_HOST = "127.0.0.1"
        API_PORT = 8000
        BACKEND_URL = "http://127.0.0.1:8000/loan_approval"
        MCP_APPLICANT_DB_PORT = 8001
        MCP_RISK_RULES_DB_PORT = 8002
        MCP_DECISION_SYNTHESIS_PORT = 8003
        MCP_NOTIFICATION_SYSTEM_PORT = 8004


def run_backend():
    """Run the FastAPI backend server."""
    print(f"\n{'='*60}")
    print(f"Starting FastAPI backend on http://{Config.API_HOST}:{Config.API_PORT}")
    print(f"API docs available at http://{Config.API_HOST}:{Config.API_PORT}/docs")
    print(f"{'='*60}\n")
    subprocess.run(
        [
            "uvicorn",
            "gateway:app",
            "--host", Config.API_HOST,
            "--port", str(Config.API_PORT),
            "--reload"
        ]
    )


def run_frontend():
    """Run the Streamlit frontend."""
    print(f"\n{'='*60}")
    print(f"Starting Streamlit frontend")
    print(f"Backend URL: {Config.BACKEND_URL}")
    print(f"{'='*60}\n")
    subprocess.run(
        [
            "streamlit",
            "run",
            "frontend.py",
            "--logger.level=info"
        ]
    )


def run_mcp_applicant():
    """
    Run ApplicantDB MCP server as standalone HTTP microservice.

    REASON: Allows ApplicantDB to scale independently in production.
    Port can be configured via MCP_APPLICANT_DB_PORT environment variable.
    """
    print(f"\n{'='*60}")
    print(f"Starting ApplicantDB MCP Server (HTTP)")
    print(f"Listening on port {Config.MCP_APPLICANT_DB_PORT}")
    print(f"Protocol: streamable-http (MCP 1.0)")
    print(f"{'='*60}\n")
    from src.mcps.applicant_db.server import applicant_mcp
    applicant_mcp.run(transport="streamable-http", port=Config.MCP_APPLICANT_DB_PORT)


def run_mcp_risk():
    """
    Run RiskRulesDB MCP server as standalone HTTP microservice.

    REASON: Allows RiskRulesDB to scale independently in production.
    Port can be configured via MCP_RISK_RULES_DB_PORT environment variable.
    """
    print(f"\n{'='*60}")
    print(f"Starting RiskRulesDB MCP Server (HTTP)")
    print(f"Listening on port {Config.MCP_RISK_RULES_DB_PORT}")
    print(f"Protocol: streamable-http (MCP 1.0)")
    print(f"{'='*60}\n")
    from src.mcps.risk_rules_db.server import risk_mcp
    risk_mcp.run(transport="streamable-http", port=Config.MCP_RISK_RULES_DB_PORT)


def run_mcp_decision():
    """
    Run DecisionSynthesis MCP server as standalone HTTP microservice.

    REASON: Allows DecisionSynthesis to scale independently in production.
    Port can be configured via MCP_DECISION_SYNTHESIS_PORT environment variable.
    """
    print(f"\n{'='*60}")
    print(f"Starting DecisionSynthesis MCP Server (HTTP)")
    print(f"Listening on port {Config.MCP_DECISION_SYNTHESIS_PORT}")
    print(f"Protocol: streamable-http (MCP 1.0)")
    print(f"{'='*60}\n")
    from src.mcps.decision_synthesis.server import decision_mcp
    decision_mcp.run(transport="streamable-http", port=Config.MCP_DECISION_SYNTHESIS_PORT)


def run_mcp_notification():
    """
    Run NotificationSystem MCP server as standalone HTTP microservice.

    REASON: Allows NotificationSystem to scale independently in production.
    Port can be configured via MCP_NOTIFICATION_SYSTEM_PORT environment variable.
    """
    print(f"\n{'='*60}")
    print(f"Starting NotificationSystem MCP Server (HTTP)")
    print(f"Listening on port {Config.MCP_NOTIFICATION_SYSTEM_PORT}")
    print(f"Protocol: streamable-http (MCP 1.0)")
    print(f"{'='*60}\n")
    from src.mcps.notification_system.server import notification_mcp
    notification_mcp.run(transport="streamable-http", port=Config.MCP_NOTIFICATION_SYSTEM_PORT)


def run_all():
    """
    Run ALL services in parallel (MCPs + Backend + Frontend).

    REASON: For production deployment, start everything at once.
    Uses threading to run all services concurrently.

    Services started (in order):
    1. ApplicantDB MCP (Port 8001)
    2. RiskRulesDB MCP (Port 8002)
    3. DecisionSynthesis MCP (Port 8003)
    4. NotificationSystem MCP (Port 8004)
    5. FastAPI Backend (Port 8000)
    6. Streamlit Frontend (Port 8501)

    All run in the same process with separate threads.
    Stop all with Ctrl+C (SIGINT).
    """
    print(f"\n{'='*70}")
    print(f"🚀 STARTING ALL SERVICES (Production Mode)")
    print(f"{'='*70}\n")

    # Create list of services to run
    services = [
        ("ApplicantDB MCP", run_mcp_applicant, 1),
        ("RiskRulesDB MCP", run_mcp_risk, 2),
        ("DecisionSynthesis MCP", run_mcp_decision, 3),
        ("NotificationSystem MCP", run_mcp_notification, 4),
        ("FastAPI Backend", run_backend, 5),
        ("Streamlit Frontend", run_frontend, 6),
    ]

    print("Starting services:")
    for name, _, order in services:
        print(f"  {order}. {name}")

    print(f"\n{'='*70}")
    print(f"Waiting for services to initialize...")
    print(f"{'='*70}\n")

    threads = []

    # Start all services in separate threads
    for name, func, delay in services:
        # Stagger startup by 1 second per service
        thread = threading.Thread(
            target=lambda f=func, s=delay: (time.sleep(s * 0.5), f()),
            daemon=False  # Don't use daemon so Ctrl+C works properly
        )
        thread.start()
        threads.append((name, thread))
        print(f"✓ {name} thread started (will initialize in ~{delay*0.5}s)")

    print(f"\n{'='*70}")
    print(f"All services started!")
    print(f"{'='*70}\n")

    print("🌐 Access URLs:")
    print(f"  • Streamlit UI: http://127.0.0.1:8501")
    print(f"  • FastAPI Backend: http://127.0.0.1:8000")
    print(f"  • API Docs: http://127.0.0.1:8000/docs")
    print(f"\n🔧 MCP Services:")
    print(f"  • ApplicantDB: http://127.0.0.1:8001")
    print(f"  • RiskRulesDB: http://127.0.0.1:8002")
    print(f"  • DecisionSynthesis: http://127.0.0.1:8003")
    print(f"  • NotificationSystem: http://127.0.0.1:8004")

    print(f"\n⚠️  Press Ctrl+C to stop all services gracefully\n")

    # Keep main thread alive
    try:
        for name, thread in threads:
            thread.join()
    except KeyboardInterrupt:
        print(f"\n\n{'='*70}")
        print(f"⛔ Shutdown signal received. Stopping all services...")
        print(f"{'='*70}\n")
        # Threads are daemon=False, so they'll exit when main thread exits
        sys.exit(0)


def print_usage():
    """Print usage instructions."""
    print(f"""
{'='*70}
Loan Underwriting Platform - Service Launcher
{'='*70}

USAGE: python main.py [SERVICE]

QUICK START (All at once):
  python main.py all  # Start ALL services in parallel (recommended!)
                      # Equivalent to running 6 terminals at once

DEVELOPMENT MODE (in-process MCP, no extra processes):
  python main.py backend   # Start FastAPI gateway + orchestrator
  python main.py frontend  # Start Streamlit UI (requires backend running)

PRODUCTION MODE (MCP as standalone HTTP microservices):

Terminal 1:
  python main.py mcp-applicant    # ApplicantDB MCP (port {Config.MCP_APPLICANT_DB_PORT})

Terminal 2:
  python main.py mcp-risk         # RiskRulesDB MCP (port {Config.MCP_RISK_RULES_DB_PORT})

Terminal 3:
  python main.py mcp-decision     # DecisionSynthesis MCP (port {Config.MCP_DECISION_SYNTHESIS_PORT})

Terminal 4:
  python main.py mcp-notification # NotificationSystem MCP (port {Config.MCP_NOTIFICATION_SYSTEM_PORT})

Terminal 5:
  python main.py backend          # FastAPI gateway

Terminal 6:
  python main.py frontend         # Streamlit UI

ARCHITECTURE:
  Streamlit UI → FastAPI Gateway → LangGraph Orchestrator
                                        ↓
                    ┌─────────────────────────────────┐
                    │   5-Node Agent Pipeline          │
                    ├─────────────────────────────────┤
                    │ 1. Applicant Analysis (MCP)      │
                    │ 2. Risk Analysis (MCP)           │
                    │ 3. Decision Synthesis (MCP)      │
                    │ 4. Compliance & Action (MCP)     │
                    │ 5. LLM Synthesis (Sonnet)        │
                    └─────────────────────────────────┘

In development mode, MCPs run in-process (no extra processes).
In production mode, MCPs run as independent HTTP microservices (scalable).

{'='*70}
""")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        service = sys.argv[1].lower()

        if service == "all":
            run_all()
        elif service == "backend":
            run_backend()
        elif service == "frontend":
            run_frontend()
        elif service == "mcp-applicant":
            run_mcp_applicant()
        elif service == "mcp-risk":
            run_mcp_risk()
        elif service == "mcp-decision":
            run_mcp_decision()
        elif service == "mcp-notification":
            run_mcp_notification()
        elif service in ["-h", "--help", "help"]:
            print_usage()
        else:
            print(f"Unknown service: {service}")
            print_usage()
    else:
        print_usage()

# Quick Start Guide - Multi-Agent MCP Integration

## What Was Built

A **5-node multi-agent loan underwriting system** where:
- Nodes 1-4: Deterministic analysis via MCP servers (no LLM)
- Node 5: LLM synthesis to write professional verdict

## Architecture

```
User Form
   ↓
FastAPI Gateway (validates, initializes state)
   ↓
┌─── LangGraph Orchestrator (5-node pipeline) ───┐
│                                                 │
│ Node 1: Applicant Profile (ApplicantDB MCP)    │
│         ↓                                       │
│ Node 2: Financial Risk (RiskRulesDB MCP)       │
│         ↓                                       │
│ Node 3: Decision Synthesis (DecisionSynthesis) │
│         ↓                                       │
│ Node 4: Case & Notifications (Notification)    │
│         ↓                                       │
│ Node 5: LLM Verdict (Claude Sonnet)            │
│                                                 │
└─────────────────────────────────────────────────┘
   ↓
Streamlit UI (displays verdict)
```

---

## Key Changes to Files

### 1. `orchestrator.py` ✅ UPDATED
- Changed from 1-node to **5-node pipeline**
- New state schema with structured fields (profile_analysis, risk_analysis, decision, compliance_result, final_verdict)
- Model upgraded: Haiku → **Sonnet** (only for Node 5 synthesis)
- Each node calls a specific MCP server

### 2. `gateway.py` ✅ UPDATED
- Handler now initializes all state fields (not just messages)
- Extracts `final_verdict` from state (not last message)
- API contract unchanged: still returns `{"verdict": string}`

### 3. `src/config.py` ✨ NEW
- Centralized config for Sonnet model
- MCP port definitions (8001-8004)
- Environment-overridable

### 4. `main.py` ✨ NEW
- Service launcher: `python main.py [backend|frontend|mcp-*]`
- MCP servers: ApplicantDB, RiskRulesDB, DecisionSynthesis, NotificationSystem

### 5. `src/mcps/` ✨ 4 NEW MCP SERVERS
Each with 1 specialized tool (@mcp.tool decorator):

| MCP | Tool | Output |
|-----|------|--------|
| **ApplicantDB** | analyze_applicant_profile | Profile analysis (stability, risk, credit, completeness) |
| **RiskRulesDB** | analyze_financial_risk | DTI, credit risk, loan risk, anomalies |
| **DecisionSynthesis** | synthesize_loan_decision | Risk score, classification, confidence, factors |
| **NotificationSystem** | dispatch_notification | Case ID, notification, action, timestamp |

---

## Files Created

```
NEW src/ structure:
├── src/config.py                 # Configuration
├── src/logger.py                 # Logging utility
└── src/mcps/                     # MCP package
    ├── mcp_bridge.py             # Sync wrapper for async MCP calls
    ├── applicant_db/
    │   ├── __init__.py
    │   └── server.py             # ApplicantDB MCP
    ├── risk_rules_db/
    │   ├── __init__.py
    │   └── server.py             # RiskRulesDB MCP
    ├── decision_synthesis/
    │   ├── __init__.py
    │   └── server.py             # DecisionSynthesis MCP
    └── notification_system/
        ├── __init__.py
        └── server.py             # NotificationSystem MCP

ROOT files updated:
├── orchestrator.py               # 5-node pipeline (updated)
├── gateway.py                    # State initialization (updated)
├── main.py                       # Service launcher (new)
├── frontend.py                   # No changes
├── requirements.txt              # No changes (fastmcp 3.4.2 already there)
```

---

## Running the System

### Development Mode (Simple - Recommended)

```bash
# Terminal 1: Start backend
python main.py backend
# Output: FastAPI running on http://127.0.0.1:8000
# MCPs run in-process (no extra processes)

# Terminal 2: Start frontend
python main.py frontend
# Opens Streamlit at http://127.0.0.1:8501
```

### Production Mode (Scalable)

```bash
# Terminal 1-4: Start MCP servers
python main.py mcp-applicant      # Port 8001
python main.py mcp-risk           # Port 8002
python main.py mcp-decision       # Port 8003
python main.py mcp-notification   # Port 8004

# Terminal 5: Start backend
python main.py backend

# Terminal 6: Start frontend
python main.py frontend
```

---

## Testing the Integration

### Step 1: Submit Form
- Go to http://127.0.0.1:8501
- Fill in applicant details
- Click "Submit"

### Step 2: Watch Logs
```
INFO - === NODE 1: APPLICANT ANALYSIS ===
INFO - Analyzing applicant profile for APP12345
INFO - Profile analysis complete: Low employment risk

INFO - === NODE 2: FINANCIAL RISK ANALYSIS ===
INFO - Analyzing financial risk for APP12345
INFO - Financial risk analysis: DTI 35.2%, 1 anomalies detected

INFO - === NODE 3: DECISION SYNTHESIS ===
INFO - Synthesizing decision for APP12345
INFO - Decision synthesized: Approve (Risk: 18.5/100, Confidence: 0.815)

INFO - === NODE 4: COMPLIANCE & ACTION ===
INFO - Dispatching compliance action for APP12345
INFO - Case created: CASE-A1B2C3D4

INFO - === NODE 5: LLM SYNTHESIS (FINAL VERDICT) ===
INFO - Generating final verdict for APP12345
INFO - Final verdict generated (487 characters)
```

### Step 3: View Result
Streamlit shows:
```json
{
  "status": "Success",
  "backend_validated_at": "2026-06-22 14:30:00",
  "orchestrator_output": {
    "verdict": "We are pleased to inform you that your loan application has been APPROVED..."
  }
}
```

---

## Why These Changes?

| Question | Answer |
|----------|--------|
| Why 5 nodes instead of 1? | **Separation of concerns**: each agent specializes in one task. Nodes 1-4 do analysis, Node 5 explains. |
| Why MCP for nodes 1-4? | **Auditability**: deterministic rules, not LLM randomness. Compliance requirement. |
| Why Sonnet for node 5 only? | **Cost**: Agents 1-4 cost zero tokens (MCP). Sonnet used only for synthesis (better reasoning). |
| Why structured state? | **Audit trail**: each agent output becomes input to next. Complete traceability. |
| Why HTTP MCPs optional? | **Flexibility**: dev uses simple in-process, prod uses scalable HTTP microservices. |
| Why gateway unchanged? | **Backward compat**: API still returns `{"verdict": string}`. Frontend needs no changes. |

---

## State Flow Example

```
Initial State (from gateway):
{
  "messages": [...],
  "applicant_data": {"applicant_id": "APP12345", "age": 35, ...},
  "profile_analysis": {},
  "risk_analysis": {},
  "decision": {},
  "compliance_result": {},
  "final_verdict": ""
}

After Node 1 (ApplicantDB):
{
  "profile_analysis": {
    "employment_risk": "Low",
    "income_stability_score": 0.9,
    "credit_history": {"rating": "Good"},
    ...
  }
  # Other fields unchanged
}

After Node 2 (RiskRulesDB):
{
  "risk_analysis": {
    "debt_to_income_ratio": 35.2,
    "credit_score_risk_level": "Low",
    "anomaly_count": 0,
    ...
  }
  # profile_analysis, applicant_data unchanged
}

After Node 3 (DecisionSynthesis):
{
  "decision": {
    "classification": "Approve",
    "risk_score": 18.5,
    "confidence_level": 0.815,
    ...
  }
}

After Node 4 (NotificationSystem):
{
  "compliance_result": {
    "case_id": "CASE-A1B2C3D4",
    "action_taken": "Approval notice generated...",
    ...
  }
}

After Node 5 (LLM Synthesis):
{
  "final_verdict": "We are pleased to inform you that your loan application..."
}

Return to Gateway:
{"verdict": "We are pleased to inform you..."}
```

---

## Environment Setup

Add to `.env`:
```env
ANTHROPIC_API_KEY=sk-...
BASE_URL=https://llmgw-wp.tekstac.com

# Optional (defaults shown):
SONNET_MODEL=global.anthropic.claude-sonnet-4-6-20250514-v1:0
MCP_APPLICANT_DB_PORT=8001
MCP_RISK_RULES_DB_PORT=8002
MCP_DECISION_SYNTHESIS_PORT=8003
MCP_NOTIFICATION_SYSTEM_PORT=8004
LOG_LEVEL=INFO
```

---

## Next Steps

1. ✅ Run `python main.py backend` + `python main.py frontend`
2. ✅ Submit a loan application
3. ✅ Watch the 5 nodes execute sequentially
4. ✅ View the final verdict

---

## Documentation

- **`MCP_INTEGRATION_SUMMARY.md`**: Detailed architecture and design decisions
- **`CHANGES_AND_REASONS.md`**: Line-by-line changes with reasoning
- **`QUICK_START.md`**: This file

---

## Support

If the system doesn't work:

1. **Check imports**: Ensure `src/` structure exists with `__init__.py` files
2. **Check logs**: Look for error messages in the terminal
3. **Test MCP individually**: Try `python -c "from src.mcps.applicant_db.server import applicant_mcp; print('OK')"`
4. **Check environment**: Ensure `.env` has `ANTHROPIC_API_KEY` and `BASE_URL`

---

## API Reference

### POST /loan_approval

**Request**:
```json
{
  "applicant_id": "APP12345",
  "name": "Jane Doe",
  "age": 35,
  "location": "New York, NY",
  "employment_type": "Full-Time",
  "gross_annual_income": 75000,
  "existing_liabilities": 450,
  "credit_score": 710,
  "loan_amount": 25000,
  "loan_duration_years": 5,
  "application_timestamp": "2026-06-22T14:30:00"
}
```

**Response**:
```json
{
  "status": "Success",
  "backend_validated_at": "2026-06-22 14:30:00",
  "orchestrator_output": {
    "verdict": "Professional loan decision summary..."
  }
}
```

---

Enjoy your multi-agent loan underwriting system! 🚀

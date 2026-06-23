# Loan Underwriting Platform - Multi-Agent MCP Integration

## 🎯 Overview

This is a **production-grade, multi-agent loan underwriting system** that uses **4 MCP (Model Context Protocol) servers** with a **LangGraph orchestrator** to make deterministic, auditable loan decisions.

### Key Innovation
Unlike traditional AI systems that call the LLM for every decision:
- **Agents 1-4** (MCP): Deterministic, rule-based analysis → **zero LLM tokens**
- **Agent 5** (LLM): Subjective explanation only → **one Sonnet call** (better quality than Haiku)

Result: Better decisions, lower cost, full auditability.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Streamlit Frontend                       │
│                  (Loan application form)                     │
└──────────────────────────┬──────────────────────────────────┘
                           │
                      POST /loan_approval
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                    FastAPI Gateway                           │
│             (Pydantic validation + state init)              │
└──────────────────────────┬──────────────────────────────────┘
                           │
                    chatbot.invoke(state)
                           │
┌──────────────────────────▼──────────────────────────────────┐
│        LangGraph Multi-Agent Orchestrator (5 nodes)          │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Node 1: applicant_analysis_node                            │
│  ├─ Calls: ApplicantDB MCP                                  │
│  ├─ Analyzes: income stability, employment, credit, app    │
│  └─ Output: profile_analysis                               │
│     │                                                       │
│  Node 2: risk_analysis_node                                 │
│  ├─ Calls: RiskRulesDB MCP                                  │
│  ├─ Calculates: DTI, credit risk, loan risk, anomalies      │
│  └─ Output: risk_analysis                                  │
│     │                                                       │
│  Node 3: decision_synthesis_node                            │
│  ├─ Calls: DecisionSynthesis MCP                            │
│  ├─ Scores: risk_score (0-100), classification decision     │
│  └─ Output: decision (Approve/Review/Reject)               │
│     │                                                       │
│  Node 4: compliance_action_node                             │
│  ├─ Calls: NotificationSystem MCP                           │
│  ├─ Generates: case ID, notification email, action record   │
│  └─ Output: compliance_result                              │
│     │                                                       │
│  Node 5: llm_synthesis_node                                 │
│  ├─ Calls: Claude Sonnet 4.6                                │
│  ├─ Writes: professional final verdict (3-5 sentences)      │
│  └─ Output: final_verdict                                  │
│                                                              │
└──────────────────────────┬──────────────────────────────────┘
                           │
                    {"verdict": "..."}
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                   Streamlit Frontend                         │
│               (Display final verdict)                        │
└─────────────────────────────────────────────────────────────┘
```

---

## 📦 What's Included

### Core Files (Updated)
- **`orchestrator.py`** ← MAJOR: 5-node pipeline (was single-node)
- **`gateway.py`** ← MINOR: State initialization (was prompt-building)
- **`frontend.py`** → No changes
- **`requirements.txt`** → No changes (fastmcp 3.4.2 already there)

### Configuration & Utilities (New)
- **`src/config.py`** - Centralized config (model, ports)
- **`src/logger.py`** - Logging utility
- **`src/mcps/mcp_bridge.py`** - Sync wrapper for async MCP calls
- **`main.py`** - Service launcher (backend, frontend, MCPs)

### 4 MCP Servers (New)
- **`src/mcps/applicant_db/server.py`** - Applicant profile analysis
- **`src/mcps/risk_rules_db/server.py`** - Financial risk metrics
- **`src/mcps/decision_synthesis/server.py`** - Loan decision scoring
- **`src/mcps/notification_system/server.py`** - Case management

### Documentation (New)
- **`QUICK_START.md`** - Getting started guide
- **`MCP_INTEGRATION_SUMMARY.md`** - Architecture & design
- **`CHANGES_AND_REASONS.md`** - Line-by-line changes with reasoning

---

## 🚀 Quick Start

### Development Mode (Recommended)

```bash
# Terminal 1: Start backend
python main.py backend

# Terminal 2: Start frontend
python main.py frontend

# Open http://127.0.0.1:8501 and submit a form
```

MCPs run **in-process** (no extra processes). Perfect for development.

### Production Mode (Scalable)

```bash
# Terminal 1-4: Start MCP microservices
python main.py mcp-applicant        # Port 8001
python main.py mcp-risk             # Port 8002
python main.py mcp-decision         # Port 8003
python main.py mcp-notification     # Port 8004

# Terminal 5: Start backend
python main.py backend

# Terminal 6: Start frontend
python main.py frontend
```

MCPs run as **HTTP microservices** (independently scalable).

---

## 🔄 5-Node Pipeline Explained

### Node 1: Applicant Analysis (MCP)
**Purpose**: Analyze applicant profile
**Why MCP?** Deterministic rules (employment type → stability score)
**Input**: applicant_data
**Output**: 
```json
{
  "income_stability_score": 0.9,
  "employment_risk": "Low",
  "credit_history": {"rating": "Good"},
  "application_completeness": {"is_complete": true}
}
```

### Node 2: Financial Risk Analysis (MCP)
**Purpose**: Calculate financial risk metrics
**Why MCP?** Standard formulas (DTI = (liabilities + payment) / income)
**Input**: applicant_data, profile_analysis
**Output**:
```json
{
  "debt_to_income_ratio": 35.2,
  "credit_score_risk_level": "Low",
  "loan_amount_risk": "Medium",
  "anomalies_detected": ["High DTI"]
}
```

### Node 3: Decision Synthesis (MCP)
**Purpose**: Synthesize preliminary decision
**Why MCP?** Auditable scoring (risk_score = weighted formula, thresholds)
**Input**: applicant_data, profile_analysis, risk_analysis
**Output**:
```json
{
  "classification": "Approve",
  "risk_score": 18.5,
  "confidence_level": 0.815,
  "key_decision_factors": ["Stable Income", "Acceptable DTI"]
}
```

### Node 4: Compliance & Action (MCP)
**Purpose**: Generate case record and notification
**Why MCP?** Consistency (same decision → same message)
**Input**: decision, applicant_data
**Output**:
```json
{
  "case_id": "CASE-A1B2C3D4",
  "action_taken": "Approval notice generated",
  "notification_sent": true,
  "summary": "[CASE-A1B2C3D4] Jane Doe: Approve - Risk: 18.5/100"
}
```

### Node 5: LLM Synthesis (Claude Sonnet)
**Purpose**: Write professional final verdict
**Why LLM?** Subjective explanation (cannot change decision from Node 3)
**Input**: ALL prior agent outputs
**Output**: 
```
"We are pleased to inform you that your loan application has been approved. 
Your strong credit history and stable employment, combined with an acceptable 
debt-to-income ratio, demonstrate your capacity to manage this loan. 
You will receive formal approval documents within 1-2 business days."
```

---

## 💰 Cost Comparison

| Metric | Before (Haiku) | After (MCP + Sonnet) |
|--------|----------------|---------------------|
| **Calls per app** | 1 (LLM) | 4 (MCP) + 1 (LLM) |
| **Tokens per app** | ~500 (Haiku) | ~2000 (Sonnet, synthesis only) |
| **Cost estimate** | $0.005 | $0.030 |
| **Decision quality** | Lower (Haiku)| Higher (Sonnet, but final step only) |
| **Auditability** | Black box | Transparent (each step documented) |
| **Consistency** | Variable (LLM randomness) | Fixed (deterministic rules) |

**Verdict**: Better quality, auditability, compliance. Small cost increase justified.

---

## 📋 State Schema

```python
class LoanUnderwritingState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    applicant_data: dict              # Original application
    profile_analysis: dict            # Node 1 output
    risk_analysis: dict               # Node 2 output
    decision: dict                    # Node 3 output
    compliance_result: dict           # Node 4 output
    final_verdict: str                # Node 5 output
```

Each node reads from prior nodes and writes to its field. Complete audit trail.

---

## 🔐 Security & Compliance

### Why MCP for Nodes 1-4?

1. **Auditability**: Every decision step is transparent and versioned
2. **Compliance**: Rules-based logic passes regulatory review
3. **No Hallucination**: LLM not involved in decision-making
4. **Consistency**: Same inputs always produce same output
5. **Explainability**: Key factors list explains the decision

### Why LLM for Node 5 Only?

1. **Not Decision-Making**: LLM only writes explanation (decision already made)
2. **Constrained**: Prompt explicitly states "do not second-guess the decision"
3. **Verifiable**: If LLM misbehaves, only the explanation changes (not decision)
4. **Professional**: Sonnet writes better prose than Haiku for formal communication

---

## 🔍 Example Flow

### Input (from frontend)
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

### Processing (logs)
```
INFO - === NODE 1: APPLICANT ANALYSIS ===
INFO - Profile analysis: Low employment risk, Good credit

INFO - === NODE 2: FINANCIAL RISK ANALYSIS ===
INFO - Financial risk: DTI 35.2%, 1 anomaly detected

INFO - === NODE 3: DECISION SYNTHESIS ===
INFO - Decision: Approve (Risk: 18.5/100, Confidence: 0.815)

INFO - === NODE 4: COMPLIANCE & ACTION ===
INFO - Case created: CASE-A1B2C3D4

INFO - === NODE 5: LLM SYNTHESIS ===
INFO - Final verdict generated (487 characters)
```

### Output (to frontend)
```json
{
  "status": "Success",
  "backend_validated_at": "2026-06-22 14:30:00",
  "orchestrator_output": {
    "verdict": "We are pleased to inform you that your loan application has been approved..."
  }
}
```

---

## 🛠️ Development

### Run Tests
```bash
# Check imports
python -c "from src.mcps.applicant_db.server import applicant_mcp; print('OK')"

# Test MCP tools individually
python -c "
from src.mcps.applicant_db.server import applicant_mcp
from src.mcps.mcp_bridge import call_mcp_tool
import json

data = {'applicant_id': 'APP123', 'employment_type': 'Full-Time', 'credit_score': 750}
result = call_mcp_tool(applicant_mcp, 'analyze_applicant_profile', {'applicant_data': json.dumps(data)})
print(result)
"
```

### Enable Debug Logging
```bash
# In .env
LOG_LEVEL=DEBUG

# Restart backend
python main.py backend
```

---

## 📚 Documentation Files

1. **`QUICK_START.md`** - 5-minute getting started
2. **`MCP_INTEGRATION_SUMMARY.md`** - Full architecture (20 min read)
3. **`CHANGES_AND_REASONS.md`** - Detailed changes with reasoning (30 min read)
4. **`README_MCP_INTEGRATION.md`** - This file

---

## 🎓 How to Modify

### Add a New MCP?
1. Create `src/mcps/my_agent/server.py`
2. Define tool with `@mcp.tool` decorator
3. Add new node in `orchestrator.py`
4. Add edge to pipeline
5. Add config to `src/config.py`

### Tweak Decision Scoring?
Edit `src/mcps/decision_synthesis/server.py` → `calculate_risk_score()` function
- Adjust weights (DTI 40%, Credit 30%, etc.)
- Modify thresholds (Approve < 25, Review < 55, etc.)
- All changes are versioned and auditable

### Change LLM Model?
1. Update `.env`: `SONNET_MODEL=claude-opus-4-8`
2. Or edit `src/config.py` default
3. Restart backend

---

## 🚨 Troubleshooting

### Import Error: `from src.mcps ...`
**Fix**: Ensure `src/` folder exists with `__init__.py` files
```bash
# Check structure
ls -la src/mcps/__init__.py
ls -la src/mcps/applicant_db/__init__.py
```

### MCP Tool Not Found
**Fix**: Restart backend (MCPs loaded at startup)
```bash
Ctrl+C
python main.py backend
```

### State Field Missing (KeyError)
**Fix**: Ensure gateway initializes all fields:
```python
inputs = {
    "applicant_data": data,
    "profile_analysis": {},      # ← Ensure all present
    "risk_analysis": {},
    "decision": {},
    "compliance_result": {},
    "final_verdict": ""
}
```

### LLM Not Responding
**Fix**: Check .env has `ANTHROPIC_API_KEY` and `BASE_URL`
```bash
# Test
python -c "from langchain_anthropic import ChatAnthropic; print('OK')"
```

---

## 🎯 Key Takeaways

✅ **Multi-agent architecture** - Specialized nodes for specialized tasks
✅ **Deterministic decisions** - Rules-based, not LLM-based (compliance)
✅ **Auditability** - Every decision step transparent and versioned
✅ **Cost-efficient** - MCPs use zero tokens; LLM only for synthesis
✅ **Scalable** - MCPs can be deployed independently as HTTP microservices
✅ **Backward compatible** - API unchanged; frontend needs no updates
✅ **Production-ready** - All features for regulatory compliance

---

## 📞 Support

- **Logs**: Check terminal output for error messages
- **Docs**: See linked README files above
- **Testing**: Use `python main.py [backend|frontend|mcp-*]` commands

---

**Built with LangGraph, FastMCP, and Claude Sonnet 4.6** 🚀

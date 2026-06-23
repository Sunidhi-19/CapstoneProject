# 🚀 Run All Services at Once

## Quick Start (One Command!)

```bash
python main.py all
```

That's it! This single command starts **everything** in parallel:
- ✅ ApplicantDB MCP (Port 8001)
- ✅ RiskRulesDB MCP (Port 8002)
- ✅ DecisionSynthesis MCP (Port 8003)
- ✅ NotificationSystem MCP (Port 8004)
- ✅ FastAPI Backend (Port 8000)
- ✅ Streamlit Frontend (Port 8501)

---

## What Happens

When you run `python main.py all`:

```
==================================================================================
🚀 STARTING ALL SERVICES (Production Mode)
==================================================================================

Starting services:
  1. ApplicantDB MCP
  2. RiskRulesDB MCP
  3. DecisionSynthesis MCP
  4. NotificationSystem MCP
  5. FastAPI Backend
  6. Streamlit Frontend

==================================================================================
Waiting for services to initialize...
==================================================================================

✓ ApplicantDB MCP thread started (will initialize in ~0.5s)
✓ RiskRulesDB MCP thread started (will initialize in ~1s)
✓ DecisionSynthesis MCP thread started (will initialize in ~1.5s)
✓ NotificationSystem MCP thread started (will initialize in ~2s)
✓ FastAPI Backend thread started (will initialize in ~2.5s)
✓ Streamlit Frontend thread started (will initialize in ~3s)

==================================================================================
All services started!
==================================================================================

🌐 Access URLs:
  • Streamlit UI: http://127.0.0.1:8501
  • FastAPI Backend: http://127.0.0.1:8000
  • API Docs: http://127.0.0.1:8000/docs

🔧 MCP Services:
  • ApplicantDB: http://127.0.0.1:8001
  • RiskRulesDB: http://127.0.0.1:8002
  • DecisionSynthesis: http://127.0.0.1:8003
  • NotificationSystem: http://127.0.0.1:8004

⚠️  Press Ctrl+C to stop all services gracefully
```

---

## Using the System

### 1. Open Streamlit UI
Once services are running, open your browser:
```
http://127.0.0.1:8501
```

### 2. Fill in the Loan Application Form
- Applicant ID: `APP12345`
- Full Name: `Jane Doe`
- Age: `35`
- Location: `New York, NY`
- Employment Type: `Full-Time`
- Gross Annual Income: `75000`
- Existing Liabilities: `450`
- Credit Score: `710`
- Loan Amount: `25000`
- Duration: `5` years

### 3. Click "Submit"

### 4. Watch the Magic Happen
- All 5 nodes execute sequentially
- Final verdict is displayed in Streamlit

---

## Terminal Output Explained

When you submit a loan application, you'll see in your terminal:

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

INFO - === NODE 5: LLM SYNTHESIS ===
INFO - Generating final verdict for APP12345
INFO - Final verdict generated (487 characters)
```

---

## Stopping All Services

### Graceful Shutdown
```bash
# Press Ctrl+C in the terminal
Ctrl+C
```

This will stop all services gracefully.

---

## Comparison: All Methods

| Method | Command | Pros | Cons |
|--------|---------|------|------|
| **Run All (Recommended)** | `python main.py all` | One command, clean output, production-ready | Runs in one terminal |
| **Development Mode** | 2 terminals: backend + frontend | Simple for dev, MCPs in-process | Need 2 terminals |
| **Production Mode** | 6 terminals: 4 MCPs + backend + frontend | Full scalability | Complex setup |

---

## Troubleshooting

### Problem: "Port already in use"
```bash
# Kill existing processes
pkill -f "python main.py"

# Then try again
python main.py all
```

### Problem: Some services not starting
```bash
# Check if all dependencies are installed
pip list | grep -E "fastapi|streamlit|langgraph|fastmcp"

# Or reinstall
pip install -r requirements.txt
```

### Problem: API key error
```bash
# Check .env has required keys
cat .env
# Should show: ANTHROPIC_API_KEY and BASE_URL

# Add if missing
echo 'ANTHROPIC_API_KEY=sk-your-key' >> .env
echo 'BASE_URL=https://llmgw-wp.tekstac.com' >> .env
```

### Problem: Streamlit not opening automatically
```bash
# Open manually in browser
http://127.0.0.1:8501
```

---

## Under the Hood

The `run_all()` function:

1. **Creates threads** for each service (6 total)
2. **Staggers startup** by 0.5 seconds per service (to avoid port conflicts)
3. **Runs all in parallel** in the same process
4. **Listens for Ctrl+C** to gracefully shutdown everything
5. **Prints URLs** so you know where to access each service

---

## Architecture When Running "All"

```
Single Command: python main.py all
         ↓
    Main Process (main.py)
         ↓
    ┌────────────────────────────────────┐
    │  6 Threads (all running in parallel)  │
    ├────────────────────────────────────┤
    │ Thread 1: ApplicantDB MCP (8001)   │
    │ Thread 2: RiskRulesDB MCP (8002)   │
    │ Thread 3: DecisionSynthesis (8003) │
    │ Thread 4: NotificationSystem (8004)│
    │ Thread 5: FastAPI Backend (8000)   │
    │ Thread 6: Streamlit Frontend (8501)│
    └────────────────────────────────────┘
         ↓
    All services accessible immediately
```

---

## Example Workflow

```bash
# 1. Navigate to project
cd /home/ubuntu/ClaudeTest/CapstoneProject

# 2. Activate environment (if needed)
source .venv/bin/activate

# 3. Run everything
python main.py all

# 4. Wait for "All services started!" message

# 5. Open browser: http://127.0.0.1:8501

# 6. Fill form and submit

# 7. View results in Streamlit

# 8. Stop with Ctrl+C
```

---

## Comparison with Manual Setup

### Before (Manual - 6 terminals):
```bash
# Terminal 1
python main.py mcp-applicant

# Terminal 2
python main.py mcp-risk

# Terminal 3
python main.py mcp-decision

# Terminal 4
python main.py mcp-notification

# Terminal 5
python main.py backend

# Terminal 6
python main.py frontend
```

### After (One command):
```bash
python main.py all
```

✅ Same result, one command!

---

## Summary

| Aspect | Before | After |
|--------|--------|-------|
| **Setup** | 6 terminals | 1 terminal |
| **Commands** | 6 different commands | 1 command |
| **Complexity** | High | Zero |
| **Learning curve** | Steep | Flat |
| **Result** | Same | Same |

**Recommendation**: Use `python main.py all` for everything! 🚀

---

## Still Want Individual Control?

If you need to run individual services:

```bash
python main.py backend         # FastAPI only
python main.py frontend        # Streamlit only
python main.py mcp-applicant   # ApplicantDB MCP only
python main.py mcp-risk        # RiskRulesDB MCP only
python main.py mcp-decision    # DecisionSynthesis MCP only
python main.py mcp-notification # NotificationSystem MCP only
```

But honestly? Just use:
```bash
python main.py all
```

You're welcome! 😊

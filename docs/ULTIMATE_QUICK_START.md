# 🚀 ULTIMATE QUICK START - Run Everything in One Command

## ⚡ TL;DR (Too Long; Didn't Read)

```bash
cd /home/ubuntu/ClaudeTest/CapstoneProject
source .venv/bin/activate
python main.py all
```

Then open: **http://127.0.0.1:8501**

Done! 🎉

---

## 📋 Step-by-Step Guide

### 1️⃣ Open Terminal

```bash
cd /home/ubuntu/ClaudeTest/CapstoneProject
```

### 2️⃣ Activate Virtual Environment

```bash
source .venv/bin/activate
```

You should see `(.venv)` in your terminal prompt.

### 3️⃣ Start Everything

```bash
python main.py all
```

### 4️⃣ Wait for Initialization

You'll see:
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

### 5️⃣ Open Streamlit UI

Click on: http://127.0.0.1:8501

Or open your browser and paste: `http://127.0.0.1:8501`

### 6️⃣ Fill in Loan Application

Enter test data:
```
Applicant ID:           APP12345
Full Name:              Jane Doe
Age:                    35
Location:               New York, NY
Employment Type:        Full-Time
Gross Annual Income:    75000
Existing Liabilities:   450
Credit Score:           710
Loan Amount:            25000
Duration (Years):       5
```

### 7️⃣ Click "Submit"

### 8️⃣ Watch It Work!

Back in your terminal, you'll see:

```
INFO - === NODE 1: APPLICANT ANALYSIS ===
INFO - Analyzing applicant profile for APP12345
INFO - Profile analysis: Low employment risk

INFO - === NODE 2: FINANCIAL RISK ANALYSIS ===
INFO - Financial risk analysis: DTI 35.2%, 1 anomalies detected

INFO - === NODE 3: DECISION SYNTHESIS ===
INFO - Decision: Approve (Risk: 18.5/100, Confidence: 0.815)

INFO - === NODE 4: COMPLIANCE & ACTION ===
INFO - Case created: CASE-A1B2C3D4

INFO - === NODE 5: LLM SYNTHESIS ===
INFO - Final verdict generated (487 characters)
```

### 9️⃣ View Result in Streamlit

The Streamlit page will display:

```json
{
  "status": "Success",
  "backend_validated_at": "2026-06-22 14:30:00",
  "orchestrator_output": {
    "verdict": "We are pleased to inform you that your loan application has been approved. Your strong credit history and stable employment, combined with an acceptable debt-to-income ratio, demonstrate your capacity to manage this loan. You will receive formal approval documents within 1-2 business days."
  }
}
```

✅ **DONE! System is working!**

### 🔟 Stop Everything

```bash
Ctrl+C
```

This will gracefully shut down all 6 services.

---

## 🎯 What Just Happened?

| Component | Port | Status |
|-----------|------|--------|
| ApplicantDB MCP | 8001 | ✅ Running |
| RiskRulesDB MCP | 8002 | ✅ Running |
| DecisionSynthesis MCP | 8003 | ✅ Running |
| NotificationSystem MCP | 8004 | ✅ Running |
| FastAPI Backend | 8000 | ✅ Running |
| Streamlit Frontend | 8501 | ✅ Running |

All 6 services started in **one terminal** with **one command**! 🚀

---

## 📊 The 5-Node Pipeline

When you submit a form:

```
User Form (Streamlit)
    ↓
FastAPI Gateway (validates data)
    ↓
Node 1: ApplicantDB → employment risk, credit history
    ↓
Node 2: RiskRulesDB → DTI, credit risk, anomalies
    ↓
Node 3: DecisionSynthesis → risk score, classification (Approve/Reject/Review)
    ↓
Node 4: NotificationSystem → case ID, notification
    ↓
Node 5: Claude Sonnet → professional final verdict
    ↓
Result displayed in Streamlit ✅
```

---

## 🆚 Old vs New

### Before (6 Terminals)
```
Terminal 1: python main.py mcp-applicant
Terminal 2: python main.py mcp-risk
Terminal 3: python main.py mcp-decision
Terminal 4: python main.py mcp-notification
Terminal 5: python main.py backend
Terminal 6: python main.py frontend
```

### After (1 Terminal)
```
python main.py all
```

**Same result, simpler setup!** ✨

---

## 🔧 Available Commands

```bash
python main.py all              # ⭐ Start EVERYTHING (recommended!)
python main.py backend          # Start FastAPI only
python main.py frontend         # Start Streamlit only
python main.py mcp-applicant    # Start ApplicantDB MCP only
python main.py mcp-risk         # Start RiskRulesDB MCP only
python main.py mcp-decision     # Start DecisionSynthesis MCP only
python main.py mcp-notification # Start NotificationSystem MCP only
python main.py help             # Show help
```

---

## 🐛 Troubleshooting

### "Port already in use"
```bash
# Kill existing processes
pkill -f "python main.py"

# Try again
python main.py all
```

### "Module not found" errors
```bash
# Reinstall dependencies
pip install -r requirements.txt

# Try again
python main.py all
```

### "ANTHROPIC_API_KEY not found"
```bash
# Check .env file
cat .env

# Should show:
# ANTHROPIC_API_KEY=sk-...
# BASE_URL=https://llmgw-wp.tekstac.com

# If missing, add them:
echo 'ANTHROPIC_API_KEY=sk-your-key' >> .env
echo 'BASE_URL=https://llmgw-wp.tekstac.com' >> .env
```

### Services not responding
```bash
# Give it 5 seconds to fully initialize
# Then try again

# Or restart:
Ctrl+C
python main.py all
```

---

## 📚 Documentation

- **This file**: ULTIMATE_QUICK_START.md (quick reference)
- **Full guide**: RUN_ALL_SERVICES.md (detailed documentation)
- **Architecture**: MCP_INTEGRATION_SUMMARY.md (how it works)
- **Changes**: CHANGES_AND_REASONS.md (what was modified)
- **Reference**: README_MCP_INTEGRATION.md (complete reference)

---

## 🎓 Key Concepts

### What is MCP?
Model Context Protocol - lets AI systems call external tools/databases.

### Why 4 MCP Servers?
- **ApplicantDB**: Analyzes applicant profile (employment, credit, etc.)
- **RiskRulesDB**: Calculates financial risk (DTI, credit risk, anomalies)
- **DecisionSynthesis**: Makes loan decision (Approve/Reject/Review)
- **NotificationSystem**: Generates notifications and case records

### Why Claude Sonnet?
Better reasoning than Haiku. Only used for final verdict (explanation), not decision-making.

### Why Threading?
Runs all 6 services in parallel in one terminal instead of 6 separate terminals.

---

## 💡 Pro Tips

1. **Leave terminal open** while testing
   ```bash
   # Terminal stays open while you test in browser
   # See real-time logs of 5-node pipeline
   ```

2. **Check API docs**
   ```
   http://127.0.0.1:8000/docs
   ```

3. **Multiple applications**
   ```bash
   # You can submit multiple applications
   # Each triggers the 5-node pipeline
   ```

4. **Use test data**
   ```
   APP12345, Jane Doe, 35, etc.
   Logs will show pipeline execution
   ```

5. **Read logs carefully**
   ```
   Terminal shows exactly what each node did
   Great for understanding the system
   ```

---

## 🎉 Summary

| Aspect | Details |
|--------|---------|
| **Command** | `python main.py all` |
| **Services** | 6 (4 MCPs + Backend + Frontend) |
| **Ports** | 8001-8004 (MCPs), 8000 (API), 8501 (UI) |
| **Setup Time** | 3-4 seconds |
| **Terminals Needed** | 1 |
| **Pipeline Nodes** | 5 |
| **Production Ready** | ✅ Yes |

---

## 🚀 You're All Set!

Just run:
```bash
python main.py all
```

Open:
```
http://127.0.0.1:8501
```

And you're ready to go! 🎉

---

**Questions?** Check the documentation files or examine the terminal logs when you submit a form.

**Happy underwriting!** 🏦

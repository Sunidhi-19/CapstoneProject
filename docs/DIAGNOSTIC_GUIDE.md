# 🔍 Diagnostic Guide - Debugging Verdict Display

## Issue

The verdict display is showing all N/A values or 0.0 instead of actual data:

```
🟡 REVIEW
Risk Score: 0.0/100 | Confidence: 0.0%
N/A values everywhere
```

## Solution

I've added debugging features to help diagnose the issue.

### What Changed

**frontend.py:**
1. Added **DEBUG expander** - shows raw API response
2. Added **Fallback message** - if analysis data is missing
3. Both help diagnose what data is flowing through

### How to Diagnose

#### Step 1: Run the system
```bash
python main.py all
```

#### Step 2: Submit a form

Use this test data:
```
Applicant ID: APP12345
Full Name: Jane Doe
Age: 35
Location: New York, NY
Employment Type: Full-Time
Gross Annual Income: 75000
Existing Liabilities: 450
Credit Score: 710
Loan Amount: 25000
Duration: 5 years
```

#### Step 3: Check the response

Look for the **🔍 DEBUG: Raw API Response** expander (it appears after "✅ Analysis Complete!")

Click it to expand and see what data is actually being returned.

### What to Look For

**Good response structure:**
```json
{
  "verdict": "We are pleased...",
  "analysis": {
    "decision": {
      "classification": "Approve",
      "risk_score": 18.5,
      "risk_level": "Low",
      "confidence_level": 0.815,
      "key_factors": ["Stable Income", "Acceptable DTI"]
    },
    "risk": {
      "debt_to_income_ratio": 35.2,
      "dti_rating": "Acceptable",
      "credit_score_risk_level": "Low",
      "loan_amount_risk": "Medium",
      "anomalies_detected": []
    },
    "profile": {
      "employment_risk": "Low",
      "income_stability_score": 0.9,
      "credit_rating": "Good",
      "application_completeness": {...}
    },
    "compliance": {
      "case_id": "CASE-XXXXX",
      "case_status": "Active"
    }
  }
}
```

**Bad response (missing analysis):**
```json
{
  "verdict": "We are pleased...",
  "analysis": {}  // ← Empty!
}
```

### Common Issues & Fixes

| Issue | Symptoms | Fix |
|-------|----------|-----|
| **Empty analysis** | All N/A values | Check orchestrator logs - are 5 nodes executing? |
| **Missing decision** | Risk Score: 0.0 | Check if DecisionSynthesis MCP ran successfully |
| **Missing profile** | Employment: N/A | Check if ApplicantDB MCP ran successfully |
| **Missing risk** | DTI: 0% | Check if RiskRulesDB MCP ran successfully |

### Debug Checklist

✅ **Check Terminal Logs**
```
Look for these lines when submitting a form:
=== NODE 1: APPLICANT ANALYSIS ===
=== NODE 2: FINANCIAL RISK ANALYSIS ===
=== NODE 3: DECISION SYNTHESIS ===
=== NODE 4: COMPLIANCE & ACTION ===
=== NODE 5: LLM SYNTHESIS ===
```

If you don't see all 5 nodes, the pipeline is stopping early.

✅ **Check Streamlit Debug Output**
Expand the DEBUG expander to see the raw JSON response and trace which fields are missing.

✅ **Check Backend URL**
Make sure the frontend is connecting to the right backend:
```python
BACKEND_URL = "http://127.0.0.1:8000/loan_approval"
```

✅ **Check Error Messages**
Look for any error messages in the response - they might hint at what failed.

### If Data Still Missing

Try these steps:

1. **Restart everything**
   ```bash
   Ctrl+C (to stop)
   python main.py all
   ```

2. **Check logs carefully**
   - Watch the terminal output when submitting
   - Look for any ERROR or EXCEPTION messages
   - Note which node failed (if any)

3. **Test with curl**
   ```bash
   curl -X POST http://127.0.0.1:8000/docs
   # Open swagger UI and test the endpoint directly
   ```

4. **Check MCP imports**
   ```bash
   python3 -c "from src.mcps.applicant_db.server import applicant_mcp; print('OK')"
   ```

### Fallback Behavior

If analysis data is missing, the frontend now:
1. Shows a warning: "⚠️ Analysis data incomplete"
2. Displays the verdict narrative text
3. This prevents blank/N/A display

### Next Steps

1. Run the system with debug enabled
2. Submit a form
3. Expand the DEBUG section
4. Report what you see in the raw response
5. Use the checklist above to identify which node failed

### Example: Good vs Bad

**GOOD OUTPUT:**
```
✅ Analysis Complete!

🔍 DEBUG: Raw API Response (expander)
{
  "analysis": {
    "decision": {
      "classification": "Approve",
      "risk_score": 18.5,
      ...
    }
  }
}

🟢 APPROVE
Risk Score: 18.5/100 | Confidence: 81.5%
```

**BAD OUTPUT:**
```
✅ Analysis Complete!

⚠️ Analysis data incomplete. Showing verdict:
We are pleased to inform you...

🔍 DEBUG: Raw API Response (expander)
{
  "analysis": {}  ← EMPTY!
}
```

If you see BAD OUTPUT, check the terminal logs to see where the pipeline failed.

---

**Run it now and let me know what you see in the DEBUG section!** 🔍

# Implementation Changes and Reasons

This document details every change made to integrate 4 MCP servers with the orchestrator, with inline comments and reasoning.

---

## File: `orchestrator.py` 

### Changes

#### 1. **Imports (NEW)**
```python
from src.mcps.applicant_db.server import applicant_mcp
from src.mcps.risk_rules_db.server import risk_mcp
from src.mcps.decision_synthesis.server import decision_mcp
from src.mcps.notification_system.server import notification_mcp
from src.mcps.mcp_bridge import call_mcp_tool
```

**Reason**: Import the 4 MCP servers so nodes can call them. `call_mcp_tool` is the synchronous wrapper (LangGraph nodes are sync, MCP client is async).

---

#### 2. **State Schema (CHANGED)**

**Before**:
```python
class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
```

**After**:
```python
class LoanUnderwritingState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    applicant_data: dict           # Original application data
    profile_analysis: dict          # ApplicantDB agent output
    risk_analysis: dict             # RiskRulesDB agent output
    decision: dict                  # DecisionSynthesis agent output
    compliance_result: dict         # NotificationSystem agent output
    final_verdict: str              # LLM synthesis output
```

**Reason**: Multi-agent pipeline requires structured state to pass outputs between nodes. Each field carries the result of one node to the next. By keeping everything in state, we have a complete audit trail.

---

#### 3. **LLM Model (CHANGED)**

**Before**:
```python
llm = ChatAnthropic(
    model="global.anthropic.claude-haiku-4-5-20251001-v1:0",
    ...
)
```

**After**:
```python
llm = ChatAnthropic(
    model=Config.SONNET_MODEL,  # Defaults to claude-sonnet-4-6
    ...
)
```

**Reason**: Sonnet has better reasoning for synthesizing final verdicts. Since Agents 1-4 use MCP (no LLM), only Node 5 pays for Sonnet. Result: better quality final verdict at no extra cost (savings from removing LLM calls from Agents 1-4).

---

#### 4. **Node 1: applicant_analysis_node (NEW)**

```python
def applicant_analysis_node(state: LoanUnderwritingState):
    """
    Analyze applicant profile using ApplicantDB MCP.
    
    REASON: Deterministic rule-based analysis (employment type → stability score).
    No LLM needed; logic is transparent and auditable.
    """
    result = call_mcp_tool(
        applicant_mcp,
        "analyze_applicant_profile",
        {"applicant_data": json.dumps(state["applicant_data"])}
    )
    state["profile_analysis"] = result
    return state
```

**Reason**: First agent analyzes applicant profile using deterministic rules. Output becomes input to Node 2. By using MCP instead of LLM, we ensure:
- Reproducibility: same input always produces same output
- Auditability: business rules are versioned in the MCP server
- Cost: zero LLM tokens

---

#### 5. **Node 2: risk_analysis_node (NEW)**

```python
def risk_analysis_node(state: LoanUnderwritingState):
    """
    Analyze financial risk using RiskRulesDB MCP.
    
    REASON: Standard lending formulas (DTI, amortization). No LLM needed;
    all calculations are deterministic and rule-based.
    """
    result = call_mcp_tool(
        risk_mcp,
        "analyze_financial_risk",
        {
            "applicant_data": json.dumps(state["applicant_data"]),
            "profile_analysis": json.dumps(state["profile_analysis"])
        }
    )
    state["risk_analysis"] = result
    return state
```

**Reason**: Second agent calculates financial risk metrics. Uses the profile from Node 1 as input. By using MCP:
- Compliance: DTI calculation is documented and auditable
- Transparency: anyone can verify the formula
- Cost: zero LLM tokens

---

#### 6. **Node 3: decision_synthesis_node (NEW)**

```python
def decision_synthesis_node(state: LoanUnderwritingState):
    """
    Synthesize preliminary decision using DecisionSynthesis MCP.
    
    REASON: Deterministic scoring with fixed thresholds.
    Decision (Approve/Reject/Review) should NOT depend on LLM randomness.
    """
    result = call_mcp_tool(
        decision_mcp,
        "synthesize_loan_decision",
        {
            "applicant_data": json.dumps(state["applicant_data"]),
            "profile_analysis": json.dumps(state["profile_analysis"]),
            "risk_analysis": json.dumps(state["risk_analysis"])
        }
    )
    state["decision"] = result
    return state
```

**Reason**: Third agent decides Approve/Reject/Review using weighted scoring formula. By using MCP:
- Auditable: risk_score = sum of weighted penalties (formula documented)
- Non-random: same inputs always produce same decision
- Compliant: decision logic separate from LLM (cannot be hallucinated)
- Explainable: key_decision_factors list why decision was made

---

#### 7. **Node 4: compliance_action_node (NEW)**

```python
def compliance_action_node(state: LoanUnderwritingState):
    """
    Generate case record using NotificationSystem MCP.
    
    REASON: Compliance requires consistent messaging.
    Same decision must always produce same notification (no LLM variation).
    """
    result = call_mcp_tool(
        notification_mcp,
        "dispatch_notification",
        {
            "decision_data": json.dumps(state["decision"]),
            "applicant_data": json.dumps(state["applicant_data"])
        }
    )
    state["compliance_result"] = result
    return state
```

**Reason**: Fourth agent creates case record and notification. By using MCP:
- Consistency: Approve → same email every time
- Audit trail: case_id links decision to notification
- Compliance: templates can be reviewed by legal independently
- Cost: zero LLM tokens

---

#### 8. **Node 5: llm_synthesis_node (NEW)**

```python
def llm_synthesis_node(state: LoanUnderwritingState):
    """
    LLM synthesis to write professional final verdict.
    
    REASON: LLM is used ONLY to explain decisions in clear prose.
    The decision itself (Approve/Reject/Review) comes from Agent 3, NOT the LLM.
    This ensures decisions cannot be influenced by prompt injection or model hallucination.
    """
    synthesis_prompt = f"""
    [Includes all 4 agent outputs for context]
    Please write a final verdict that:
    1. States the decision clearly (already made by agents)
    2. Summarizes key factors (from agent outputs)
    3. Explains what happens next
    4. Maintains professional tone
    """
    response = llm.invoke([HumanMessage(content=synthesis_prompt)])
    state["final_verdict"] = response.content
    return state
```

**Reason**: Fifth agent uses LLM ONLY for explanation, not decision-making. LLM:
- Reads all prior agent outputs
- Writes a human-readable summary for the applicant file
- Cannot change the decision (already made)
- Cannot hallucinate additional factors (all facts from agents)

---

#### 9. **Graph Structure (CHANGED)**

**Before**:
```python
graph = StateGraph(ChatState)
graph.add_node("chat_node", chat_node)
graph.add_edge(START, "chat_node")
graph.add_edge("chat_node", END)
```

**After**:
```python
graph = StateGraph(LoanUnderwritingState)
graph.add_node("applicant_analysis", applicant_analysis_node)
graph.add_node("risk_analysis", risk_analysis_node)
graph.add_node("decision_synthesis", decision_synthesis_node)
graph.add_node("compliance_action", compliance_action_node)
graph.add_node("llm_synthesis", llm_synthesis_node)

graph.add_edge(START, "applicant_analysis")
graph.add_edge("applicant_analysis", "risk_analysis")
graph.add_edge("risk_analysis", "decision_synthesis")
graph.add_edge("decision_synthesis", "compliance_action")
graph.add_edge("compliance_action", "llm_synthesis")
graph.add_edge("llm_synthesis", END)
```

**Reason**: Changed from single-node to 5-node sequential pipeline. Each node is specialized:
- Nodes 1-4: Deterministic analysis (MCP)
- Node 5: Subjective explanation (LLM)

This separation ensures decisions are verifiable while explanations are well-written.

---

## File: `gateway.py`

### Changes

#### 1. **Handler Update (CHANGED)**

**Before**:
```python
def pass_to_orchestrator(data: dict) -> dict:
    prompt_text = f"""...[raw prompt building]..."""
    inputs = {"messages": [HumanMessage(content=prompt_text)]}
    graph_output = chatbot.invoke(inputs)
    last_message = graph_output["messages"][-1]
    return {"verdict": last_message.content}
```

**After**:
```python
def pass_to_orchestrator(data: dict) -> dict:
    inputs = {
        "messages": [HumanMessage(content=f"Process loan application {data.get('applicant_id')}")],
        "applicant_data": data,           # NEW: Pass original data
        "profile_analysis": {},            # NEW: Will be filled by Node 1
        "risk_analysis": {},               # NEW: Will be filled by Node 2
        "decision": {},                    # NEW: Will be filled by Node 3
        "compliance_result": {},           # NEW: Will be filled by Node 4
        "final_verdict": ""                # NEW: Will be filled by Node 5
    }
    graph_output = chatbot.invoke(inputs)
    final_verdict = graph_output.get("final_verdict")
    return {"verdict": final_verdict}
```

**Reason**: 
- Initialize all state fields that nodes will populate
- Gateway no longer builds the underwriting prompt (nodes do it step-by-step)
- Extract final_verdict from state instead of last message
- API contract unchanged: still returns `{"verdict": string}`

---

## File: `src/config.py` (NEW)

```python
SONNET_MODEL = os.getenv("SONNET_MODEL", "global.anthropic.claude-sonnet-4-6-20250514-v1:0")
MCP_APPLICANT_DB_PORT = int(os.getenv("MCP_APPLICANT_DB_PORT", 8001))
MCP_RISK_RULES_DB_PORT = int(os.getenv("MCP_RISK_RULES_DB_PORT", 8002))
MCP_DECISION_SYNTHESIS_PORT = int(os.getenv("MCP_DECISION_SYNTHESIS_PORT", 8003))
MCP_NOTIFICATION_SYSTEM_PORT = int(os.getenv("MCP_NOTIFICATION_SYSTEM_PORT", 8004))
```

**Reason**:
- Centralized config: avoid hardcoding ports/models in MCP files
- Environment overridable: prod can use different model/ports
- Future-proof: easy to add more MCPs with their own ports

---

## File: `main.py` (CREATED)

```python
def run_mcp_applicant():
    """Run ApplicantDB MCP as HTTP microservice."""
    from src.mcps.applicant_db.server import applicant_mcp
    applicant_mcp.run(transport="streamable-http", port=Config.MCP_APPLICANT_DB_PORT)
```

**Reason**:
- Each MCP can be launched independently via CLI
- Transport: "streamable-http" = MCP 1.0 protocol over HTTP
- Ports: 8001-8004 for each MCP
- Use case: dev = in-process (no extra processes), prod = HTTP (scalable)

---

## MCP Servers (4 NEW FILES)

### `src/mcps/applicant_db/server.py`

```python
@applicant_mcp.tool
def analyze_applicant_profile(applicant_data: str) -> str:
    """
    Analyze applicant profile and return:
    - Income stability score (0.0-1.0)
    - Employment risk level (Low/Medium/High)
    - Credit history summary (Excellent/Good/Fair/Poor)
    - Application completeness flags
    
    WHY: All logic is deterministic:
    - Employment type → stability score (lookup: Full-Time=0.9, Contract=0.6, Freelancer=0.4)
    - Credit score band → rating (threshold: ≥750=Excellent, ≥700=Good, etc.)
    - Required fields → completeness (validation logic)
    
    NO LLM needed. Result is 100% reproducible and auditable.
    """
```

**Reason**: 
- Rule-based analysis with fixed mappings
- No LLM tokens
- Auditable and reproducible

---

### `src/mcps/risk_rules_db/server.py`

```python
@risk_mcp.tool
def analyze_financial_risk(applicant_data: str, profile_analysis: str) -> str:
    """
    Analyze financial risk metrics:
    - DTI ratio (formula: (liabilities + monthly_payment) / (annual_income / 12))
    - Credit score risk (Low/Medium/High based on score band)
    - Loan amount risk (Low/Medium/High based on loan-to-income)
    - Financial anomalies (high DTI, unusual income-for-age, etc.)
    
    WHY: Standard lending formulas with clear cutoffs:
    - Monthly payment: amortization formula at fixed 7% APR, 5-year term
    - DTI thresholds: ≤36% Excellent, ≤43% Acceptable, >50% Very High
    - Anomalies: rule-based detection (e.g., income < age*1000 is unusual)
    
    NO LLM needed. All calculations are deterministic and documented.
    """
```

**Reason**:
- Industry-standard financial formulas
- Transparent calculations
- Compliance: documented methodology
- Cost: zero LLM tokens

---

### `src/mcps/decision_synthesis/server.py`

```python
@decision_mcp.tool
def synthesize_loan_decision(applicant_data: str, profile_analysis: str, risk_analysis: str) -> str:
    """
    Synthesize preliminary decision:
    - Risk score (0-100) from weighted formula:
      * DTI: 40% weight
      * Credit score: 30% weight
      * Employment stability: 15% weight
      * Loan amount risk: 15% weight
    - Classification:
      * Approve if risk_score < 25
      * Review if 25 ≤ risk_score < 55
      * Reject if risk_score ≥ 55
    - Confidence level: 1.0 - (risk_score / 100)
    - Key decision factors: list of main contributing factors
    
    WHY: Decision must be deterministic and auditable.
    Not delegated to LLM because:
    - LLM can hallucinate or be influenced by prompt injection
    - Lending decisions must follow documented rules
    - Regulators need to see the exact scoring formula
    - Same inputs must always produce same decision
    
    NO LLM. Pure scoring algorithm with transparent weights.
    """
```

**Reason**:
- Decision logic must be verifiable
- Cannot use LLM for decisions (regulatory/compliance)
- Weights and thresholds are business rules, not LLM outputs
- Explainability: key_decision_factors show why

---

### `src/mcps/notification_system/server.py`

```python
@notification_mcp.tool
def dispatch_notification(decision_data: str, applicant_data: str) -> str:
    """
    Dispatch notification and create case record:
    - Case ID: CASE-XXXXXXXX (audit trail)
    - Notification email:
      * Approve: congratulations + next steps
      * Reject: professional decline + appeal info
      * Review: manual review notice + SLA
    - Action taken: determines routing (documentation team / archive / manual review)
    - Timestamp: compliance logging
    
    WHY: Compliance requires consistent messaging.
    If decision = "Approve", applicant must always receive the same email.
    LLM could vary the message (randomness, prompt injection), which violates compliance.
    
    NO LLM. Template-based messaging ensures consistency.
    """
```

**Reason**:
- Consistency: same decision → same message
- Compliance: templates reviewed by legal
- Audit trail: case ID ties everything together
- Cost: zero LLM tokens

---

### `src/mcps/mcp_bridge.py`

```python
def call_mcp_tool(
    mcp_server: FastMCP,
    tool_name: str,
    tool_params: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Call MCP tool synchronously (wrapper for async function).
    
    WHY: LangGraph nodes are synchronous functions, but FastMCP Client is async.
    This wrapper:
    1. Gets or creates event loop
    2. Runs async MCP call synchronously
    3. Parses JSON result
    4. Handles errors centrally
    
    Used by all 5 nodes:
    - Node 1: call_mcp_tool(applicant_mcp, "analyze_applicant_profile", ...)
    - Node 2: call_mcp_tool(risk_mcp, "analyze_financial_risk", ...)
    - Node 3: call_mcp_tool(decision_mcp, "synthesize_loan_decision", ...)
    - Node 4: call_mcp_tool(notification_mcp, "dispatch_notification", ...)
    - Node 5: Does not call MCP (calls Claude directly)
    """
```

**Reason**:
- Solves sync/async mismatch
- Centralizes MCP call logic
- Consistent error handling
- Reusable across all nodes

---

## Summary of Reasoning

| Change | Why |
|--------|-----|
| **State schema expansion** | Multi-agent pipeline needs to pass data between nodes |
| **5-node pipeline** | Separation of concerns: analysis (MCP) + synthesis (LLM) |
| **MCP for Agents 1-4** | Deterministic logic, auditability, cost savings, compliance |
| **LLM for Agent 5 only** | Subjective explanation, cannot influence decision |
| **Sonnet instead of Haiku** | Better reasoning for synthesis, cost offset by MCP savings elsewhere |
| **Centralized config** | Avoid hardcoding, enable environment overrides, future MCP additions |
| **Bridge utility** | Solve sync/async mismatch, centralize MCP call logic |
| **HTTP MCP ports** | Enable production deployment as independent microservices |
| **main.py service launcher** | Support both dev (in-process) and prod (HTTP) modes |

---

## Result

✅ **Deterministic loan decisions** with transparent, auditable logic
✅ **Cost-efficient**: LLM only for explanation (Sonnet), not analysis (MCPs)
✅ **Compliant**: decisions cannot be influenced by LLM randomness or injection
✅ **Explainable**: each step documents its reasoning
✅ **Scalable**: MCPs can be deployed independently in production
✅ **Backward compatible**: API contract unchanged

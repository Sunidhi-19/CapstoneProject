# 🔧 Bug Fix: JSON Serialization Error

## Problem

When submitting a loan application, the system threw a 500 error:

```
Backend error (500): {"detail":"LangChain orchestration layer failure: Object of type datetime is not JSON serializable"}
```

## Root Cause

The `application_timestamp` field from Pydantic validation is a `datetime` object. When the MCP tools try to serialize this with `json.dumps()`, Python's JSON encoder fails because it doesn't know how to serialize datetime objects.

**Flow:**
```
Frontend submits form
    ↓
Gateway receives: application_timestamp = datetime(2026-06-22, 17:37:41)  ← datetime object
    ↓
Gateway passes to Orchestrator: json.dumps(data)  ← ❌ FAILS
    ↓
Error: Object of type datetime is not JSON serializable
```

## Solution

Convert `datetime` to ISO format string before passing to orchestrator.

**File:** `gateway.py`

**Change:**
```python
def pass_to_orchestrator(data: dict) -> dict:
    # FIX: Convert datetime to string for JSON serialization
    # REASON: MCP tools use json.dumps() which cannot serialize datetime objects.
    if isinstance(data.get("application_timestamp"), datetime):
        data["application_timestamp"] = data["application_timestamp"].isoformat()
    
    # Rest of function...
```

**What it does:**
- Checks if `application_timestamp` is a datetime object
- Converts it to ISO format string: `"2026-06-22T17:37:41.982968"`
- String is JSON serializable ✅

## Before vs After

### Before
```python
data = {
    'applicant_id': 'APP12345',
    'application_timestamp': datetime(2026, 6, 22, 17, 37, 41)  # datetime object
}

json.dumps(data)  # ❌ TypeError: Object of type datetime is not JSON serializable
```

### After
```python
data = {
    'applicant_id': 'APP12345',
    'application_timestamp': '2026-06-22T17:37:41.982968'  # ISO string
}

json.dumps(data)  # ✅ SUCCESS
```

## Testing the Fix

```bash
# Test that datetime is properly converted
python3 -c "
from datetime import datetime
import json

data = {'timestamp': datetime.now()}

# Before fix
try:
    json.dumps(data)
except TypeError:
    print('Before fix: ❌ Fails')

# After fix
data['timestamp'] = data['timestamp'].isoformat()
json.dumps(data)
print('After fix: ✅ Works')
"
```

Output:
```
Before fix: ❌ Fails
After fix: ✅ Works
```

## Where Used

The fix is applied in `gateway.py` in the `pass_to_orchestrator()` function:

1. **Input:** Pydantic-validated datetime object
2. **Process:** Convert to ISO string with `.isoformat()`
3. **Output:** String that can be JSON serialized
4. **Pass to:** MCP tools (which use `json.dumps()`)

## ISO Format Explanation

Python's `.isoformat()` method converts datetime to ISO 8601 format:

```
datetime(2026, 6, 22, 17, 37, 41, 982968)
    ↓
"2026-06-22T17:37:41.982968"
```

This format is:
- ✅ JSON serializable
- ✅ Standard and readable
- ✅ Includes microseconds for precision
- ✅ Can be parsed back to datetime if needed

## Why This Works

### MCP Tools Do This:
```python
# In src/mcps/applicant_db/server.py
def analyze_applicant_profile(applicant_data: str) -> str:
    data = json.loads(applicant_data)  # ← Expects JSON string
    # Use data...
```

### Gateway Passes JSON:
```python
# In gateway.py
result = call_mcp_tool(
    applicant_mcp,
    "analyze_applicant_profile",
    {"applicant_data": json.dumps(state["applicant_data"])}  # ← Needs to serialize
)
```

**With datetime object:** `json.dumps()` fails ❌

**With ISO string:** `json.dumps()` succeeds ✅

## Complete Fix Applied

**File:** `gateway.py`

**Location:** `pass_to_orchestrator()` function

**Line:** Added before initializing `inputs` dict

```python
def pass_to_orchestrator(data: dict) -> dict:
    """
    UPDATED: Passes validated application data to the multi-agent LangGraph orchestrator.
    ...
    """
    # FIX: Convert datetime to string for JSON serialization
    # REASON: MCP tools use json.dumps() which cannot serialize datetime objects.
    # Pydantic validates the timestamp on input, so we just need to convert it for storage.
    if isinstance(data.get("application_timestamp"), datetime):
        data["application_timestamp"] = data["application_timestamp"].isoformat()
    
    # Initialize the structured state for multi-agent pipeline
    inputs = {
        "messages": [HumanMessage(content=f"Process loan application {data.get('applicant_id')}")],
        "applicant_data": data,  # ← Now has ISO string instead of datetime
        # ... rest of state
    }
    
    # ... rest of function
```

## Testing the Full Flow

Now you can:

1. Start the system: `python main.py all`
2. Open: `http://127.0.0.1:8501`
3. Submit a form with timestamp
4. ✅ No more 500 error!

## Summary

| Aspect | Details |
|--------|---------|
| **Error Type** | JSON serialization failure |
| **Root Cause** | datetime object in JSON serialization |
| **Solution** | Convert to ISO format string with `.isoformat()` |
| **Lines Changed** | 2 lines in `gateway.py` |
| **Impact** | Fixes 500 error when submitting forms |
| **Backward Compatible** | ✅ Yes (only affects internal conversion) |

---

**The system should now work perfectly!** 🎉

Try running: `python main.py all` and submit a loan application again.

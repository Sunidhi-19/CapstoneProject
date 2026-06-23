import streamlit as st
import requests
from datetime import datetime

BACKEND_URL = "http://127.0.0.1:8000/loan_approval"

st.set_page_config(page_title="Loan Underwriting Portal", page_icon="🏦", layout="centered")
st.title("🏦 Automated Loan Underwriting Portal")
st.markdown("Provide comprehensive profile parameters below to submit for approval.")
st.markdown("---")

current_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

with st.form(key="loan_application_form"):
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("👤 Applicant Profile")
        applicant_id = st.text_input("Applicant ID", placeholder="e.g., APP98421")
        name = st.text_input("Full Name", placeholder="e.g., Jane Doe")
        age = st.number_input("Age", min_value=18, max_value=100)
        location = st.text_input("Location", placeholder="e.g., New York, NY")

    with col2:
        st.subheader("📊 Financial Profile")
        employment_type = st.selectbox("Employment Type", ("Full-Time", "Contract", "Freelancer"))
        income = st.number_input("Gross Annual Income", min_value=10000.0, step=5000.0, format="%.2f")
        existing_liabilities = st.number_input(
            "Monthly Liabilities", min_value=0.0,
            help="Monthly EMIs, credit card payments, existing loan obligations"
        )
        credit_score = st.number_input("Credit Score", min_value=300, max_value=850)

    st.subheader("💰 Loan Request")
    term_col1, term_col2 = st.columns(2)
    with term_col1:
        loan_amount = st.number_input("Loan Amount", min_value=0.0, step=1000.0)
    with term_col2:
        loan_duration = st.slider("Repayment Term (Years)", min_value=1, max_value=30)

    st.markdown(f"**Application Timestamp:** `{current_timestamp}`")
    submit = st.form_submit_button("Submit Application For Review", type="primary", use_container_width= True)

# ── Processing ─────────────────────────────────────────────────────────────────
if submit:
    payload = {
        "applicant_id": applicant_id,
        "name": name,
        "age": age,
        "employment_type": employment_type,
        "location": location,
        "gross_annual_income": income,
        "existing_liabilities": existing_liabilities,
        "credit_score": credit_score,
        "loan_amount": loan_amount,
        "loan_duration_years": loan_duration,
        "application_timestamp": current_timestamp
    }

    with st.status("Running underwriting pipeline...", expanded=True) as pipeline_status:
        try:
            st.write("⏳ Dispatching application to backend...")
            response = requests.post(BACKEND_URL, json=payload)

            if response.status_code == 200:
                result = response.json()
                st.write("✅ Node 1 — ApplicantDB · Profile & employment analysis")
                st.write("✅ Node 2 — RiskRulesDB · DTI ratio & financial risk scoring")
                st.write("✅ Node 3 — DecisionSynthesis · Classification & confidence")
                st.write("✅ Node 4 — NotificationSystem · Case record & compliance")
                st.write("✅ Node 5 — LLM Synthesis · Final verdict generation")
                pipeline_status.update(label="✅ Underwriting complete", state="complete", expanded=False)

                # ── Extract data ───────────────────────────────────────────────
                orchestrator_output = result.get("orchestrator_output", {})
                analysis = orchestrator_output.get("analysis", {})
                decision = analysis.get("decision", {})
                risk = analysis.get("risk", {})
                profile = analysis.get("profile", {})
                compliance = analysis.get("compliance", {})

                classification = decision.get("classification", "Review")
                risk_score = decision.get("risk_score", 0)
                confidence = decision.get("confidence_level", 0)

                # ── Decision colors ────────────────────────────────────────────
                if classification == "Approve":
                    icon = "🟢"
                    status_color = "#2e7d32"
                    bg_color = "#e8f5e9"
                elif classification == "Reject":
                    icon = "🔴"
                    status_color = "#c62828"
                    bg_color = "#ffebee"
                else:
                    icon = "🟡"
                    status_color = "#e65100"
                    bg_color = "#fff3e0"

                # ── 1. Decision hero ───────────────────────────────────────────
                st.markdown("---")
                st.markdown(f"""
                <div style="
                    background-color:{bg_color};
                    padding:30px; border-radius:12px;
                    border-left:5px solid {status_color};
                    margin:16px 0;
                ">
                    <h1 style="margin:0; color:{status_color}; text-align:center;">
                        {icon} {classification.upper()}
                    </h1>
                    <p style="text-align:center; color:#555; margin-top:10px; font-size:18px;">
                        Risk Score: <b>{risk_score:.1f}/100</b> &nbsp;|&nbsp;
                        Confidence: <b>{confidence:.1%}</b>
                    </p>
                </div>
                """, unsafe_allow_html=True)

                # ── 2. Key factors ─────────────────────────────────────────────
                st.markdown("### 🚩 Key Decision Factors")
                key_factors = decision.get("key_factors", [])
                if key_factors:
                    fcols = st.columns(min(3, len(key_factors)))
                    for idx, factor in enumerate(key_factors[:3]):
                        with fcols[idx % len(fcols)]:
                            st.info(f"✓ {factor}")
                else:
                    st.info("✓ Standard Underwriting Criteria")

                # ── 3. Metrics grid ────────────────────────────────────────────
                st.markdown("### 📊 Detailed Analysis")
                c1, c2, c3 = st.columns(3)

                with c1:
                    st.markdown("#### 👤 Profile")
                    st.metric("Employment Risk", profile.get("employment_risk", "N/A"))
                    st.metric("Income Stability", f"{profile.get('income_stability_score', 0):.2f}")
                    st.metric("Credit Rating", profile.get("credit_rating", "N/A"))

                with c2:
                    st.markdown("#### 📈 Financial Risk")
                    st.metric("DTI Ratio", f"{risk.get('debt_to_income_ratio', 0):.1f}%")
                    st.metric("DTI Rating", risk.get("dti_rating", "N/A"))
                    st.metric("Credit Risk", risk.get("credit_score_risk_level", "N/A"))

                with c3:
                    st.markdown("#### ⚠️ Risk Assessment")
                    st.metric("Risk Level", decision.get("risk_level", "N/A"))
                    st.metric("Loan Amount Risk", risk.get("loan_amount_risk", "N/A"))
                    st.metric("Risk Score", f"{risk_score:.0f} / 100")

                # ── 4. Anomalies ───────────────────────────────────────────────
                anomalies = risk.get("anomalies_detected", [])
                if anomalies:
                    st.markdown("### ⚠️ Detected Anomalies")
                    for anomaly in anomalies:
                        st.warning(f"🔔 {anomaly}")

                # ── 5. Decision reason narrative ───────────────────────────────────────
                decision_reason = decision.get("decision_reason", "")
                if decision_reason:
                    st.markdown("### 📝 Decision Reason")
                    st.markdown(f"""
                    <div style="
                        background-color:#f8f9fa;
                        padding:20px 24px; border-radius:10px;
                        border-left:4px solid {status_color};
                        font-size:0.95rem; line-height:1.7; color:#333;
                    ">{decision_reason}</div>
                    """, unsafe_allow_html=True)

                # ── 6. Case record ─────────────────────────────────────────────
                if compliance:
                    st.markdown("### 📋 Case Record")
                    cc1, cc2 = st.columns(2)
                    with cc1:
                        st.info(f"**Case ID:** {compliance.get('case_id', 'N/A')}")
                    with cc2:
                        st.info(f"**Status:** {compliance.get('case_status', 'Active')}")

                st.markdown("---")

            else:
                pipeline_status.update(label="Pipeline error", state="error")
                st.error(f"Backend returned {response.status_code}: {response.text}")

        except requests.exceptions.ConnectionError:
            pipeline_status.update(label="Connection failed", state="error")
            st.error(f"Could not connect to backend at {BACKEND_URL}. Is the FastAPI server running?")

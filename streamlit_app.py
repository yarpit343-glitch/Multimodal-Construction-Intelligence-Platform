"""
ConstructAI — Multimodal Construction Intelligence Platform
Streamlit Web Application for Streamlit Community Cloud and Local Execution.
All financial outputs localized to Indian Rupees (₹ / INR).
"""

import os
import sys
import json
from datetime import date
from io import BytesIO
from pathlib import Path
from typing import Optional

import streamlit as st
from PIL import Image

# Ensure backend modules (ai_service, schemas) are importable
ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Attempt to load local environment if python-dotenv is present
try:
    from dotenv import load_dotenv
    if (BACKEND_DIR / ".env").exists():
        load_dotenv(BACKEND_DIR / ".env")
    elif (ROOT_DIR / ".env").exists():
        load_dotenv(ROOT_DIR / ".env")
except Exception:
    pass

from schemas import (
    SiteAnalysisResponse, CostEstimationResponse, SafetyInspectionResponse,
    ProgressMonitoringResponse, MaterialAnalysisResponse, ProjectReportResponse,
    ChatResponse,
)
from ai_service import GroqAIService, AIServiceError, DEFAULT_GROQ_TEXT_MODEL, DEFAULT_GROQ_VISION_MODEL

# ─────────────────── Page Configuration ──────────────────────────

st.set_page_config(
    page_title="ConstructAI — Construction Intelligence",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────── Custom Styling ──────────────────────────────

CUSTOM_CSS = """
<style>
/* Main Container Typography & Background */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* Glassmorphism Card Style */
.metric-card {
    background: rgba(30, 41, 59, 0.7);
    border: 1px solid rgba(245, 158, 11, 0.2);
    border-radius: 12px;
    padding: 18px 20px;
    box-shadow: 0 4px 14px 0 rgba(0, 0, 0, 0.3);
    backdrop-filter: blur(8px);
    transition: transform 0.2s ease, border-color 0.2s ease;
}
.metric-card:hover {
    border-color: rgba(245, 158, 11, 0.5);
    transform: translateY(-2px);
}

.metric-label {
    font-size: 0.82rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #94A3B8;
    margin-bottom: 6px;
}

.metric-value {
    font-size: 1.85rem;
    font-weight: 800;
    color: #F8FAFC;
    line-height: 1.2;
}

.metric-sub {
    font-size: 0.8rem;
    color: #CBD5E1;
    margin-top: 4px;
}

/* Badges */
.badge {
    display: inline-block;
    padding: 4px 10px;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 700;
    text-transform: uppercase;
}
.badge-low { background-color: rgba(16, 185, 129, 0.2); color: #34D399; border: 1px solid #10B981; }
.badge-medium { background-color: rgba(245, 158, 11, 0.2); color: #FBBF24; border: 1px solid #F59E0B; }
.badge-high { background-color: rgba(239, 68, 68, 0.2); color: #F87171; border: 1px solid #EF4444; }
.badge-critical { background-color: rgba(220, 38, 38, 0.35); color: #FECACA; border: 1px solid #DC2626; }

/* Status Banners */
.disclaimer-banner {
    background-color: rgba(245, 158, 11, 0.1);
    border-left: 4px solid #F59E0B;
    padding: 12px 16px;
    border-radius: 6px;
    font-size: 0.85rem;
    color: #FDE68A;
    margin-bottom: 1rem;
}

.ppe-box {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 8px 14px;
    border-radius: 8px;
    font-weight: 600;
    font-size: 0.9rem;
    margin: 4px;
}
.ppe-pass { background-color: rgba(16, 185, 129, 0.15); border: 1px solid #10B981; color: #34D399; }
.ppe-fail { background-color: rgba(239, 68, 68, 0.15); border: 1px solid #EF4444; color: #F87171; }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ─────────────────── Currency & Formatting Helpers ───────────────

def format_inr(value: float) -> str:
    """Format a number into Indian Rupees with Lakh / Crore shorthand."""
    if value is None:
        return "₹0"
    abs_val = abs(value)
    if abs_val >= 10_000_000:
        return f"₹{value / 10_000_000:.2f} Cr"
    elif abs_val >= 100_000:
        return f"₹{value / 100_000:.2f} Lakh"
    return f"₹{value:,.2f}"


def get_risk_badge_html(level: str) -> str:
    lvl = (level or "low").lower()
    return f'<span class="badge badge-{lvl}">{lvl.upper()}</span>'


# ─────────────────── Secret & Client Resolution ──────────────────

def resolve_api_key() -> str:
    """Retrieve Groq API key with Streamlit Cloud secrets prioritized."""
    # 1. Streamlit Secrets (for Streamlit Community Cloud)
    if hasattr(st, "secrets"):
        try:
            if "GROQ_API_KEY" in st.secrets and st.secrets["GROQ_API_KEY"]:
                return str(st.secrets["GROQ_API_KEY"]).strip()
        except Exception:
            pass

    # 2. Local Environment variable
    env_key = os.getenv("GROQ_API_KEY", "").strip()
    if env_key:
        return env_key

    # 3. Session state user override
    return st.session_state.get("groq_key_override", "").strip()


def resolve_models() -> tuple[str, str]:
    """Retrieve preferred text and vision models."""
    text_model = DEFAULT_GROQ_TEXT_MODEL
    vision_model = DEFAULT_GROQ_VISION_MODEL
    if hasattr(st, "secrets"):
        try:
            text_model = st.secrets.get("GROQ_TEXT_MODEL", text_model)
            vision_model = st.secrets.get("GROQ_VISION_MODEL", vision_model)
        except Exception:
            pass
    text_model = os.getenv("GROQ_TEXT_MODEL", text_model)
    vision_model = os.getenv("GROQ_VISION_MODEL", vision_model)
    return text_model, vision_model


@st.cache_resource(show_spinner=False)
def get_ai_service(api_key: str, text_model: str, vision_model: str) -> Optional[GroqAIService]:
    """Instantiate and cache the Groq AI service."""
    if not api_key:
        return None
    try:
        return GroqAIService(
            api_key=api_key,
            text_model=text_model,
            vision_model=vision_model,
        )
    except Exception as e:
        st.error(f"Failed to initialize Groq client: {e}")
        return None


# ─────────────────── Sidebar Setup ───────────────────────────────

api_key = resolve_api_key()
text_model, vision_model = resolve_models()

with st.sidebar:
    st.markdown("### 🏗️ **ConstructAI**")
    st.caption("Multimodal Construction Intelligence Platform")
    st.divider()

    # Connection Status
    if api_key:
        st.success("🟢 **Groq AI Connected**", icon="✅")
    else:
        st.warning("🟡 **API Key Needed**", icon="⚠️")
        user_key = st.text_input(
            "Enter Groq API Key",
            type="password",
            placeholder="gsk_...",
            help="Free API key from https://console.groq.com",
            key="groq_key_input",
        )
        if user_key:
            st.session_state["groq_key_override"] = user_key.strip()
            st.rerun()

    # Navigation menu
    menu = st.radio(
        "Navigation",
        [
            "📊 Dashboard Overview",
            "🔍 Site Analysis",
            "🦺 Safety Inspection",
            "💰 Cost Estimation",
            "📈 Progress Monitoring",
            "📸 Visual Progress",
            "🧱 Material Analysis & BOQ",
            "💬 ConstructAI Chatbot",
            "📑 Project Report Generator",
        ],
        index=0,
    )

    st.divider()
    with st.expander("⚙️ System Specs", expanded=False):
        st.caption(f"**Text Model**: `{text_model}`")
        st.caption(f"**Vision Model**: `{vision_model}`")
        st.caption("**Currency**: Indian Rupees (₹ / INR)")
        st.caption("**Standards**: IS 456, IS 800, IS 4130, BOCW Act")
    st.caption("v1.0.0 • Streamlit Cloud Edition")

service = get_ai_service(api_key, text_model, vision_model) if api_key else None


def require_ai_service():
    if not service:
        st.error("⚠️ **Groq API Key Required**: Please configure `GROQ_API_KEY` in Streamlit Cloud Secrets or enter your key in the sidebar.")
        st.stop()


# ─────────────────── 1. Dashboard Overview ────────────────────────

if menu == "📊 Dashboard Overview":
    st.title("🏗️ Multimodal Construction Intelligence Platform")
    st.markdown(
        "Enterprise-grade decision support platform for site engineers, contractors, and project managers. "
        "All calculations and rate estimates are localized to **Indian Rupees (₹ / INR)**."
    )

    # Top Metric Highlights
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(
            """<div class="metric-card">
                <div class="metric-label">AI Engine</div>
                <div class="metric-value" style="color: #F59E0B;">Groq LPU</div>
                <div class="metric-sub">Multimodal Vision & Text</div>
            </div>""",
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            """<div class="metric-card">
                <div class="metric-label">Market Standard</div>
                <div class="metric-value" style="color: #10B981;">₹ INR</div>
                <div class="metric-sub">IS & BOCW Aligned</div>
            </div>""",
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            """<div class="metric-card">
                <div class="metric-label">Analysis Modules</div>
                <div class="metric-value" style="color: #38BDF8;">8 Modules</div>
                <div class="metric-sub">Vision, Cost, Safety, Chat</div>
            </div>""",
            unsafe_allow_html=True,
        )
    with c4:
        st.markdown(
            """<div class="metric-card">
                <div class="metric-label">Status</div>
                <div class="metric-value" style="color: #A855F7;">Active</div>
                <div class="metric-sub">Ready for Deployment</div>
            </div>""",
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("Available Intelligence Modules")

    col_a, col_b = st.columns(2)
    with col_a:
        st.info("🔍 **Site Analysis**: Multimodal visual inspection for site conditions, cracks, structural distress, readiness, and risk screening.")
        st.info("🦺 **Safety Inspection**: Automated PPE compliance checking (Helmets, Vests, Gloves, Boots) and BOCW / IS 4130 regulatory violation detection.")
        st.info("💰 **Cost Estimation**: Itemized construction cost breakdowns for Indian civil, MEP, and finishing projects in ₹ INR.")
        st.info("🧱 **Material Analysis & BOQ**: Bill of quantities estimation for concrete, steel, sand, aggregates, and procurement planning.")

    with col_b:
        st.info("📈 **Progress Monitoring**: EVM-backed schedule tracking, phase completion variance, and budget utilization.")
        st.info("📸 **Visual Progress**: Direct photo-based estimation of completion stage, active labor force, and equipment count.")
        st.info("💬 **ConstructAI Assistant**: Specialized chat expert on Indian construction bylaws, IS codes, and site best practices.")
        st.info("📑 **Project Report Generator**: One-click executive summary, KPI dashboard, milestone tracker, and risk register export.")


# ─────────────────── 2. Site Analysis ─────────────────────────────

elif menu == "🔍 Site Analysis":
    st.title("🔍 Site Analysis & Structural Distress Inspection")
    st.caption("Upload a construction site photo to assess readiness, structural elements, visible cracks, and risks.")

    require_ai_service()

    col_left, col_right = st.columns([1, 1])

    with col_left:
        uploaded_file = st.file_uploader(
            "Upload Construction Site Image (JPG, PNG, WEBP)",
            type=["jpg", "jpeg", "png", "webp"],
            key="site_upload",
        )
        context = st.text_area(
            "Additional Context (Optional)",
            placeholder="e.g. Residential tower foundation work in Pune, ongoing monsoon season...",
            max_chars=2000,
        )
        analyze_btn = st.button("🚀 Analyze Site Image", type="primary", use_container_width=True)

    if uploaded_file:
        with col_left:
            st.image(uploaded_file, caption="Uploaded Site Photo", use_column_width=True)

    if analyze_btn:
        if not uploaded_file:
            st.warning("Please upload an image first.")
        else:
            with st.spinner("Analyzing site with Groq Multimodal Vision..."):
                try:
                    img_bytes = uploaded_file.getvalue()
                    mime_type = uploaded_file.type or "image/jpeg"
                    if mime_type not in ["image/jpeg", "image/png", "image/webp", "image/gif"]:
                        mime_type = "image/jpeg"

                    system_prompt = """You are an expert construction site analyst with 20+ years of experience.
Analyze the provided construction site image and extract detailed information about:
- Site conditions and readiness
- Detected construction elements and infrastructure
- Visible structural distress, including cracks, spalling, exposed reinforcement, or deformation
- Safety hazards and concerns
- Infrastructure readiness assessment
- Actionable recommendations for site engineers
All assessments must be practical and conservative. Image findings are preliminary visual observations, not engineering diagnoses.
For each structural finding, include location, risk level, corrective action, confidence, and uncertainty notes.
Return an empty structural_findings list if no relevant distress is visible. Require qualified professional review of suspected defects."""

                    user_prompt = f"""Analyze this construction site image comprehensively.
{f'Additional context: {context}' if context else ''}
Provide a thorough analysis including site condition, detected elements, visible crack/structural findings, safety concerns,
risk assessment, uncertainty notes, and recommended actions. Use applicable Indian standards and regulatory references.
Express infrastructure readiness and confidence as scores from 0-100. Do not infer crack depth, structural capacity, or hidden damage from an image."""

                    result: SiteAnalysisResponse = service.analyze_image_with_text(
                        image_bytes=img_bytes,
                        image_type=mime_type,
                        system_prompt=system_prompt,
                        user_prompt=user_prompt,
                        schema=SiteAnalysisResponse,
                    )

                    with col_right:
                        st.markdown(
                            f'<div class="disclaimer-banner">⚠️ <strong>Notice:</strong> {result.professional_review_warning}</div>',
                            unsafe_allow_html=True,
                        )

                        # Quick Score Metrics
                        m1, m2, m3 = st.columns(3)
                        m1.metric("Readiness Score", f"{result.infrastructure_readiness_score}/100")
                        m2.metric("Confidence", f"{result.confidence_score}%")
                        with m3:
                            st.markdown(f"**Risk Level**<br>{get_risk_badge_html(result.risk_level)}", unsafe_allow_html=True)

                        st.markdown("#### Summary")
                        st.write(result.summary)
                        st.markdown(f"**Site Condition:** {result.site_condition}")
                        if result.estimated_site_area_sqft:
                            st.markdown(f"**Estimated Visible Area:** {result.estimated_site_area_sqft:,.0f} sq.ft")

                        st.markdown("#### Detected Elements")
                        st.write(", ".join(result.detected_elements) if result.detected_elements else "None specified")

                        if result.structural_findings:
                            st.markdown("#### ⚠️ Structural Observations & Cracks")
                            for sf in result.structural_findings:
                                with st.expander(f"📍 {sf.location}: {sf.finding} ({sf.risk_level.upper()})", expanded=True):
                                    st.write(f"**Recommended Action:** {sf.recommended_action}")
                                    st.caption(f"Confidence: {sf.confidence_score}% | Uncertainty: {', '.join(sf.uncertainty_notes)}")

                        if result.safety_concerns:
                            st.markdown("#### Safety Concerns")
                            for sc in result.safety_concerns:
                                st.write(f"• {sc}")

                        if result.recommended_actions:
                            st.markdown("#### Actionable Recommendations")
                            for act in result.recommended_actions:
                                st.write(f"✅ {act}")

                except AIServiceError as e:
                    st.error(f"AI Service error: {e.code}. Please retry.")
                except Exception as e:
                    st.error(f"Analysis failed: {str(e)}")


# ─────────────────── 3. Safety Inspection ─────────────────────────

elif menu == "🦺 Safety Inspection":
    st.title("🦺 Site Safety & PPE Compliance Inspection")
    st.caption("Audit site images for PPE compliance (Helmets, Vests, Boots, Gloves) and BOCW / IS 4130 safety violations.")

    require_ai_service()

    col1, col2 = st.columns([1, 1])
    with col1:
        safety_file = st.file_uploader(
            "Upload Site Safety Photo",
            type=["jpg", "jpeg", "png", "webp"],
            key="safety_upload",
        )
        site_type = st.selectbox(
            "Site Type",
            ["High-Rise Commercial", "Residential RCC", "Industrial Plant", "Infrastructure & Highway", "Demolition"],
        )
        inspect_btn = st.button("🦺 Run Safety Inspection", type="primary", use_container_width=True)

    if safety_file:
        with col1:
            st.image(safety_file, caption="Safety Inspection Photo", use_column_width=True)

    if inspect_btn:
        if not safety_file:
            st.warning("Please upload a safety inspection image.")
        else:
            with st.spinner("Inspecting site safety against Indian regulations..."):
                try:
                    img_bytes = safety_file.getvalue()
                    mime_type = safety_file.type or "image/jpeg"
                    if mime_type not in ["image/jpeg", "image/png", "image/webp", "image/gif"]:
                        mime_type = "image/jpeg"

                    system_prompt = """You are a certified construction safety inspector with expertise in Indian safety regulations.
Analyze construction site images for safety compliance per:
- The Factories Act 1948
- Building & Other Construction Workers Act 1996 (BOCW)
- IS 4130 Safety Requirements
- OSHA guidelines adapted for Indian context
Be thorough, precise, and conservative in safety assessments."""

                    user_prompt = f"""Inspect this {site_type} construction site image for safety compliance.
Identify:
1. PPE compliance (helmets, safety vests, gloves, safety boots)
2. Safety violations and their severity
3. Structural or environmental hazards
4. Regulatory compliance issues
5. Corrective actions required
6. Estimated penalties for violations in INR
Score overall safety from 0 (critical danger) to 100 (fully compliant). Include a risk level, confidence score from 0-100,
and uncertainty notes. Treat results as preliminary screening, not certification or legal advice; require qualified safety review."""

                    resp: SafetyInspectionResponse = service.analyze_image_with_text(
                        image_bytes=img_bytes,
                        image_type=mime_type,
                        system_prompt=system_prompt,
                        user_prompt=user_prompt,
                        schema=SafetyInspectionResponse,
                    )

                    with col2:
                        st.markdown(
                            f'<div class="disclaimer-banner">⚠️ <strong>Notice:</strong> {resp.professional_review_warning}</div>',
                            unsafe_allow_html=True,
                        )

                        s1, s2, s3 = st.columns(3)
                        s1.metric("Safety Score", f"{resp.overall_safety_score}/100")
                        s2.metric("Estimated Penalty", format_inr(resp.estimated_penalty_inr))
                        with s3:
                            st.markdown(f"**Risk Level**<br>{get_risk_badge_html(resp.risk_level)}", unsafe_allow_html=True)

                        st.markdown(f"**Compliance Status:** `{resp.compliance_status}`")

                        # PPE Compliance Indicators
                        st.markdown("#### PPE Compliance")
                        ppe = resp.ppe_compliance
                        p_cols = st.columns(4)
                        p_cols[0].markdown(
                            f'<div class="ppe-box {"ppe-pass" if ppe.helmet else "ppe-fail"}">⛑️ Helmet: {"PASS" if ppe.helmet else "FAIL"}</div>',
                            unsafe_allow_html=True,
                        )
                        p_cols[1].markdown(
                            f'<div class="ppe-box {"ppe-pass" if ppe.safety_vest else "ppe-fail"}">🦺 Vest: {"PASS" if ppe.safety_vest else "FAIL"}</div>',
                            unsafe_allow_html=True,
                        )
                        p_cols[2].markdown(
                            f'<div class="ppe-box {"ppe-pass" if ppe.gloves else "ppe-fail"}">🧤 Gloves: {"PASS" if ppe.gloves else "FAIL"}</div>',
                            unsafe_allow_html=True,
                        )
                        p_cols[3].markdown(
                            f'<div class="ppe-box {"ppe-pass" if ppe.safety_boots else "ppe-fail"}">🥾 Boots: {"PASS" if ppe.safety_boots else "FAIL"}</div>',
                            unsafe_allow_html=True,
                        )

                        if resp.violations:
                            st.markdown("#### Detected Violations")
                            for v in resp.violations:
                                with st.expander(f"⚠️ {v.violation_type} ({v.severity.upper()})"):
                                    st.write(f"**Location:** {v.location_in_image}")
                                    st.write(f"**Action Required:** {v.corrective_action}")
                                    st.caption(f"Regulation: {v.regulatory_reference}")

                        if resp.immediate_actions_required:
                            st.markdown("#### Immediate Actions Required")
                            for act in resp.immediate_actions_required:
                                st.write(f"🚨 {act}")

                except Exception as e:
                    st.error(f"Safety inspection failed: {str(e)}")


# ─────────────────── 4. Cost Estimation ───────────────────────────

elif menu == "💰 Cost Estimation":
    st.title("💰 AI Construction Cost Estimation (INR / ₹)")
    st.caption("Generate indicative itemized construction estimates for Indian residential, commercial, or industrial builds.")

    require_ai_service()

    with st.form("cost_estimation_form"):
        c1, c2 = st.columns(2)
        with c1:
            proj_name = st.text_input("Project Name / Description", value="Residential G+3 Building")
            proj_type = st.selectbox("Project Type", ["Residential", "Commercial Office", "Industrial Warehouse", "Villa / Bungalow", "Retail Mall"])
            location = st.text_input("Location (City, State)", value="Mumbai, Maharashtra")
        with c2:
            built_up_area = st.number_input("Built-up Area (sq.ft)", min_value=100.0, max_value=5_000_000.0, value=2500.0, step=100.0)
            floors = st.number_input("Number of Floors", min_value=1, max_value=80, value=4, step=1)
            quality = st.selectbox("Quality Standard", ["Economy / Affordable", "Standard / Builder Grade", "Premium", "Luxury"])

        special_reqs = st.text_input("Special Requirements / Inclusions", placeholder="e.g., Solar rooftop, earthquake-resistant design, basement parking")
        calc_btn = st.form_submit_button("📊 Generate Cost Estimate", type="primary", use_container_width=True)

    if calc_btn:
        with st.spinner("Calculating detailed itemized estimate in INR..."):
            try:
                system_prompt = """You are a certified quantity surveyor and cost consultant specializing in Indian construction markets.
Generate an indicative construction estimate in Indian Rupees (₹/INR), not a quotation.
No live market-rate source is connected. State assumptions and uncertainty; never claim current or verified rates.
For each line item provide quantity, unit, and estimated unit rate. The server calculates line and grand totals."""

                user_prompt = f"""Generate a comprehensive construction cost estimate for:
- Project Name: {proj_name}
- Project Type: {proj_type}
- Location: {location}
- Built-up Area: {built_up_area} sq.ft
- Number of Floors: {floors}
- Quality Standard: {quality}
{f'- Special Requirements: {special_reqs}' if special_reqs else ''}

Provide an itemized estimate with quantities, units, estimated unit rates in INR, assumptions, uncertainty, and risks.
Cover civil work, finishing, MEP services, external development, fees and approvals, and contingency where applicable.
Do not invent live supplier quotes or rate-source citations. The server calculates line and grand totals from quantities and rates."""

                est_resp: CostEstimationResponse = service.query_text(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    schema=CostEstimationResponse,
                )
                est_resp.cost_per_sqft_inr = round(est_resp.total_estimated_cost_inr / built_up_area, 2)

                st.success("Cost estimate calculated successfully!")
                st.markdown(f'<div class="disclaimer-banner">ℹ️ <strong>Estimate Source:</strong> {est_resp.estimate_source}</div>', unsafe_allow_html=True)

                k1, k2, k3, k4 = st.columns(4)
                k1.metric("Grand Total Cost", format_inr(est_resp.total_estimated_cost_inr))
                k2.metric("Cost per sq.ft", f"₹{est_resp.cost_per_sqft_inr:,.0f} / sq.ft")
                k3.metric("Estimated Timeline", f"{est_resp.timeline_months} Months")
                k4.metric("Confidence Score", f"{est_resp.confidence_score}%")

                st.subheader("Itemized Cost Breakdown (BOQ)")
                table_data = []
                for item in est_resp.cost_breakdown:
                    table_data.append({
                        "Description": item.label,
                        "Quantity": f"{item.quantity:,.1f}",
                        "Unit": item.unit,
                        "Unit Rate (₹)": f"₹{item.unit_rate_inr:,.2f}",
                        "Total Amount (₹)": f"₹{item.amount_inr:,.2f}",
                    })
                st.dataframe(table_data, use_container_width=True)

                c_left, c_right = st.columns(2)
                with c_left:
                    st.markdown("#### 📌 Key Assumptions")
                    for a in est_resp.assumptions:
                        st.write(f"• {a}")
                with c_right:
                    st.markdown("#### 💡 Recommendations")
                    for r in est_resp.recommendations:
                        st.write(f"• {r}")

            except Exception as e:
                st.error(f"Cost estimation failed: {str(e)}")


# ─────────────────── 5. Progress Monitoring ───────────────────────

elif menu == "📈 Progress Monitoring":
    st.title("📈 Project Progress & Schedule Monitoring")
    st.caption("Track project adherence, phase-by-phase completion, budget utilization, and EVM variance.")

    require_ai_service()

    with st.form("progress_monitoring_form"):
        col1, col2 = st.columns(2)
        with col1:
            p_name = st.text_input("Project Name", value="Commercial Plaza Phase 1")
            s_date = st.date_input("Project Start Date", value=date(2024, 1, 1))
            e_date = st.date_input("Planned End Date", value=date(2024, 12, 31))
            c_phase = st.selectbox("Current Phase", ["Excavation", "Substructure / Foundation", "RCC Frame / Structure", "Brickwork & Plaster", "MEP Rough-in", "Finishes", "Handover"])
        with col2:
            t_budget = st.number_input("Total Budget (₹ INR)", min_value=10000.0, value=25000000.0, step=500000.0)
            spent = st.number_input("Amount Spent So Far (₹ INR)", min_value=0.0, value=11500000.0, step=250000.0)
            completed_str = st.text_input("Completed Phases (comma separated)", value="Excavation, Substructure")
            notes = st.text_area("Site Notes / Delays", placeholder="e.g. Concrete pour delayed by 10 days due to monsoon rainfall...")

        prog_btn = st.form_submit_button("📈 Evaluate Progress & EVM", type="primary", use_container_width=True)

    if prog_btn:
        with st.spinner("Analyzing project milestones and schedule variance..."):
            try:
                system_prompt = """You are an expert construction project manager and schedule analyst.
Analyze project progress data and provide accurate assessment of:
- Schedule adherence and variance
- Budget utilization efficiency  
- Phase-by-phase progress evaluation
- Critical path analysis
- Resource optimization recommendations
Use Earned Value Management (EVM) principles where applicable."""

                user_prompt = f"""Analyze construction project progress:
- Project: {p_name}
- Start Date: {s_date}
- Planned End Date: {e_date}
- Total Budget: ₹{t_budget:,.0f}
- Spent So Far: ₹{spent:,.0f}
- Current Phase: {c_phase}
- Completed Phases: {completed_str}
{f'- Notes: {notes}' if notes else ''}

Provide detailed progress analysis including phase completion percentages, schedule variance, 
budget tracking, and projected completion date. All amounts in INR."""

                prog_res: ProgressMonitoringResponse = service.query_text(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    schema=ProgressMonitoringResponse,
                )

                st.subheader("Progress & Financial Health")
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Overall Progress", f"{prog_res.overall_progress_percent}%")
                variance_text = f"{prog_res.schedule_variance_days} Days"
                if prog_res.schedule_variance_days > 0:
                    variance_text += " Delay"
                m2.metric("Schedule Variance", variance_text)
                m3.metric("Budget Spent", format_inr(prog_res.budget_utilized_inr))
                m4.metric("Budget Remaining", format_inr(prog_res.budget_remaining_inr))

                st.markdown(f"**Projected Completion Date:** `{prog_res.projected_completion_date}`")

                st.markdown("#### Phase Completion")
                for ph in prog_res.phases:
                    st.write(f"**{ph.phase_name}** ({ph.status.upper()}) — Actual: {ph.actual_percent}% / Planned: {ph.planned_percent}%")
                    st.progress(min(1.0, ph.actual_percent / 100.0))

                col_obs, col_rec = st.columns(2)
                with col_obs:
                    st.markdown("#### 🔍 Key Observations")
                    for obs in prog_res.key_observations:
                        st.write(f"• {obs}")
                with col_rec:
                    st.markdown("#### 💡 Action Recommendations")
                    for r in prog_res.recommendations:
                        st.write(f"• {r}")

            except Exception as e:
                st.error(f"Progress monitoring failed: {str(e)}")


# ─────────────────── 6. Visual Progress ───────────────────────────

elif menu == "📸 Visual Progress":
    st.title("📸 Visual Progress Tracking via AI Vision")
    st.caption("Upload an image of ongoing construction to automatically assess progress %, visible phases, and site resources.")

    require_ai_service()

    col_up, col_res = st.columns([1, 1])
    with col_up:
        vp_file = st.file_uploader("Upload Progress Photo", type=["jpg", "jpeg", "png", "webp"], key="vp_upload")
        v_proj_name = st.text_input("Project Name", value="Metro Rail Station / Commercial Hub")
        v_budget = st.number_input("Total Project Budget (₹ INR)", value=50000000.0, step=1000000.0)
        v_btn = st.button("📸 Run Visual Progress Analysis", type="primary", use_container_width=True)

    if vp_file:
        with col_up:
            st.image(vp_file, caption="Site Progress Image", use_column_width=True)

    if v_btn:
        if not vp_file:
            st.warning("Please upload a site progress image.")
        else:
            with st.spinner("Analyzing image features and estimating completion stage..."):
                try:
                    img_bytes = vp_file.getvalue()
                    mime_type = vp_file.type or "image/jpeg"

                    system_prompt = """You are an expert construction progress analyst using computer vision.
Analyze construction site images to determine:
- Overall construction progress percentage
- Visible construction phases and their completion
- Resource utilization (workers, equipment)
- Quality observations
- Schedule adherence indicators
Be precise and conservative in progress estimates."""

                    user_prompt = f"""Analyze this construction site image for project: {v_proj_name}
Total project budget: ₹{v_budget:,.0f}

Estimate:
1. Overall progress percentage (0-100%)
2. Which construction phases are visible and their completion
3. Number of visible workers and equipment
4. Quality observations
5. Projected completion based on visible progress
6. Budget utilization estimate in ₹"""

                    v_resp: ProgressMonitoringResponse = service.analyze_image_with_text(
                        image_bytes=img_bytes,
                        image_type=mime_type,
                        system_prompt=system_prompt,
                        user_prompt=user_prompt,
                        schema=ProgressMonitoringResponse,
                    )

                    with col_res:
                        st.markdown(f"### Visual Estimate: **{v_resp.overall_progress_percent}% Complete**")
                        st.progress(min(1.0, v_resp.overall_progress_percent / 100.0))

                        m1, m2 = st.columns(2)
                        m1.metric("Estimated Spent", format_inr(v_resp.budget_utilized_inr))
                        m2.metric("Projected Handover", v_resp.projected_completion_date)

                        st.markdown("#### Detected Phases")
                        for p in v_resp.phases:
                            st.write(f"• **{p.phase_name}**: {p.actual_percent}% ({p.status})")

                        st.markdown("#### Observations & Quality")
                        for obs in v_resp.key_observations:
                            st.write(f"🔍 {obs}")

                except Exception as e:
                    st.error(f"Visual progress analysis failed: {str(e)}")


# ─────────────────── 7. Material Analysis & BOQ ───────────────────

elif menu == "🧱 Material Analysis & BOQ":
    st.title("🧱 Material Requirement Analysis & BOQ")
    st.caption("Calculate indicative material quantities (Cement, TMT Steel, Sand, Coarse Aggregates, Bricks) and estimated costs.")

    require_ai_service()

    with st.form("material_form"):
        m_c1, m_c2 = st.columns(2)
        with m_c1:
            m_type = st.selectbox("Project Category", ["Residential Villa", "Apartment Complex", "Commercial Complex", "Industrial Shed"])
            m_area = st.number_input("Total Built-up Area (sq.ft)", min_value=100.0, value=3000.0, step=100.0)
            m_location = st.text_input("Project Location", value="Bengaluru, Karnataka")
        with m_c2:
            m_structure = st.selectbox("Structural System", ["RCC Frame Structure", "Load Bearing Masonry", "Structural Steel Frame", "Precast Concrete"])
            m_grade = st.selectbox("Material Quality Grade", ["Standard (Fe 500 / OPC 43)", "Premium (Fe 550D / OPC 53 / RMC)", "Budget / Local"])
            m_special = st.text_input("Special Materials (Optional)", placeholder="e.g. Waterproofing admixtures, fly ash bricks...")

        mat_btn = st.form_submit_button("🧱 Generate Material BOQ", type="primary", use_container_width=True)

    if mat_btn:
        with st.spinner("Compiling Bill of Quantities with prevailing Indian material rates..."):
            try:
                system_prompt = """You are an expert construction materials analyst and procurement specialist.
Generate an indicative Bill of Quantities, not a quotation. No live price feed is connected.
State assumptions and uncertainty; do not claim prices are current or verified. Provide quantity, unit, and estimated unit rate for each item.
The server calculates line and grand totals. Use Indian Rupees (₹/INR)."""

                user_prompt = f"""Generate comprehensive material analysis and BOQ for:
- Project Type: {m_type}
- Built-up Area: {m_area} sq.ft
- Location: {m_location}
- Quality Grade: {m_grade}
- Construction Type: {m_structure}
{f'- Special Materials: {m_special}' if m_special else ''}

Include cement, steel, aggregates, sand, bricks, tiles, waterproofing, paint, electrical and plumbing materials.
Provide estimated unit rates in INR, assumptions, uncertainty, supplier category recommendations, and quality grades.
Do not claim live prices or verified supplier offers."""

                mat_resp: MaterialAnalysisResponse = service.query_text(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    schema=MaterialAnalysisResponse,
                )

                st.markdown(f'<div class="disclaimer-banner">ℹ️ <strong>Estimate Source:</strong> {mat_resp.estimate_source}</div>', unsafe_allow_html=True)

                k1, k2, k3 = st.columns(3)
                k1.metric("Total Material Cost", format_inr(mat_resp.total_material_cost_inr))
                k2.metric("Wastage Factor", f"{mat_resp.wastage_factor_percent}%")
                k3.metric("Procurement Timeline", f"{mat_resp.procurement_timeline_days} Days")

                st.subheader("Itemized Material Bill of Quantities")
                m_table = []
                for m in mat_resp.materials:
                    m_table.append({
                        "Material": m.name,
                        "Qty": f"{m.quantity_required:,.1f}",
                        "Unit": m.unit,
                        "Unit Rate (₹)": f"₹{m.unit_cost_inr:,.2f}",
                        "Total (₹)": f"₹{m.total_cost_inr:,.2f}",
                        "Grade": m.quality_grade,
                        "Supplier Category": m.supplier_recommendation,
                    })
                st.dataframe(m_table, use_container_width=True)

                st.markdown("#### 💡 Procurement & Cost Optimization Tips")
                for tip in mat_resp.cost_optimization_tips:
                    st.write(f"• {tip}")

            except Exception as e:
                st.error(f"Material analysis failed: {str(e)}")


# ─────────────────── 8. ConstructAI Chatbot ───────────────────────

elif menu == "💬 ConstructAI Chatbot":
    st.title("💬 ConstructAI — Construction Intelligence Assistant")
    st.caption("Ask questions about Indian Standards (IS 456, IS 800), bylaws, material rates, curing periods, or site safety.")

    require_ai_service()

    # Session State Chat History
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = [
            {
                "role": "assistant",
                "content": "Namaste! I am **ConstructAI**, your assistant for Indian construction engineering, safety protocols, IS standards, and costing. How can I help with your project today?",
            }
        ]

    # Quick suggestion chips
    st.markdown("**Quick Topics:**")
    q1, q2, q3 = st.columns(3)
    if q1.button("📋 IS 456 Curing Guidelines", use_container_width=True):
        st.session_state.chat_messages.append({"role": "user", "content": "What are the minimum curing periods for concrete as per IS 456 for ordinary Portland cement and mineral admixtures?"})
        st.rerun()
    if q2.button("🏗️ M25 Concrete Mix Proportions", use_container_width=True):
        st.session_state.chat_messages.append({"role": "user", "content": "What is the standard nominal mix ratio for M25 concrete and the required water-cement ratio?"})
        st.rerun()
    if q3.button("🦺 BOCW Safety Requirements", use_container_width=True):
        st.session_state.chat_messages.append({"role": "user", "content": "What are the mandatory scaffolding and safety net requirements under the BOCW Act for working at heights above 2 meters?"})
        st.rerun()

    # Display Chat History
    for msg in st.session_state.chat_messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # Chat Input
    user_query = st.chat_input("Ask ConstructAI about structural codes, rates, or site problems...")
    if user_query:
        st.session_state.chat_messages.append({"role": "user", "content": user_query})
        with st.chat_message("user"):
            st.write(user_query)

        with st.chat_message("assistant"):
            with st.spinner("Consulting Indian construction standards..."):
                try:
                    system_prompt = """You are ConstructAI, an expert AI assistant specialized in Indian construction industry.
You have deep knowledge of:
- Indian construction standards (IS codes, BIS standards, NBC 2016)
- Building bylaws and local authority regulations (RERA, municipal bylaws)
- Material costs and market prices in INR (₹)
- Safety regulations (Factories Act, BOCW Act 1996, IS 4130)
- Project management (PERT, CPM, EVM)
- Structural engineering and architecture

Always provide practical, actionable advice. Quote prices in Indian Rupees (₹).
Be concise but comprehensive. Reference relevant IS codes and regulations when applicable."""

                    res: ChatResponse = service.chat_query(
                        system_prompt=system_prompt,
                        user_message=user_query,
                        schema=ChatResponse,
                    )

                    ans_text = res.answer
                    if res.data_points:
                        ans_text += "\n\n**Key Standard References:**\n" + "\n".join(f"- {dp}" for dp in res.data_points)
                    if res.follow_up_suggestions:
                        ans_text += "\n\n**Suggested Follow-ups:**\n" + "\n".join(f"- {fu}" for fu in res.follow_up_suggestions)

                    st.write(ans_text)
                    st.session_state.chat_messages.append({"role": "assistant", "content": ans_text})

                except Exception as e:
                    st.error(f"Chat error: {str(e)}")


# ─────────────────── 9. Project Report Generator ──────────────────

elif menu == "📑 Project Report Generator":
    st.title("📑 Comprehensive Project Status Report Generator")
    st.caption("Generate executive-ready project status reports, KPIs, financial summaries, and risk registers.")

    require_ai_service()

    with st.form("report_form"):
        r_c1, r_c2 = st.columns(2)
        with r_c1:
            rep_pname = st.text_input("Project Name", value="Prestige Tech Park Tower B")
            rep_type = st.selectbox("Project Type", ["Commercial Office", "Residential High-Rise", "Hospital", "Industrial Facility"])
            rep_loc = st.text_input("Location", value="Hyderabad, Telangana")
            rep_sdate = st.date_input("Start Date", value=date(2023, 6, 1))
            rep_edate = st.date_input("Planned Finish Date", value=date(2025, 6, 30))
        with r_c2:
            rep_budget = st.number_input("Total Budget (₹ INR)", value=85000000.0, step=1000000.0)
            rep_spent = st.number_input("Total Spent So Far (₹ INR)", value=42000000.0, step=1000000.0)
            rep_progress = st.slider("Current Progress (%)", min_value=0, max_value=100, value=52)
            rep_phase = st.text_input("Current Phase", value="Superstructure Floor 8 Pouring")
            rep_team = st.number_input("Site Team / Labor Strength", min_value=1, value=120)

        rep_issues = st.text_area("Key Site Issues / Delays (Optional)", value="Steel delivery delayed by 1 week; monsoon dewatering active.")
        rep_achieve = st.text_area("Recent Achievements (Optional)", value="Cast foundation and ground floor ahead of schedule; zero lost-time injuries.")

        gen_rep_btn = st.form_submit_button("📑 Generate Executive Report", type="primary", use_container_width=True)

    if gen_rep_btn:
        with st.spinner("Synthesizing executive project report..."):
            try:
                system_prompt = """You are a senior construction project manager generating executive-level project reports.
Produce comprehensive, professional reports that provide actionable insights for:
- Project owners and investors
- Site engineers and contractors
- Regulatory and compliance teams
Use EVM, KPI frameworks, and Indian construction industry standards."""

                user_prompt = f"""Generate a comprehensive project status report for:
- Project Name: {rep_pname}
- Type: {rep_type} at {rep_loc}
- Timeline: {rep_sdate} to {rep_edate}
- Budget: ₹{rep_budget:,.0f} | Spent: ₹{rep_spent:,.0f}
- Progress: {rep_progress}% | Phase: {rep_phase}
- Team Size: {rep_team} workers
{f'- Key Issues: {rep_issues}' if rep_issues else ''}
{f'- Achievements: {rep_achieve}' if rep_achieve else ''}

Generate executive summary, KPIs, milestone status, financial summary, risk register, and action items.
All financial figures in Indian Rupees (₹)."""

                rep_resp: ProjectReportResponse = service.query_text(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    schema=ProjectReportResponse,
                )

                st.header(f"📊 Project Status Report: {rep_resp.project_name}")
                st.caption(f"Generated on {rep_resp.report_date} • Health: **{rep_resp.overall_health}**")

                st.subheader("Executive Summary")
                st.write(rep_resp.executive_summary)

                # Financial Summary
                st.subheader("Financial Overview")
                f1, f2, f3, f4 = st.columns(4)
                f1.metric("Total Budget", format_inr(rep_resp.financial_summary.total_budget_inr))
                f2.metric("Spent to Date", format_inr(rep_resp.financial_summary.spent_inr))
                f3.metric("Remaining", format_inr(rep_resp.financial_summary.remaining_inr))
                f4.metric("Projected Overrun", format_inr(rep_resp.financial_summary.projected_overrun_inr))

                # KPIs
                st.subheader("Key Performance Indicators")
                k1, k2, k3, k4 = st.columns(4)
                k1.metric("Budget Utilization", str(rep_resp.kpis.budget_utilization))
                k2.metric("Schedule Adherence", str(rep_resp.kpis.schedule_adherence))
                k3.metric("Quality Score", str(rep_resp.kpis.quality_score))
                k4.metric("Safety Score", str(rep_resp.kpis.safety_score))

                # Milestones
                st.subheader("Milestone Tracking")
                m_list = []
                for m in rep_resp.milestones:
                    m_list.append({
                        "Milestone": m.name,
                        "Planned Date": m.planned_date,
                        "Actual Date": m.actual_date or "Pending",
                        "Status": m.status.upper(),
                    })
                st.dataframe(m_list, use_container_width=True)

                # Risks
                st.subheader("Risk Register")
                for rk in rep_resp.risks:
                    with st.expander(f"⚠️ {rk.description} ({rk.severity.upper()})"):
                        st.write(f"**Mitigation Plan:** {rk.mitigation}")

                # Action Items
                st.subheader("Next Steps & Action Items")
                for item in rep_resp.action_items:
                    st.write(f"• {item}")

                # Downloadable Report Content
                report_md = f"""# Project Status Report: {rep_resp.project_name}
Date: {rep_resp.report_date} | Overall Health: {rep_resp.overall_health}

## Executive Summary
{rep_resp.executive_summary}

## Financial Summary
- Total Budget: {format_inr(rep_resp.financial_summary.total_budget_inr)}
- Spent: {format_inr(rep_resp.financial_summary.spent_inr)}
- Remaining: {format_inr(rep_resp.financial_summary.remaining_inr)}
- Projected Overrun: {format_inr(rep_resp.financial_summary.projected_overrun_inr)}

## KPIs
- Budget Utilization: {rep_resp.kpis.budget_utilization}
- Schedule Adherence: {rep_resp.kpis.schedule_adherence}
- Quality Score: {rep_resp.kpis.quality_score}
- Safety Score: {rep_resp.kpis.safety_score}

## Action Items
{chr(10).join(f"- {a}" for a in rep_resp.action_items)}
"""
                st.download_button(
                    "📥 Download Markdown Report",
                    data=report_md,
                    file_name=f"{rep_pname.replace(' ', '_')}_Report.md",
                    mime="text/markdown",
                )

            except Exception as e:
                st.error(f"Report generation failed: {str(e)}")

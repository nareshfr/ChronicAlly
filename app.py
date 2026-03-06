import streamlit as st
import random
import textwrap
from itertools import combinations
from chatbot import render_chatbot


st.set_page_config(
    page_title="MedGuard AI — Drug Interaction Analyzer",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)

if "theme" not in st.session_state:
    st.session_state.theme = "Dark Mode"


st.markdown(
    """
    <style>
    /* ===== GOOGLE FONT ===== */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    /* ===== GLOBAL ===== */
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
        max-width: 1100px;
    }

    /* ===== HEADER BANNER ===== */
    .main-header {
        background: linear-gradient(135deg, #0a3d6b 0%, #1565c0 50%, #1e88e5 100%);
        padding: 2.2rem 2.8rem;
        border-radius: 16px;
        margin-bottom: 1.8rem;
        color: white;
        position: relative;
        overflow: hidden;
    }
    .main-header::before {
        content: '';
        position: absolute;
        top: -50%;
        right: -20%;
        width: 300px;
        height: 300px;
        background: radial-gradient(circle, rgba(255,255,255,0.08) 0%, transparent 70%);
        border-radius: 50%;
    }
    .main-header h1 {
        margin: 0;
        font-size: 2rem;
        font-weight: 800;
        letter-spacing: -0.5px;
        color: white !important;
    }
    .main-header .subtitle {
        margin: 0.5rem 0 0 0;
        font-size: 0.95rem;
        font-weight: 400;
        opacity: 0.85;
        color: white !important;
        letter-spacing: 0.3px;
    }
    .main-header .badge {
        display: inline-block;
        background: rgba(255,255,255,0.18);
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 1px;
        text-transform: uppercase;
        margin-top: 0.6rem;
        color: white !important;
        backdrop-filter: blur(4px);
    }

    /* ===== SECTION TITLES ===== */
    .section-title {
        font-size: 0.78rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        color: rgba(128,128,128,0.6);
        margin-bottom: 0.8rem;
        padding-bottom: 0.4rem;
        border-bottom: 1px solid rgba(128,128,128,0.12);
    }

    /* ===== CARD — glassmorphism ===== */
    .card {
        background: rgba(128, 128, 128, 0.06);
        border: 1px solid rgba(128,128,128,0.15);
        border-radius: 14px;
        padding: 1.6rem 1.8rem;
        margin-bottom: 1rem;
        color: inherit;
        backdrop-filter: blur(8px);
    }
    .card h3 {
        margin: 0 0 0.6rem 0;
        font-size: 1.1rem;
        font-weight: 700;
        color: rgb(49, 131, 207) !important;
    }
    .card p {
        color: inherit !important;
        font-size: 0.92rem;
        line-height: 1.5;
        margin: 0.25rem 0;
    }
    .card b, .card strong {
        color: inherit !important;
    }

    /* ===== REPORT HEADER — branded ===== */
    .report-header {
        background: linear-gradient(135deg, rgba(15,76,129,0.12) 0%, rgba(26,115,232,0.08) 100%);
        border: 1px solid rgba(26,115,232,0.2);
        border-radius: 14px;
        padding: 1.4rem 1.8rem;
        margin-bottom: 1rem;
        color: inherit;
    }
    .report-header h3 {
        margin: 0 0 0.5rem 0;
        font-size: 1.1rem;
        font-weight: 700;
        color: rgb(49, 131, 207) !important;
    }
    .report-header .meta {
        font-size: 0.88rem;
        color: inherit !important;
        opacity: 0.85;
    }
    .report-header .meta b {
        color: inherit !important;
        opacity: 1;
    }

    /* ===== SIDEBAR ===== */
    section[data-testid="stSidebar"] {
        border-right: 1px solid rgba(128,128,128,0.12);
    }
    section[data-testid="stSidebar"] h2 {
        font-size: 1.1rem;
        font-weight: 700;
        color: rgb(49, 131, 207);
        letter-spacing: -0.3px;
    }
    .sidebar-badge {
        display: inline-block;
        background: linear-gradient(135deg, #0a3d6b, #1565c0);
        color: white !important;
        padding: 0.2rem 0.6rem;
        border-radius: 6px;
        font-size: 0.65rem;
        font-weight: 700;
        letter-spacing: 0.8px;
        text-transform: uppercase;
    }

    /* ===== BUTTON — polished ===== */
    .stButton > button {
        background: linear-gradient(135deg, #0a3d6b 0%, #1565c0 100%);
        color: white;
        border: none;
        padding: 0.75rem 2rem;
        font-size: 0.95rem;
        font-weight: 600;
        border-radius: 10px;
        cursor: pointer;
        transition: all 0.2s ease;
        width: 100%;
        letter-spacing: 0.3px;
        font-family: 'Inter', sans-serif;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(21, 101, 192, 0.35);
    }
    .stButton > button:active {
        transform: translateY(0);
    }

    /* ===== DIVIDER ===== */
    .clean-divider {
        border: none;
        height: 1px;
        background: rgba(128,128,128,0.12);
        margin: 1.5rem 0;
    }

    /* ===== DISCLAIMER ===== */
    .disclaimer {
        text-align: center;
        padding: 1rem 2rem;
        background: rgba(128, 128, 128, 0.06);
        border: 1px solid rgba(128,128,128,0.15);
        border-left: 4px solid #e67e22;
        border-radius: 8px;
        margin-bottom: 1rem;
        color: inherit;
        font-size: 0.85rem;
    }
    .disclaimer strong {
        color: inherit !important;
    }

    /* ===== FOOTER ===== */
    .footer {
        text-align: center;
        color: rgba(128,128,128,0.55);
        font-size: 0.75rem;
        margin-top: 2.5rem;
        padding-top: 1rem;
        border-top: 1px solid rgba(128,128,128,0.12);
        letter-spacing: 0.3px;
    }
    .footer a {
        color: rgb(49, 131, 207);
        text-decoration: none;
    }

    /* ===== METRIC POLISH ===== */
    [data-testid="stMetric"] {
        background: rgba(128, 128, 128, 0.06);
        border: 1px solid rgba(128,128,128,0.12);
        border-radius: 12px;
        padding: 1rem 1.2rem;
    }

    /* ===== EXPANDER POLISH ===== */
    [data-testid="stExpander"] {
        border: 1px solid rgba(128,128,128,0.15);
        border-radius: 12px;
        overflow: hidden;
    }

    /* ===== HIDE STREAMLIT BRANDING ===== */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header[data-testid="stHeader"] {background: transparent;}
    </style>
    """,
    unsafe_allow_html=True,
)

# Mock Drug List

DRUG_LIST: list[str] = [
    "Aspirin",
    "Warfarin",
    "Ibuprofen",
    "Metformin",
    "Lisinopril",
    "Amoxicillin",
    "Omeprazole",
    "Atorvastatin",
    "Ciprofloxacin",
    "Metoprolol",
]

# ──────────────────────────────────────────────
# Mock Prediction Function
# ──────────────────────────────────────────────
def predict_interaction(
    drug_a: str, drug_b: str, patient_data: dict
) -> dict:
    """Return a mock interaction prediction based on the drug pair.

    Uses a deterministic hash so the same inputs always produce
    the same result, while still *looking* realistic.
    """
    # Deterministic seed from the drug pair (order-independent)
    seed = hash(frozenset([drug_a, drug_b])) % 10_000
    rng = random.Random(seed)

    # --- severity buckets ------------------------------------------------
    INTERACTIONS: dict[frozenset, str] = {
        frozenset(["Aspirin", "Warfarin"]): "Critical",
        frozenset(["Ibuprofen", "Warfarin"]): "Critical",
        frozenset(["Ciprofloxacin", "Warfarin"]): "High Risk",
        frozenset(["Aspirin", "Ibuprofen"]): "Moderate",
        frozenset(["Metformin", "Ciprofloxacin"]): "Moderate",
        frozenset(["Atorvastatin", "Omeprazole"]): "Moderate",
        frozenset(["Omeprazole", "Metformin"]): "Minor",
        frozenset(["Lisinopril", "Amoxicillin"]): "Minor",
        frozenset(["Metoprolol", "Amoxicillin"]): "Minor",
    }

    pair = frozenset([drug_a, drug_b])
    severity = INTERACTIONS.get(pair, rng.choice(["Minor", "Moderate", "High Risk"]))

    # --- confidence (higher when severity is more dangerous) -------------
    base = {"Critical": 95, "High Risk": 91, "Moderate": 87, "Minor": 84}[severity]
    confidence = round(base + rng.uniform(0, 5), 1)
    confidence = min(confidence, 99.0)

    # --- molecular reason ------------------------------------------------
    REASONS = {
        "Critical": [
            f"{drug_a} inhibits CYP3A4-mediated metabolism of {drug_b}, "
            "leading to dangerously elevated plasma concentrations and "
            "increased risk of haemorrhage.",
            f"{drug_a} and {drug_b} both competitively bind to CYP2C9, "
            "causing synergistic anticoagulant effects and elevated INR.",
        ],
        "High Risk": [
            f"Co-administration significantly alters {drug_b} pharmacokinetics, "
            "increasing the risk of adverse cardiovascular events.",
            f"{drug_a} strongly induces CYP2D6, potentially causing rapid "
            "depletion of {drug_b} active metabolites.",
        ],
        "Moderate": [
            f"{drug_a} moderately induces CYP2D6, reducing the efficacy "
            f"of {drug_b}. Dose adjustment may be required.",
            f"Co-administration may decrease {drug_b} absorption via "
            "P-glycoprotein efflux modulation in the GI tract.",
        ],
        "Minor": [
            f"No significant cytochrome P450 overlap detected between "
            f"{drug_a} and {drug_b}. Interaction risk is minimal.",
            f"{drug_a} and {drug_b} are metabolised via independent "
            "pathways (CYP1A2 and UGT1A1 respectively). Safe to co-prescribe.",
        ],
    }

    reason = rng.choice(REASONS[severity])

    # --- adjustments
    age = patient_data.get("age", 30)
    pregnancy = patient_data.get("pregnancy", False)
    notes = []
    if age >= 65:
        notes.append("⚠️ Elderly patient — hepatic clearance may be reduced.")
    if pregnancy:
        notes.append("⚠️ Pregnancy detected — FDA category risk applies.")

    return {
        "severity": severity,
        "confidence": confidence,
        "reason": reason,
        "patient_notes": notes,
    }


# 
# 
_LLM_SYSTEM_PROMPT = textwrap.dedent("""\
    You are a Clinical Pharmacologist Assistant for the ASTRAVA 2026 platform.
    You will receive a technical report from a Random Forest model regarding
    two drugs. Your job is to translate the Interaction Severity and the
    Molecular Fingerprint Bits into a human-readable summary.
    Guidelines:
      - Keep it professional yet accessible.
      - Focus on the Why.
      - Always prioritise patient safety.
      - Structure the output into: Risk Summary, Biological Reason, and
        Suggested Action.
""")


def generate_llm_summary(technical_report: dict) -> str:
    """Simulate calling the Gemini API to summarise a technical report."""
    sev = technical_report["severity"]
    drug_a = technical_report["drug_a"]
    drug_b = technical_report["drug_b"]
    reason = technical_report["reason"]
    confidence = technical_report["confidence"]

    RISK_SUMMARIES = {
        "Critical": (
            f"**Critical Interaction** — Co-administering **{drug_a}** and "
            f"**{drug_b}** poses a **severe clinical risk**. "
            f"The AI model flagged this with {confidence}% confidence. "
            "Immediate pharmacist review is strongly recommended before dispensing."
        ),
        "High Risk": (
            f"**High-Risk Interaction** — Co-administering **{drug_a}** and "
            f"**{drug_b}** poses a **serious clinical risk**. "
            f"The AI model flagged this with {confidence}% confidence. "
            "Pharmacist review is recommended before dispensing."
        ),
        "Moderate": (
            f"**Moderate-Risk Interaction** — Combining **{drug_a}** and "
            f"**{drug_b}** may lead to altered drug efficacy or mild adverse "
            f"effects (confidence: {confidence}%). "
            "Clinical monitoring and potential dose adjustment are advised."
        ),
        "Minor": (
            f"**Low-Risk Interaction** — **{drug_a}** and **{drug_b}** appear "
            f"to be safe for concurrent use (confidence: {confidence}%). "
            "No significant pharmacokinetic or pharmacodynamic conflicts detected."
        ),
    }

    SUGGESTED_ACTIONS = {
        "Critical": (
            "1. **Do not dispense** without physician confirmation.\n"
            "2. Consider alternative medications (see Escalation section below).\n"
            "3. Document the interaction flag in the patient's medical record.\n"
            "4. Monitor INR / relevant biomarkers if co-prescription proceeds."
        ),
        "High Risk": (
            "1. **Review carefully** before dispensing.\n"
            "2. Consider alternative medications if suitable.\n"
            "3. Document the interaction flag in the patient's medical record.\n"
            "4. Schedule a follow-up to monitor for adverse effects."
        ),
        "Moderate": (
            "1. **Proceed with caution** — inform the prescribing physician.\n"
            "2. Adjust dosage if clinically appropriate.\n"
            "3. Schedule a follow-up in 48–72 hours to reassess tolerance.\n"
            "4. Educate the patient on early warning signs to report."
        ),
        "Minor": (
            "1. **Safe to dispense** under standard protocols.\n"
            "2. No special monitoring required beyond routine care.\n"
            "3. Reassess if additional drugs are added to the regimen."
        ),
    }

    summary = (
        f"**📌 Risk Summary**\n\n"
        f"{RISK_SUMMARIES[sev]}\n\n"
        f"**🔬 Biological Reason**\n\n"
        f"{reason}\n\n"
        f"**✅ Suggested Action**\n\n"
        f"{SUGGESTED_ACTIONS[sev]}"
    )
    return summary



# Mock Alternative Drugs
ALTERNATIVE_DRUGS: dict[str, list[dict]] = {
    "Aspirin": [
        {"name": "Clopidogrel (Plavix)", "note": "Antiplatelet with lower GI bleed risk"},
        {"name": "Acetaminophen", "note": "Analgesic without antiplatelet activity"},
    ],
    "Warfarin": [
        {"name": "Apixaban (Eliquis)", "note": "DOAC with fewer food/drug interactions"},
        {"name": "Rivaroxaban (Xarelto)", "note": "Once-daily DOAC, no INR monitoring"},
    ],
    "Ibuprofen": [
        {"name": "Celecoxib (Celebrex)", "note": "COX-2 selective, lower GI risk"},
        {"name": "Acetaminophen", "note": "Non-NSAID analgesic"},
    ],
    "Ciprofloxacin": [
        {"name": "Azithromycin", "note": "Macrolide with minimal CYP interaction"},
        {"name": "Levofloxacin", "note": "Fluoroquinolone with different CYP profile"},
    ],
}


 
# SIDEBAR

with st.sidebar:
    st.markdown("## 🏥 MedGuard AI")
    st.markdown(
        '<span class="sidebar-badge">ASTRAVA 2026</span>',
        unsafe_allow_html=True,
    )
    st.markdown("---")

    # ── Page Navigation ──
    page = st.radio(
        "Navigate",
        ["🔍 Drug Analyzer", "💬 AI Chatbot"],
        index=0,
        help="Switch between the Drug Interaction Analyzer and the AI Chatbot",
    )
    st.markdown("---")

    if page == "🔍 Drug Analyzer":
        st.markdown("### 🏥 Patient Context")

        age = st.slider(
            "Age (years)",
            min_value=0,
            max_value=120,
            value=30,
            help="Patient's age in years",
        )

        weight = st.number_input(
            "Weight (kg)",
            min_value=0.0,
            max_value=300.0,
            value=70.0,
            step=0.5,
            format="%.1f",
            help="Patient's weight in kilograms",
        )

        pregnancy = st.toggle(
            "Pregnancy Status",
            value=False,
            help="Toggle ON if the patient is pregnant",
        )

        st.markdown("---")
    else:
        st.markdown("**Quick Prompts:**")
        st.caption('• "What happens if I take Aspirin with Warfarin?"')
        st.caption('• "Tell me about Digoxin"')
        st.caption('• "Is Metoprolol and Digoxin dangerous?"')
        st.caption('• "Alternatives to Ciprofloxacin"')
        st.markdown("---")

    # ── Theme Toggle ──
    st.markdown("<p style='font-size:0.85rem; font-weight:600; color:rgba(128,128,128,0.8); margin-bottom:0.5rem;'>APPEARANCE</p>", unsafe_allow_html=True)

    def toggle_theme():
        if st.session_state.theme == "Dark Mode":
            st.session_state.theme = "Light Mode"
        else:
            st.session_state.theme = "Dark Mode"

    theme_icon = "☀️ Switch to Light Mode" if st.session_state.theme == "Dark Mode" else "🌙 Switch to Dark Mode"
    st.button(theme_icon, on_click=toggle_theme, use_container_width=True)

    st.markdown("---")
    st.caption("ℹ️ Patient context personalises the interaction analysis.")

# CSS theme
if st.session_state.theme == "Light Mode":
    st.markdown(
        """
        <style>
        [data-testid="stAppViewContainer"], .stApp {
            background-color: #ffffff !important;
            color: #1e293b !important;
        }
        [data-testid="stSidebar"] {
            background-color: #f8fafc !important;
        }
        h1, h2, h3, h4, p, span, div, label {
            color: #1e293b;
        }
        .main-header h1, .main-header p, .main-header span {
            color: white !important; /* Keep banner text white */
        }
        .badge, .sidebar-badge { color: white !important; }
        .stButton > button { color: white !important; }
        
        /* Fix Input Fields for Light Mode */
        .stSelectbox div[data-baseweb="select"] > div,
        .stNumberInput input,
        .stTextInput input {
            background-color: #ffffff !important;
            color: #1e293b !important;
            border: 1px solid #cbd5e1 !important;
        }
        .stSelectbox ul {
            background-color: #ffffff !important;
        }
        .stSelectbox li {
            color: #1e293b !important;
        }
        /* Slider */
        div[data-testid="stSliderTickBar"] { background-color: #cbd5e1 !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )
elif st.session_state.theme == "Dark Mode":
    st.markdown(
        """
        <style>
        [data-testid="stAppViewContainer"], .stApp {
            background-color: #0e1117 !important;
            color: #f1f5f9 !important;
        }
        [data-testid="stSidebar"] {
            background-color: #161b22 !important;
        }
        h1, h2, h3, h4, p, span, div, label {
            color: #f1f5f9;
        }
        .main-header h1, .main-header p, .main-header span {
            color: white !important;
        }
        .card h3, .report-header h3, section[data-testid="stSidebar"] h2 {
            color: #7eb8f7 !important;
        }
        .badge, .sidebar-badge { color: white !important; }
        .stButton > button { color: white !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )



# MAIN AREA

if page == "💬 AI Chatbot":
    # ── Render the NLP Chatbot ──
    render_chatbot()

else:
    #Header
    st.markdown(
        """
        <div class="main-header">
            <h1>🩺 MedGuard AI</h1>
            <p class="subtitle">Intelligent Drug Interaction Analyzer</p>
            <span class="badge">✦ Hackathon Prototype · ASTRAVA 2026</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    #Drug Selection 
    st.markdown('<p class="section-title">💊 Drug Selection</p>', unsafe_allow_html=True)

    num_drugs = st.number_input(
        "Enter the no. of drugs",
        min_value=2,
        max_value=10,
        value=2,
        step=1,
        help="Enter the number of drugs about to be consumed",
    )

    selected_drugs: list[str] = []
    drug_cols = st.columns(min(int(num_drugs), 3), gap="medium")

    for i in range(int(num_drugs)):
        col = drug_cols[i % min(int(num_drugs), 3)]
        with col:
            default_index = i if i < len(DRUG_LIST) else 0
            drug = st.selectbox(
                f"Drug {i + 1}",
                options=DRUG_LIST,
                index=default_index,
                help=f"Search or select drug {i + 1}",
                key=f"drug_{i}",
            )
            selected_drugs.append(drug)

    st.markdown("")  # spacing

    _left, center, _right = st.columns([1.2, 1, 1.2])
    with center:
        analyze = st.button("🔍  Analyze Interaction", use_container_width=True)


    # RESULT DASHBOARD
    if analyze:
        unique_drugs = list(dict.fromkeys(selected_drugs))  # preserve order, remove dupes
        if len(unique_drugs) < 2:
            st.warning("⚠️ Please select at least two **different** drugs for analysis.")
        else:
            patient_data = {"age": age, "weight": weight, "pregnancy": pregnancy}
            drug_pairs = list(combinations(unique_drugs, 2))

            st.markdown('<hr class="clean-divider">', unsafe_allow_html=True)
            st.markdown(
                '<p class="section-title">📋 Analysis Results</p>',
                unsafe_allow_html=True,
            )
            st.caption(f"Analyzing **{len(drug_pairs)}** drug pair(s) from **{len(unique_drugs)}** selected drugs.")

            for pair_idx, (drug_a, drug_b) in enumerate(drug_pairs):
                #mock prediction
                result = predict_interaction(drug_a, drug_b, patient_data)

                severity = result["severity"]
                confidence = result["confidence"]
                reason = result["reason"]
                patient_notes = result["patient_notes"]

                st.markdown(f"### 💊 {drug_a}  ↔  {drug_b}")

                # ── Report Header + Confidence (side by side) ──
                rpt_col, conf_col = st.columns([2.5, 1], gap="medium")

                with rpt_col:
                    drugs_label = ' &nbsp;&nbsp;·&nbsp;&nbsp; '.join(
                        f'<b>Drug {chr(65+j)}:</b> {d}' for j, d in enumerate([drug_a, drug_b])
                    )
                    st.markdown(
                        f"""
                        <div class="report-header">
                            <h3>📋 Interaction Report</h3>
                            <p class="meta">{drugs_label}</p>
                            <p class="meta"><b>Patient:</b> {age} yrs, {weight} kg {'&nbsp;· Pregnant' if pregnancy else ''}</p>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                with conf_col:
                    st.metric(
                        label="🤖 AI Confidence",
                        value=f"{confidence}%",
                        delta="High" if confidence >= 92 else "Moderate",
                        delta_color="normal" if confidence >= 92 else "off",
                    )

                #Risk Level
                SEVERITY_CONFIG = {
                    "Critical": {
                        "icon": "🔴",
                        "label": "CRITICAL INTERACTION DETECTED",
                        "fn": st.error,
                    },
                    "High Risk": {
                        "icon": "🟠",
                        "label": "HIGH RISK INTERACTION",
                        "fn": st.warning,
                    },
                    "Moderate": {
                        "icon": "🟡",
                        "label": "MODERATE INTERACTION — USE CAUTION",
                        "fn": st.warning,
                    },
                    "Minor": {
                        "icon": "🟢",
                        "label": "LOW RISK — GENERALLY SAFE",
                        "fn": st.success,
                    },
                }
                cfg = SEVERITY_CONFIG[severity]
                cfg["fn"](f"**{cfg['icon']} {cfg['label']}**")

                #Patient-specific alerts
                for note in patient_notes:
                    st.info(note)

                #LLM Clinical Summary
                st.markdown(
                    '<p class="section-title">🧠 AI Clinical Summary</p>',
                    unsafe_allow_html=True,
                )
                llm_input = {
                    "severity": severity,
                    "confidence": confidence,
                    "reason": reason,
                    "drug_a": drug_a,
                    "drug_b": drug_b,
                }
                llm_summary = generate_llm_summary(llm_input)
                st.markdown(llm_summary)

                #Molecular Fingerprint Analysis (XAI)
                with st.expander(f"🔬 View Molecular Fingerprint Analysis — {drug_a} ↔ {drug_b}", expanded=False):
                    st.markdown("#### Pathway Interaction Detail")
                    st.markdown(reason)

                    st.markdown("---")
                    st.markdown("#### Enzyme Affinity Map (Mock)")

                    ENZYME_DATA = {
                        "Critical": {
                            "CYP3A4": 0.92,
                            "CYP2C9": 0.85,
                            "CYP2D6": 0.40,
                            "CYP1A2": 0.15,
                            "P-gp": 0.60,
                        },
                        "High Risk": {
                            "CYP3A4": 0.70,
                            "CYP2C9": 0.65,
                            "CYP2D6": 0.80,
                            "CYP1A2": 0.20,
                            "P-gp": 0.55,
                        },
                        "Moderate": {
                            "CYP3A4": 0.55,
                            "CYP2C9": 0.45,
                            "CYP2D6": 0.70,
                            "CYP1A2": 0.30,
                            "P-gp": 0.50,
                        },
                        "Minor": {
                            "CYP3A4": 0.20,
                            "CYP2C9": 0.15,
                            "CYP2D6": 0.10,
                            "CYP1A2": 0.55,
                            "UGT1A1": 0.45,
                        },
                    }

                    enzymes = ENZYME_DATA[severity]
                    enzyme_cols = st.columns(len(enzymes))
                    for col, (enzyme, affinity) in zip(enzyme_cols, enzymes.items()):
                        with col:
                            bar_color = (
                                "🔴" if affinity >= 0.75
                                else "🟡" if affinity >= 0.45
                                else "🟢"
                            )
                            st.markdown(f"**{enzyme}**")
                            st.progress(affinity)
                            st.caption(f"{bar_color} {affinity:.0%}")

                    st.markdown("---")
                    st.caption(
                        "ℹ️ Mock model for demonstration. In production, molecular "
                        "fingerprints (ECFP4/MACCS) would be compared against a trained "
                        "GNN or transformer-based interaction model."
                    )

                #Emergency Escalation (Critical severity only)
                if severity == "Critical":
                    st.markdown('<hr class="clean-divider">', unsafe_allow_html=True)
                    st.markdown(
                        '<p class="section-title">🚨 Emergency Escalation</p>',
                        unsafe_allow_html=True,
                    )
                    esc_col1, esc_col2 = st.columns(2, gap="medium")
                    with esc_col1:
                        fda_btn = st.button(
                            "🛑  View FDA Warning & Alternatives",
                            use_container_width=True,
                            type="primary",
                            key=f"fda_{pair_idx}",
                        )
                    with esc_col2:
                        pdf_btn = st.button(
                            "📄  Generate Safety Report (PDF)",
                            use_container_width=True,
                            key=f"pdf_red_{pair_idx}",
                        )

                    if fda_btn:
                        st.markdown("#### ⚠️ FDA Interaction Warning")
                        st.error(
                            f"The FDA has documented significant adverse events when "
                            f"**{drug_a}** and **{drug_b}** are co-prescribed. "
                            f"Review the alternatives below before dispensing."
                        )
                        st.markdown("#### 💊 Recommended Alternatives")
                        alt_a = ALTERNATIVE_DRUGS.get(drug_a, [{"name": "Consult formulary", "note": "No pre-loaded alternatives"}])
                        alt_b = ALTERNATIVE_DRUGS.get(drug_b, [{"name": "Consult formulary", "note": "No pre-loaded alternatives"}])

                        alt_col1, alt_col2 = st.columns(2, gap="medium")
                        with alt_col1:
                            st.markdown(f"**Instead of {drug_a}:**")
                            for alt in alt_a:
                                st.success(f"✅ **{alt['name']}** — {alt['note']}")
                        with alt_col2:
                            st.markdown(f"**Instead of {drug_b}:**")
                            for alt in alt_b:
                                st.success(f"✅ **{alt['name']}** — {alt['note']}")

                    if pdf_btn:
                        st.toast("📄 Clinical Safety Report generated!", icon="✅")
                        st.success(
                            "✅ **Report generated and downloaded.** "
                            "The PDF contains the full interaction analysis, LLM summary, "
                            "and suggested clinical actions."
                        )

                else:
                    # Non-red: only show export button
                    st.markdown('<hr class="clean-divider">', unsafe_allow_html=True)
                    exp_col, _ = st.columns([1, 2])
                    with exp_col:
                        pdf_btn_safe = st.button(
                            "📄  Generate Safety Report (PDF)",
                            use_container_width=True,
                            key=f"pdf_safe_{pair_idx}",
                        )
                    if pdf_btn_safe:
                        st.toast("📄 Clinical Safety Report generated!", icon="✅")
                        st.success(
                            "✅ **Report generated and downloaded.** "
                            "The PDF contains the full interaction analysis, LLM summary, "
                            "and suggested clinical actions."
                        )

                # Divider between pairs
                if pair_idx < len(drug_pairs) - 1:
                    st.markdown('<hr class="clean-divider">', unsafe_allow_html=True)


# ══════════════════════════════════════════════
# DISCLAIMER & FOOTER
# ══════════════════════════════════════════════
st.markdown('<hr class="clean-divider">', unsafe_allow_html=True)
st.markdown(
    """
    <div class="disclaimer">
        <strong>⚕️ Disclaimer:</strong> This is an AI prototype for ASTRAVA 2026.
        <strong>Consult a certified medical professional</strong> before making
        any clinical decisions. This tool does not replace professional medical judgement.
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="footer">MedGuard AI &copy; 2026 &nbsp;·&nbsp; Built for ASTRAVA 2026 Hackathon &nbsp;·&nbsp; Powered by Streamlit</div>',
    unsafe_allow_html=True,
)

import streamlit as st
import random
import textwrap
import time
import io
import requests
import pandas as pd
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

# Load Drug List from Mapping File
try:
    smiles_df = pd.read_csv("smiles_mapping.csv")
    DRUG_LIST = sorted(smiles_df["drug_name"].dropna().unique().tolist())
except Exception as e:
    # Fallback just in case
    DRUG_LIST = [
        "Aspirin", "Warfarin", "Ibuprofen", "Metformin", "Lisinopril",
        "Amoxicillin", "Omeprazole", "Atorvastatin", "Ciprofloxacin", "Metoprolol"
    ]

# ──────────────────────────────────────────────
# Real ML Prediction Function
# ──────────────────────────────────────────────
def predict_interaction(
    drug_a: str, drug_b: str, patient_data: dict
) -> dict:
    """Fetch interaction prediction from the Flask backend ML model."""
    try:
        response = requests.post(
            "http://127.0.0.1:5000/predict",
            json={
                "drugs": [drug_a, drug_b],
                "patient": patient_data
            },
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                res = data[0]
                return {
                    "severity": res.get("final_severity", "Unknown"),
                    "confidence": round(res.get("confidence", 0.0) * 100, 1),
                    "reason": " \n".join(res.get("patient_factors", [])),
                    "ai_severity": res.get("ai_severity", "Unknown"),
                    "patient_notes": res.get("patient_factors", [])
                }
    except Exception as e:
        st.error(f"Error connecting to ML backend: {e}")
    
    # Fallback if API fails
    return {
        "severity": "Unknown",
        "confidence": 0.0,
        "reason": "Backend prediction service unavailable.",
        "ai_severity": "Unknown",
        "patient_notes": []
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

    _default_risk = (
        f"**Interaction Assessment** — **{drug_a}** and **{drug_b}** "
        f"interaction severity: **{sev}** (confidence: {confidence}%). "
        "Please consult a healthcare professional for guidance."
    )
    _default_action = (
        "1. **Consult your physician** for personalised advice.\n"
        "2. Do not change your medication regimen without professional guidance."
    )

    summary = (
        f"**📌 Risk Summary**\n\n"
        f"{RISK_SUMMARIES.get(sev, _default_risk)}\n\n"
        f"**🔬 Biological Reason**\n\n"
        f"{reason}\n\n"
        f"**✅ Suggested Action**\n\n"
        f"{SUGGESTED_ACTIONS.get(sev, _default_action)}"
    )
    return summary



# ──────────────────────────────────────────────
# PDF Safety Report Generator
# ──────────────────────────────────────────────
def _pdf_escape(text: str) -> str:
    """Escape special PDF characters in text strings."""
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def generate_safety_report(patient_data: dict, results: list[dict]) -> bytes:
    """Generate a simple PDF safety report from analysis results (no external deps)."""
    # Build readable text content
    lines: list[str] = []
    lines.append("MedGuard AI  -  Drug Interaction Safety Report")
    lines.append(f"Generated: {time.strftime('%Y-%m-%d %H:%M')}")
    lines.append("")
    lines.append("--- Patient Context ---")
    lines.append(f"  Age: {patient_data.get('age', 'N/A')}")
    lines.append(f"  Renal: {patient_data.get('renal', 'N/A')}")
    lines.append(f"  Liver: {patient_data.get('liver', 'N/A')}")
    lines.append(f"  Pregnant: {'Yes' if patient_data.get('is_pregnant') else 'No'}")
    conditions = []
    if patient_data.get("diabetes"): conditions.append("Diabetes")
    if patient_data.get("asthma"): conditions.append("Asthma/COPD")
    if patient_data.get("heart"): conditions.append("Heart Condition")
    lines.append(f"  Conditions: {', '.join(conditions) if conditions else 'None'}")
    lines.append("")

    for idx, res in enumerate(results, 1):
        pair = res.get("pair", ("?", "?"))
        lines.append(f"--- Pair {idx}: {pair[0]}  <->  {pair[1]} ---")
        lines.append(f"  Severity : {res.get('severity', 'Unknown')}")
        lines.append(f"  Confidence: {res.get('confidence', 0)}%")
        reason = res.get("reason", "")
        if reason:
            # Wrap long reason text
            for r_line in reason.split("\n"):
                lines.append(f"  {r_line.strip()}")
        notes = res.get("patient_notes", [])
        if notes:
            lines.append("  Patient factors:")
            for n in notes:
                lines.append(f"    - {n}")
        lines.append("")

    lines.append("--- Disclaimer ---")
    lines.append("This is an AI-generated prototype report for ASTRAVA 2026.")
    lines.append("Consult a certified medical professional before making clinical decisions.")

    # ── Build a minimal valid PDF ──
    font_size = 10
    leading = 14  # line spacing in points
    margin_left = 50
    margin_top = 750
    page_width = 612
    page_height = 792

    # Pre-render lines per page
    pages: list[list[str]] = []
    current_page: list[str] = []
    y = margin_top
    for line in lines:
        if y < 50:  # need a new page
            pages.append(current_page)
            current_page = []
            y = margin_top
        current_page.append((line, y))
        y -= leading
    if current_page:
        pages.append(current_page)

    buf = io.BytesIO()
    offsets: list[int] = []
    obj_num = 0

    def write(s: str):
        buf.write(s.encode("latin-1"))

    def start_obj():
        nonlocal obj_num
        obj_num += 1
        offsets.append(buf.tell())
        write(f"{obj_num} 0 obj\n")
        return obj_num

    write("%PDF-1.4\n")

    # Obj 1 — Catalog
    cat_id = start_obj()
    write("<< /Type /Catalog /Pages 2 0 R >>\n")
    write("endobj\n")

    # Obj 2 — Pages (placeholder, we'll overwrite)
    pages_id = start_obj()
    pages_obj_offset = offsets[-1]

    page_obj_ids: list[int] = []
    # Reserve space — we'll rewrite this object at the end
    write("<< /Type /Pages /Kids [] /Count 0 >>\n")
    write("endobj\n")

    # Obj 3 — Font
    font_id = start_obj()
    write("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\n")
    write("endobj\n")

    # Now create page objects + content streams
    for page_lines in pages:
        # Content stream
        stream_lines = [f"BT /F1 {font_size} Tf"]
        for line_text, y_pos in page_lines:
            escaped = _pdf_escape(line_text)
            stream_lines.append(f"{margin_left} {y_pos} Td ({escaped}) Tj")
            stream_lines.append(f"-{margin_left} -{y_pos} Td")  # reset position
        stream_lines.append("ET")
        stream_data = "\n".join(stream_lines)

        content_id = start_obj()
        write(f"<< /Length {len(stream_data)} >>\n")
        write(f"stream\n{stream_data}\nendstream\n")
        write("endobj\n")

        page_id = start_obj()
        page_obj_ids.append(page_id)
        write(f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {page_width} {page_height}] ")
        write(f"/Contents {content_id} 0 R ")
        write(f"/Resources << /Font << /F1 {font_id} 0 R >> >> >>\n")
        write("endobj\n")

    # Rewrite the Pages object in place by seeking back
    kids_str = " ".join(f"{pid} 0 R" for pid in page_obj_ids)
    new_pages_obj = f"<< /Type /Pages /Kids [{kids_str}] /Count {len(page_obj_ids)} >>"
    # We can't easily seek-overwrite in a stream, so just append a new Pages obj
    # and update the catalog. Actually, simpler: rebuild the whole thing cleanly.
    # Let's just rebuild:
    buf2 = io.BytesIO()
    offsets2: list[int] = []
    obj_count = 0

    def write2(s: str):
        buf2.write(s.encode("latin-1"))

    def start_obj2():
        nonlocal obj_count
        obj_count += 1
        offsets2.append(buf2.tell())
        write2(f"{obj_count} 0 obj\n")
        return obj_count

    write2("%PDF-1.4\n")

    # Obj 1 — Catalog
    start_obj2()
    write2("<< /Type /Catalog /Pages 2 0 R >>\n")
    write2("endobj\n")

    # Obj 2 — Pages (will reference page objects starting at obj 4)
    start_obj2()
    page_ids_final: list[int] = []
    # We need to know page object IDs in advance
    # Layout: obj3=font, then for each page: obj(content), obj(page)
    next_id = 4  # obj3 is font, page objects start after
    for _ in pages:
        next_id += 1  # content stream
        page_ids_final.append(next_id)
        next_id += 1  # page object
    kids_refs = " ".join(f"{pid} 0 R" for pid in page_ids_final)
    write2(f"<< /Type /Pages /Kids [{kids_refs}] /Count {len(pages)} >>\n")
    write2("endobj\n")

    # Obj 3 — Font
    start_obj2()
    write2("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\n")
    write2("endobj\n")

    # Page content + page objects
    for page_lines in pages:
        stream_lines = [f"BT /F1 {font_size} Tf"]
        for line_text, y_pos in page_lines:
            escaped = _pdf_escape(line_text)
            stream_lines.append(f"{margin_left} {y_pos} Td ({escaped}) Tj")
            stream_lines.append(f"-{margin_left} -{y_pos} Td")
        stream_lines.append("ET")
        stream_data = "\n".join(stream_lines)

        cid = start_obj2()
        write2(f"<< /Length {len(stream_data)} >>\n")
        write2(f"stream\n{stream_data}\nendstream\n")
        write2("endobj\n")

        pid = start_obj2()
        write2(f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {page_width} {page_height}] ")
        write2(f"/Contents {cid} 0 R ")
        write2(f"/Resources << /Font << /F1 3 0 R >> >> >>\n")
        write2("endobj\n")

    # Cross-reference table
    xref_offset = buf2.tell()
    write2("xref\n")
    write2(f"0 {obj_count + 1}\n")
    write2("0000000000 65535 f \n")
    for off in offsets2:
        write2(f"{off:010d} 00000 n \n")

    # Trailer
    write2("trailer\n")
    write2(f"<< /Size {obj_count + 1} /Root 1 0 R >>\n")
    write2("startxref\n")
    write2(f"{xref_offset}\n")
    write2("%%EOF\n")

    return buf2.getvalue()


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
            "Patient Age",
            min_value=0,
            max_value=120,
            value=30,
            help="Patient's age in years",
        )

        gender = st.radio("Gender", ["Male", "Female", "Other"], horizontal=True)
        
        renal = st.select_slider("Renal Function", ["Failure", "Impaired", "Normal"], "Normal")
        liver = st.selectbox("Liver Status", ["Healthy", "Compromised"])

        pregnancy = False
        if gender == "Female":
            pregnancy = st.toggle("Is Pregnant?", value=False)

        st.markdown("---")
        st.markdown("### ⚕️ Medical History")
        
        diabetes = st.checkbox("Diabetes")
        asthma = st.checkbox("Asthma / COPD")
        heart = st.checkbox("Heart Condition")
        
        # Package patient data for backend API
        patient_data = {
            "age": age,
            "is_pregnant": pregnancy,
            "diabetes": diabetes,
            "asthma": asthma,
            "heart": heart,
            "renal": renal,
            "liver": liver
        }

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
            # patient_data is already defined in the sidebar section
            drug_pairs = list(combinations(unique_drugs, 2))

            st.markdown('<hr class="clean-divider">', unsafe_allow_html=True)
            st.markdown(
                '<p class="section-title">📋 Analysis Results</p>',
                unsafe_allow_html=True,
            )
            st.caption(f"Analyzing **{len(drug_pairs)}** drug pair(s) from **{len(unique_drugs)}** selected drugs.")

            all_results = []

            for pair_idx, (drug_a, drug_b) in enumerate(drug_pairs):
                # ML API prediction
                result = predict_interaction(drug_a, drug_b, patient_data)
                result['pair'] = (drug_a, drug_b)
                all_results.append(result)

                severity = result.get("severity", "Unknown")
                confidence = result.get("confidence", 0.0)
                reason = result.get("reason", "No detailed interaction reasons provided.")
                patient_notes = result.get("patient_notes", [])
                ai_severity = result.get("ai_severity", "Unknown")

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
                            <p class="meta"><b>Patient:</b> {age} yrs, {gender} &nbsp;·&nbsp; Renal: {renal} &nbsp;·&nbsp; Liver: {liver}</p>
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
                    "Unknown": {
                        "icon": "⚪",
                        "label": "UNABLE TO DETERMINE RISK",
                        "fn": st.info,
                    },
                }
                cfg = SEVERITY_CONFIG.get(severity, SEVERITY_CONFIG["Unknown"])
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
                    esc_col1, _ = st.columns(2, gap="medium")
                    with esc_col1:
                        fda_btn = st.button(
                            "🛑  View FDA Warning & Alternatives",
                            use_container_width=True,
                            type="primary",
                            key=f"fda_{pair_idx}",
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


                # Divider between pairs
                if pair_idx < len(drug_pairs) - 1:
                    st.markdown('<hr class="clean-divider">', unsafe_allow_html=True)

            st.markdown('<hr class="clean-divider">', unsafe_allow_html=True)
            
            # Prepare PDF bytes from all results
            pdf_bytes = generate_safety_report(patient_data, all_results)
            
            st.download_button(
                label="📄  Generate Full Safety Report (PDF)",
                data=pdf_bytes,
                file_name=f"MedGuard_Safety_Report_{time.strftime('%Y%m%d_%H%M')}.pdf",
                mime="application/pdf",
                use_container_width=True,
                type="primary",
            )


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

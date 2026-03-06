"""
MedGuard AI — Agentic Medical Guidance Chatbot
════════════════════════════════════════════════════════════════
Agentic Architecture:
  1. Tool Registry       — callable functions the agent can invoke
  2. Entity Extraction   — fuzzy drug-name matching via difflib
  3. Agentic Planner     — multi-step reasoning loop that chains tools
  4. Conversation Memory  — tracks context across turns for follow-ups
  5. Response Generation  — natural, dynamic responses with reasoning traces

Usage:  from chatbot import render_chatbot; render_chatbot()
"""

import os
import re
import string
import difflib
import time
from collections import Counter
from itertools import combinations as _combinations
from dataclasses import dataclass, field
from typing import Any

import pandas as pd
import streamlit as st


# ══════════════════════════════════════════════
# DATA LAYER
# ══════════════════════════════════════════════

@st.cache_data(show_spinner=False)
def _load_dataset() -> pd.DataFrame:
    base = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(base, "data", "db_drug_interactions.csv")
    df = pd.read_csv(csv_path)
    df.columns = df.columns.str.strip()
    df["Drug 1"] = df["Drug 1"].str.strip()
    df["Drug 2"] = df["Drug 2"].str.strip()
    df["drug1_lower"] = df["Drug 1"].str.lower()
    df["drug2_lower"] = df["Drug 2"].str.lower()
    return df


@st.cache_data(show_spinner=False)
def _get_drug_names(df: pd.DataFrame) -> list[str]:
    names = set(df["Drug 1"].tolist() + df["Drug 2"].tolist())
    return sorted(names)


@st.cache_data(show_spinner=False)
def _get_drug_names_lower(drug_names: tuple[str, ...]) -> list[str]:
    return [d.lower() for d in drug_names]


_DF = _load_dataset()
_DRUG_NAMES = _get_drug_names(_DF)
_DRUG_NAMES_LOWER = _get_drug_names_lower(tuple(_DRUG_NAMES))
_LOWER_TO_ORIG: dict[str, str] = {d.lower(): d for d in _DRUG_NAMES}


# ══════════════════════════════════════════════
# TOOL DEFINITIONS  (the agent's capabilities)
# ══════════════════════════════════════════════

@dataclass
class ToolResult:
    """Standardised output from every tool call."""
    tool_name: str
    success: bool
    data: Any = None
    summary: str = ""


def tool_check_interaction(drug_a: str, drug_b: str) -> ToolResult:
    """Look up known interactions between two specific drugs."""
    a, b = drug_a.lower(), drug_b.lower()
    mask = (
        ((_DF["drug1_lower"] == a) & (_DF["drug2_lower"] == b))
        | ((_DF["drug1_lower"] == b) & (_DF["drug2_lower"] == a))
    )
    descriptions = _DF.loc[mask, "Interaction Description"].tolist()
    if descriptions:
        return ToolResult(
            tool_name="check_interaction",
            success=True,
            data={"drug_a": drug_a, "drug_b": drug_b, "descriptions": descriptions[:5]},
            summary=f"Found {len(descriptions)} interaction(s) between {drug_a} and {drug_b}.",
        )
    return ToolResult(
        tool_name="check_interaction",
        success=True,
        data={"drug_a": drug_a, "drug_b": drug_b, "descriptions": []},
        summary=f"No known interaction between {drug_a} and {drug_b}.",
    )


def tool_get_drug_info(drug: str, limit: int = 10) -> ToolResult:
    """Retrieve all known interactions for a single drug."""
    d = drug.lower()
    mask = (_DF["drug1_lower"] == d) | (_DF["drug2_lower"] == d)
    rows = _DF.loc[mask].head(limit)
    total = int(mask.sum())
    if rows.empty:
        return ToolResult(
            tool_name="get_drug_info",
            success=True,
            data={"drug": drug, "total": 0, "interactions": []},
            summary=f"No interactions found for {drug}.",
        )
    interactions = []
    for _, row in rows.iterrows():
        other = row["Drug 2"] if row["Drug 1"].lower() == d else row["Drug 1"]
        interactions.append({
            "partner": other,
            "description": row["Interaction Description"],
            "severity": _classify_severity(row["Interaction Description"]),
        })
    return ToolResult(
        tool_name="get_drug_info",
        success=True,
        data={"drug": drug, "total": total, "interactions": interactions},
        summary=f"Found {total} interaction(s) for {drug}. Showing top {len(interactions)}.",
    )


def _classify_severity(description: str) -> str:
    """Classify severity from an interaction description string."""
    desc = description.lower()
    if any(kw in desc for kw in ("toxicity", "fatal", "dangerous", "serious", "critical")):
        return "🔴 Critical"
    if any(kw in desc for kw in ("increase the risk", "increased when", "adverse effect", "bleeding", "cardiotoxic")):
        return "🟠 High Risk"
    if any(kw in desc for kw in ("moderate", "caution", "monitor")):
        return "🟡 Moderate"
    if any(kw in desc for kw in ("decrease", "reduced", "minimal", "mild", "safe")):
        return "🟢 Minor"
    return "⚪ Unknown"


def tool_assess_severity(drug_a: str, drug_b: str) -> ToolResult:
    """Assess the risk/severity level of combining two drugs."""
    a, b = drug_a.lower(), drug_b.lower()
    mask = (
        ((_DF["drug1_lower"] == a) & (_DF["drug2_lower"] == b))
        | ((_DF["drug1_lower"] == b) & (_DF["drug2_lower"] == a))
    )
    descriptions = _DF.loc[mask, "Interaction Description"].tolist()
    if not descriptions:
        return ToolResult(
            tool_name="assess_severity",
            success=True,
            data={"drug_a": drug_a, "drug_b": drug_b, "severity": "⚪ No Data", "description": None},
            summary=f"No interaction data found for {drug_a} + {drug_b}.",
        )
    severity = _classify_severity(descriptions[0])
    return ToolResult(
        tool_name="assess_severity",
        success=True,
        data={
            "drug_a": drug_a, "drug_b": drug_b,
            "severity": severity,
            "description": descriptions[0],
        },
        summary=f"{drug_a} + {drug_b} → {severity}.",
    )


def tool_find_alternatives(drug: str) -> ToolResult:
    """Suggest drugs with milder known interactions as alternatives."""
    d_lower = drug.lower()
    all_partners = set(
        _DF.loc[_DF["drug1_lower"] == d_lower, "Drug 2"].tolist()
        + _DF.loc[_DF["drug2_lower"] == d_lower, "Drug 1"].tolist()
    )
    if not all_partners:
        return ToolResult(
            tool_name="find_alternatives",
            success=True,
            data={"drug": drug, "alternatives": []},
            summary=f"No interaction data for {drug} to derive alternatives.",
        )
    mild: list[dict] = []
    for partner in all_partners:
        descs = _DF.loc[
            ((_DF["drug1_lower"] == d_lower) & (_DF["drug2_lower"] == partner.lower()))
            | ((_DF["drug1_lower"] == partner.lower()) & (_DF["drug2_lower"] == d_lower)),
            "Interaction Description"
        ].tolist()
        if descs:
            sev = _classify_severity(descs[0])
            if "Minor" in sev or "decrease" in descs[0].lower():
                mild.append({"name": partner, "severity": sev, "reason": descs[0][:120]})
        if len(mild) >= 5:
            break
    if not mild:
        for partner in list(all_partners)[:5]:
            descs = _DF.loc[
                ((_DF["drug1_lower"] == d_lower) & (_DF["drug2_lower"] == partner.lower()))
                | ((_DF["drug1_lower"] == partner.lower()) & (_DF["drug2_lower"] == d_lower)),
                "Interaction Description"
            ].tolist()
            desc_text = descs[0] if descs else "No description"
            mild.append({"name": partner, "severity": _classify_severity(desc_text), "reason": desc_text[:120]})
    return ToolResult(
        tool_name="find_alternatives",
        success=True,
        data={"drug": drug, "alternatives": mild[:5]},
        summary=f"Found {len(mild[:5])} potential alternative(s) to explore instead of {drug}.",
    )


def tool_search_drugs(query: str) -> ToolResult:
    """Fuzzy-search the drug database for matching names."""
    query_lower = query.lower()
    # exact substring matches
    exact = [name for name in _DRUG_NAMES if query_lower in name.lower()][:10]
    # fuzzy matches
    fuzzy = difflib.get_close_matches(query_lower, _DRUG_NAMES_LOWER, n=5, cutoff=0.65)
    fuzzy_orig = [_LOWER_TO_ORIG[m] for m in fuzzy if _LOWER_TO_ORIG[m] not in exact]
    results = exact + fuzzy_orig
    return ToolResult(
        tool_name="search_drugs",
        success=True,
        data={"query": query, "matches": results[:10]},
        summary=f"Found {len(results[:10])} drug(s) matching '{query}'.",
    )


# ── Tool Registry ──
TOOL_REGISTRY: dict[str, dict] = {
    "check_interaction": {
        "fn": tool_check_interaction,
        "description": "Look up interactions between two drugs",
        "params": ["drug_a", "drug_b"],
    },
    "get_drug_info": {
        "fn": tool_get_drug_info,
        "description": "Get all known interactions for a single drug",
        "params": ["drug"],
    },
    "assess_severity": {
        "fn": tool_assess_severity,
        "description": "Assess the danger/risk level of combining two drugs",
        "params": ["drug_a", "drug_b"],
    },
    "find_alternatives": {
        "fn": tool_find_alternatives,
        "description": "Suggest safer alternatives for a drug",
        "params": ["drug"],
    },
    "search_drugs": {
        "fn": tool_search_drugs,
        "description": "Fuzzy-search the drug database by name",
        "params": ["query"],
    },
}


# ══════════════════════════════════════════════
# NLP — Entity Extraction
# ══════════════════════════════════════════════

_STOPWORDS: set[str] = {
    "i", "me", "my", "we", "our", "you", "your", "he", "she", "it",
    "they", "them", "a", "an", "the", "is", "am", "are", "was", "were",
    "be", "been", "being", "have", "has", "had", "do", "does", "did",
    "will", "would", "shall", "should", "may", "might", "can", "could",
    "to", "of", "in", "for", "on", "with", "at", "by", "from", "as",
    "into", "through", "during", "before", "after", "above", "below",
    "between", "out", "off", "over", "under", "again", "further", "then",
    "once", "here", "there", "when", "where", "why", "how", "all", "each",
    "every", "both", "few", "more", "most", "other", "some", "such", "no",
    "not", "only", "own", "same", "than", "too", "very", "just", "because",
    "but", "and", "or", "if", "while", "about", "up", "so", "that", "this",
    "these", "those", "what", "which", "who", "whom",
}


def _preprocess(text: str) -> list[str]:
    text = text.lower()
    text = text.translate(str.maketrans("", "", string.punctuation))
    tokens = text.split()
    return [t for t in tokens if t not in _STOPWORDS]


_COMMON_WORDS: set[str] = _STOPWORDS | {
    "take", "taking", "took", "tell", "know", "check", "find", "get",
    "give", "use", "using", "happens", "happen", "dangerous", "safe",
    "drug", "drugs", "medicine", "medicines", "medication", "medications",
    "interact", "interaction", "interactions", "alternative", "alternatives",
    "instead", "substitute", "replace", "combine", "combined", "mix",
    "doctor", "patient", "risk", "severe", "severity", "info", "information",
    "hello", "help", "thanks", "please", "need", "want", "like",
    "yes", "no", "ok", "okay", "sure", "right",
}


def _extract_drugs(tokens: list[str], raw_text: str) -> tuple[list[str], list[str]]:
    """
    Extract drug names using exact substring match + fuzzy matching.
    Returns: (recognized_drugs, unrecognized_potential_drugs)
    """
    found: set[str] = set()
    raw_lower = raw_text.lower()

    # exact substring/word match
    for name_lower, name_orig in _LOWER_TO_ORIG.items():
        pattern = r'\b' + re.escape(name_lower) + r'\b'
        if re.search(pattern, raw_lower):
            found.add(name_orig)

    # fuzzy match individual tokens (tighter cutoff to avoid false positives)
    for tok in tokens:
        if len(tok) < 4:
            continue
        matches = difflib.get_close_matches(tok, _DRUG_NAMES_LOWER, n=1, cutoff=0.82)
        if matches:
            found.add(_LOWER_TO_ORIG[matches[0]])

    # Detect potential drug names NOT in the database
    unrecognized: list[str] = []
    
    # 1. Capitalized words that might be missing
    words = re.findall(r'\b[A-Z][a-z]{3,}\b', raw_text)
    
    # 2. Also consider lowercase tokens that are long enough
    for tok in tokens:
        if len(tok) >= 5 and tok not in _COMMON_WORDS:
            words.append(tok)
            
    # Deduplicate
    seen = set()
    unique_words = []
    for w in words:
        wl = w.lower()
        if wl not in seen:
            seen.add(wl)
            unique_words.append(w)

    for word in unique_words:
        w_lower = word.lower()
        if w_lower not in _COMMON_WORDS and not any(w_lower in f.lower() for f in found):
            # Check it's not a close match to a database drug (using the same 0.82 cutoff)
            close = difflib.get_close_matches(w_lower, _DRUG_NAMES_LOWER, n=1, cutoff=0.82)
            if not close:
                unrecognized.append(word.capitalize())

    return sorted(found), unrecognized


# ══════════════════════════════════════════════
# AGENTIC PLANNER  (the brain)
# ══════════════════════════════════════════════

@dataclass
class AgentStep:
    """One step in the agent's reasoning chain."""
    thought: str
    tool_name: str | None = None
    tool_args: dict = field(default_factory=dict)
    result: ToolResult | None = None


@dataclass
class AgentPlan:
    """The full plan the agent builds and executes."""
    steps: list[AgentStep] = field(default_factory=list)
    final_answer: str = ""


# ── Intent signals (used by the planner to decide which tools to call) ──
_INTENT_SIGNALS: dict[str, list[str]] = {
    "interaction_check": [
        "interact", "interaction", "combine", "combined", "mix",
        "take.*with", "together", "happen", "clash", "conflict",
        "co-administer", "coadminister", "concomitant",
    ],
    "drug_info": [
        "tell me about", "info", "information", "details",
        "what is", "what are", "know about", "describe",
        "interactions of", "interactions for", "lookup", "look up",
    ],
    "severity_check": [
        "dangerous", "danger", "severe", "severity", "serious",
        "safe", "safety", "risky", "risk", "fatal", "harmful", "toxic",
    ],
    "alternative_suggestion": [
        "alternative", "instead", "substitute", "replace",
        "replacement", "swap", "switch", "other option",
    ],
    "greeting": [
        "hello", "hi", "hey", "good morning", "good afternoon",
        "good evening", "greetings", "howdy", "sup", "whats up",
    ],
    "thanks": [
        "thank", "thanks", "thx", "appreciate", "grateful",
    ],
    "help": [
        "help", "how do i use", "what can you do", "commands",
        "guide", "tutorial", "instructions",
    ],
}


def _detect_intents(tokens: list[str], raw_text: str) -> list[str]:
    """Return ALL matching intents, ranked by score (multi-intent support)."""
    raw_lower = raw_text.lower()
    scores: Counter = Counter()
    for intent, patterns in _INTENT_SIGNALS.items():
        for pat in patterns:
            if " " in pat or ".*" in pat:
                if re.search(pat, raw_lower):
                    scores[intent] += 2
            else:
                if pat in tokens:
                    scores[intent] += 1
    return [intent for intent, _ in scores.most_common()] if scores else []


def _resolve_drugs_with_memory(drugs: list[str], memory: list[dict], intents: list[str]) -> list[str]:
    """If no drugs found, or if an intent requires 2 drugs but only 1 is found, pull from memory."""
    resolved = list(drugs)
    needs_two = any(i in ("interaction_check", "severity_check") for i in intents)

    if not resolved:
        # Check recent messages for drug entities
        for msg in reversed(memory[-6:]):
            if msg.get("drugs"):
                return msg["drugs"]
        return []

    if len(resolved) == 1 and needs_two:
        # We need a pair, but only have one. Pull the other from memory.
        for msg in reversed(memory[-6:]):
            if msg.get("drugs"):
                for d in msg["drugs"]:
                    if d.lower() != resolved[0].lower():
                        resolved.append(d)
                        return resolved

    return resolved


def _build_plan(intents: list[str], drugs: list[str], raw_text: str, memory: list[dict],
                unrecognized: list[str] | None = None) -> AgentPlan:
    """
    Build an execution plan: decide which tools to call and in what order.
    This is the 'reasoning' core of the agent.
    """
    plan = AgentPlan()
    unrecognized = unrecognized or []

    # ── Handle non-tool intents first ──
    if not intents or (len(intents) == 1 and intents[0] in ("greeting", "thanks", "help")):
        if "greeting" in intents:
            plan.steps.append(AgentStep(thought="User is greeting me. I'll respond warmly and explain my capabilities."))
            plan.final_answer = _make_greeting()
            return plan
        if "thanks" in intents:
            plan.steps.append(AgentStep(thought="User is expressing gratitude. I'll acknowledge kindly."))
            plan.final_answer = "You're welcome! 😊 Feel free to ask me anything else about drug interactions. I'm here to help!"
            return plan
        if "help" in intents:
            plan.steps.append(AgentStep(thought="User needs help. I'll explain what I can do and show examples."))
            plan.final_answer = _make_help()
            return plan

    # ── Note unrecognized potential drug names ──
    if unrecognized:
        plan.steps.append(AgentStep(
            thought=f"Detected potential drug name(s) not in my database: **{', '.join(unrecognized)}**. I'll note this for the user.",
        ))

    # ── Resolve drugs using memory if needed ──
    resolved_drugs = _resolve_drugs_with_memory(drugs, memory, intents)
    if not resolved_drugs and not intents:
        if unrecognized:
            plan.steps.append(AgentStep(thought="No recognized drugs found. I'll inform the user about unrecognized names."))
            plan.final_answer = _make_fallback_unrecognized(unrecognized)
        else:
            plan.steps.append(AgentStep(thought="I couldn't identify any drugs or clear intent. I'll ask the user to clarify."))
            plan.final_answer = _make_fallback_no_drugs()
        return plan

    # ── Build tool-call steps based on detected intents ──
    if not resolved_drugs and intents:
        if unrecognized:
            plan.steps.append(AgentStep(
                thought=f"Detected intent(s) but only unrecognized drug names. Informing user.",
            ))
            plan.final_answer = _make_fallback_unrecognized(unrecognized)
        else:
            plan.steps.append(AgentStep(
                thought=f"Detected intent(s): {', '.join(intents)}, but no drug names found. I'll ask the user to specify drugs.",
            ))
            plan.final_answer = _make_fallback_no_drugs()
        return plan

    used_memory = not drugs and bool(resolved_drugs)
    if used_memory:
        plan.steps.append(AgentStep(
            thought=f"No drugs in current message. Pulling from conversation memory: {', '.join(resolved_drugs)}.",
        ))

    plan.steps.append(AgentStep(
        thought=f"Identified drug(s): **{', '.join(resolved_drugs)}**. Detected intent(s): **{', '.join(intents) if intents else 'general query'}**.",
    ))

    # -- Map intents to tool calls --
    for intent in intents:
        if intent == "interaction_check" and len(resolved_drugs) >= 2:
            for a, b in _combinations(resolved_drugs, 2):
                plan.steps.append(AgentStep(
                    thought=f"Checking interaction between {a} and {b}.",
                    tool_name="check_interaction",
                    tool_args={"drug_a": a, "drug_b": b},
                ))
        elif intent == "drug_info":
            for drug in resolved_drugs[:2]:
                plan.steps.append(AgentStep(
                    thought=f"Retrieving interaction profile for {drug}.",
                    tool_name="get_drug_info",
                    tool_args={"drug": drug},
                ))
        elif intent == "severity_check" and len(resolved_drugs) >= 2:
            for a, b in _combinations(resolved_drugs, 2):
                plan.steps.append(AgentStep(
                    thought=f"Assessing severity/risk for {a} + {b}.",
                    tool_name="assess_severity",
                    tool_args={"drug_a": a, "drug_b": b},
                ))
        elif intent == "alternative_suggestion":
            for drug in resolved_drugs[:2]:
                plan.steps.append(AgentStep(
                    thought=f"Searching for safer alternatives to {drug}.",
                    tool_name="find_alternatives",
                    tool_args={"drug": drug},
                ))
        elif intent in ("greeting", "thanks", "help"):
            pass  # already handled above
        elif intent == "interaction_check" and len(resolved_drugs) == 1:
            plan.steps.append(AgentStep(
                thought=f"Only one drug detected for interaction check. Fetching general info for {resolved_drugs[0]}.",
                tool_name="get_drug_info",
                tool_args={"drug": resolved_drugs[0]},
            ))
        elif intent == "severity_check" and len(resolved_drugs) == 1:
            plan.steps.append(AgentStep(
                thought=f"Only one drug for severity check. Fetching general info for {resolved_drugs[0]}.",
                tool_name="get_drug_info",
                tool_args={"drug": resolved_drugs[0]},
            ))

    # ── Multi-step chaining: if severity is high, auto-suggest alternatives ──
    severity_intents = [i for i in intents if i in ("severity_check", "interaction_check")]
    alt_intents = [i for i in intents if i == "alternative_suggestion"]
    raw_lower = raw_text.lower()
    auto_chain_alt = (
        severity_intents
        and not alt_intents
        and any(kw in raw_lower for kw in ("if so", "also suggest", "and alternatives", "and suggest", "what else"))
    )
    if auto_chain_alt:
        for drug in resolved_drugs[:2]:
            plan.steps.append(AgentStep(
                thought=f"User also wants alternatives. Auto-chaining: finding alternatives for {drug}.",
                tool_name="find_alternatives",
                tool_args={"drug": drug},
            ))

    # If no tool steps were added (intents but all unhandled), do a general info lookup
    tool_steps = [s for s in plan.steps if s.tool_name]
    if not tool_steps:
        for drug in resolved_drugs[:2]:
            plan.steps.append(AgentStep(
                thought=f"No specific intent matched clearly. Defaulting to general info for {drug}.",
                tool_name="get_drug_info",
                tool_args={"drug": drug},
            ))

    return plan


def _execute_plan(plan: AgentPlan) -> AgentPlan:
    """Execute all tool calls in the plan and attach results."""
    for step in plan.steps:
        if step.tool_name and step.tool_name in TOOL_REGISTRY:
            tool_fn = TOOL_REGISTRY[step.tool_name]["fn"]
            step.result = tool_fn(**step.tool_args)
    return plan


# ══════════════════════════════════════════════
# RESPONSE GENERATION  (natural language from tool results)
# ══════════════════════════════════════════════

def _make_greeting() -> str:
    return (
        "👋 Hello! I'm the **MedGuard AI** agent — your intelligent drug interaction assistant.\n\n"
        "I can **reason through complex questions**, chain multiple lookups, and remember context "
        "from our conversation.\n\n"
        "Here's what I can help with:\n"
        "- 🔍 **Drug interactions** — *\"What happens if I take Aspirin with Warfarin?\"*\n"
        "- 📋 **Drug profiles** — *\"Tell me about Digoxin\"*\n"
        "- ⚠️ **Safety assessment** — *\"Is Metoprolol and Digoxin dangerous?\"*\n"
        "- 💊 **Alternatives** — *\"What can I take instead of Ibuprofen?\"*\n"
        "- 🔗 **Multi-step queries** — *\"Is Aspirin dangerous with Warfarin? If so, suggest alternatives\"*\n\n"
        "I also remember what we've been discussing, so feel free to ask follow-up questions! 👇"
    )


def _make_help() -> str:
    return (
        "### 🤖 MedGuard AI — Agent Capabilities\n\n"
        "I'm an **agentic AI** that reasons about your questions and uses specialised tools to find answers.\n\n"
        "#### 🔧 My Tools\n"
        "| Tool | What it does |\n"
        "|---|---|\n"
        "| `check_interaction` | Look up interactions between two drugs |\n"
        "| `get_drug_info` | Retrieve the interaction profile for a drug |\n"
        "| `assess_severity` | Assess the danger level of a drug combination |\n"
        "| `find_alternatives` | Suggest safer alternatives to a drug |\n"
        "| `search_drugs` | Fuzzy-search the drug database |\n\n"
        "#### 💡 Example Queries\n"
        "| Type | Example |\n"
        "|---|---|\n"
        "| Interaction check | *\"What happens if I take Aspirin with Warfarin?\"* |\n"
        "| Drug profile | *\"Tell me about Digoxin\"* |\n"
        "| Safety check | *\"Is Ciprofloxacin and Warfarin dangerous?\"* |\n"
        "| Alternatives | *\"What can I take instead of Ibuprofen?\"* |\n"
        "| Multi-step | *\"Is Aspirin dangerous with Warfarin? If so, suggest alternatives\"* |\n"
        "| Follow-up | *\"What about with Digoxin?\"* (I remember context!) |\n\n"
        f"📊 **Database:** {len(_DRUG_NAMES):,} drugs · {len(_DF):,} interaction records\n\n"
        "_Tip: I can handle minor typos in drug names!_ ✨"
    )


def _make_fallback_no_drugs() -> str:
    return (
        "I'm sorry, I didn't quite understand that. 🤔\n\n"
        "I need **drug names** to help you. Try asking:\n"
        "- *\"What happens if I take Aspirin with Warfarin?\"*\n"
        "- *\"Tell me about Digoxin\"*\n"
        "- *\"Is Ibuprofen safe with Metformin?\"*\n\n"
        "Type **help** to see all my capabilities."
    )


def _make_fallback_unrecognized(unrecognized: list[str]) -> str:
    names = ", ".join(f"**{n}**" for n in unrecognized)
    return (
        f"I noticed you mentioned {names}, but {'it is' if len(unrecognized) == 1 else 'they are'} "
        f"not in my database of {len(_DRUG_NAMES):,} drugs. 🤔\n\n"
        "This could mean:\n"
        "- The drug name is spelled differently in my database\n"
        "- The drug is not yet covered in my interaction dataset\n\n"
        "Try using the **generic name** or a different spelling. "
        "Type **help** to see example queries."
    )


def _format_tool_results(plan: AgentPlan) -> str:
    """Compose a natural-language response from all tool results."""
    parts: list[str] = []

    for step in plan.steps:
        if not step.result:
            continue

        result = step.result
        data = result.data

        if result.tool_name == "check_interaction":
            a, b = data["drug_a"], data["drug_b"]
            descs = data["descriptions"]
            parts.append(f"### 💊 {a}  ↔  {b}\n")
            if descs:
                severity = _classify_severity(descs[0])
                parts.append(f"**Risk Level:** {severity}\n")
                for desc in descs[:3]:
                    parts.append(f"- {desc}")
            else:
                parts.append("No known interaction found in the database.")
            parts.append("")

        elif result.tool_name == "get_drug_info":
            drug = data["drug"]
            total = data["total"]
            interactions = data["interactions"]
            parts.append(f"### 📋 {drug}")
            if not interactions:
                parts.append("No interactions found in the database.\n")
            else:
                parts.append(f"Found **{total}** known interactions. Here are the most notable:\n")
                for ixn in interactions:
                    parts.append(f"- **{ixn['partner']}** {ixn['severity']} — {ixn['description']}")
                if total > len(interactions):
                    parts.append(f"\n_…and {total - len(interactions)} more. Ask about a specific pair for details._")
            parts.append("")

        elif result.tool_name == "assess_severity":
            a, b = data["drug_a"], data["drug_b"]
            severity = data["severity"]
            desc = data["description"]
            parts.append(f"### ⚠️ Safety Assessment: {a}  ↔  {b}\n")
            parts.append(f"**Risk Level:** {severity}\n")
            advice = {
                "🔴 Critical": "⚠️ **This combination is potentially dangerous.** Consult your physician before co-administering.",
                "🟠 High Risk": "⚡ **High risk detected.** Use with caution and monitor for adverse effects.",
                "🟡 Moderate": "⚠️ **Moderate risk.** Use with caution and monitor for adverse effects.",
                "🟢 Minor": "✅ **Low risk.** Generally considered safe, but always inform your doctor.",
                "⚪ Unknown": "ℹ️ **Severity could not be determined automatically.** Consult a healthcare professional.",
                "⚪ No Data": "ℹ️ **No interaction data found.** This doesn't mean it's safe — consult your doctor.",
            }
            parts.append(advice.get(severity, ""))
            if desc:
                parts.append(f"\n**Detail:** {desc}")
            parts.append("")

        elif result.tool_name == "find_alternatives":
            drug = data["drug"]
            alternatives = data["alternatives"]
            parts.append(f"### 💊 Alternatives to **{drug}**\n")
            if not alternatives:
                parts.append("No alternative suggestions available from the database.")
            else:
                for alt in alternatives:
                    parts.append(f"- **{alt['name']}** {alt['severity']}")
                parts.append("\n> ⚕️ *These are drugs with milder known interactions. Always consult your doctor.*")
            parts.append("")

        elif result.tool_name == "search_drugs":
            query = data["query"]
            matches = data["matches"]
            parts.append(f"### 🔍 Search Results for \"{query}\"\n")
            if not matches:
                parts.append("No matching drugs found.")
            else:
                for m in matches:
                    parts.append(f"- {m}")
            parts.append("")

    return "\n".join(parts).strip()


def _generate_reasoning_trace(plan: AgentPlan) -> str:
    """Build a markdown trace of the agent's step-by-step reasoning."""
    lines: list[str] = []
    for i, step in enumerate(plan.steps, 1):
        icon = "🤔" if not step.tool_name else "🔧"
        lines.append(f"**Step {i}** {icon} {step.thought}")
        if step.tool_name:
            args_str = ", ".join(f"{k}=`{v}`" for k, v in step.tool_args.items())
            lines.append(f"   → Tool: `{step.tool_name}({args_str})`")
            if step.result:
                status = "✅" if step.result.success else "❌"
                lines.append(f"   → {status} {step.result.summary}")
        lines.append("")
    return "\n".join(lines)


# ══════════════════════════════════════════════
# MAIN AGENT PIPELINE
# ══════════════════════════════════════════════

def run_agent(user_input: str, memory: list[dict]) -> tuple[str, str, list[str]]:
    """
    Full agentic pipeline:
      1. Extract entities
      2. Detect intents
      3. Build plan (with memory-aware drug resolution)
      4. Execute plan (call tools)
      5. Generate response + reasoning trace

    Returns: (response_text, reasoning_trace, extracted_drugs)
    """
    tokens = _preprocess(user_input)
    drugs, unrecognized = _extract_drugs(tokens, user_input)
    intents = _detect_intents(tokens, user_input)

    # Build the plan
    plan = _build_plan(intents, drugs, user_input, memory, unrecognized=unrecognized)

    # Execute tool calls
    plan = _execute_plan(plan)

    # Generate response
    if plan.final_answer:
        response = plan.final_answer
    else:
        response = _format_tool_results(plan)
        # Append unrecognized drug note if applicable
        if unrecognized:
            names = ", ".join(f"**{n}**" for n in unrecognized)
            response += (
                f"\n\n---\n⚠️ **Note:** {names} "
                f"{'was' if len(unrecognized) == 1 else 'were'} mentioned but "
                f"not found in my database. Results shown are for the recognized drugs only."
            )
        if not response.strip():
            response = _make_fallback_no_drugs()

    # Generate reasoning trace
    trace = _generate_reasoning_trace(plan)

    # Resolve which drugs were used (for memory)
    resolved_drugs = _resolve_drugs_with_memory(drugs, memory, intents)

    return response, trace, resolved_drugs


# ══════════════════════════════════════════════
# PUBLIC: render_chatbot() — call from app.py
# ══════════════════════════════════════════════

def render_chatbot():
    """Render the full agentic chatbot UI inside the current Streamlit app."""

    # ── Header ──
    st.markdown(
        """
        <div class="main-header">
            <h1>🤖 MedGuard AI Agent</h1>
            <p class="subtitle">Agentic Drug Interaction Assistant — Reasons, Plans & Executes</p>
            <span class="badge">✦ ASTRAVA 2026 · Agentic AI</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Capability pills ──
    st.markdown(
        """
        <div style="display:flex;flex-wrap:wrap;gap:0.5rem;margin:0.5rem 0 1rem 0;">
            <span style="display:inline-block;padding:0.35rem 0.9rem;border-radius:20px;
                font-size:0.82rem;font-weight:500;background:rgba(21,101,192,0.10);
                color:#1565c0;border:1px solid rgba(21,101,192,0.25);">🔍 Interaction Check</span>
            <span style="display:inline-block;padding:0.35rem 0.9rem;border-radius:20px;
                font-size:0.82rem;font-weight:500;background:rgba(21,101,192,0.10);
                color:#1565c0;border:1px solid rgba(21,101,192,0.25);">📋 Drug Profiles</span>
            <span style="display:inline-block;padding:0.35rem 0.9rem;border-radius:20px;
                font-size:0.82rem;font-weight:500;background:rgba(21,101,192,0.10);
                color:#1565c0;border:1px solid rgba(21,101,192,0.25);">⚠️ Safety Assessment</span>
            <span style="display:inline-block;padding:0.35rem 0.9rem;border-radius:20px;
                font-size:0.82rem;font-weight:500;background:rgba(21,101,192,0.10);
                color:#1565c0;border:1px solid rgba(21,101,192,0.25);">💊 Alternatives</span>
            <span style="display:inline-block;padding:0.35rem 0.9rem;border-radius:20px;
                font-size:0.82rem;font-weight:500;background:rgba(76,175,80,0.10);
                color:#4caf50;border:1px solid rgba(76,175,80,0.25);">🧠 Multi-Step Reasoning</span>
            <span style="display:inline-block;padding:0.35rem 0.9rem;border-radius:20px;
                font-size:0.82rem;font-weight:500;background:rgba(76,175,80,0.10);
                color:#4caf50;border:1px solid rgba(76,175,80,0.25);">💬 Conversation Memory</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Database stats ──
    c1, c2, c3 = st.columns(3)
    c1.metric("💊 Drugs in Database", f"{len(_DRUG_NAMES):,}")
    c2.metric("🔗 Interaction Records", f"{len(_DF):,}")
    c3.metric("🔧 Agent Tools", f"{len(TOOL_REGISTRY)}")

    st.markdown("")

    # ── Chat & memory state ──
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
        st.session_state.chat_history.append(
            {"role": "assistant", "content": _make_greeting(), "trace": None, "drugs": []}
        )
    if "agent_memory" not in st.session_state:
        st.session_state.agent_memory = []

    # ── Render messages ──
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            # Show reasoning trace for agent messages
            if msg["role"] == "assistant" and msg.get("trace"):
                with st.expander("🧠 Agent Reasoning Trace", expanded=False):
                    st.markdown(msg["trace"])

    # ── Input ──
    user_input = st.chat_input("Ask me anything about drug interactions…")

    if user_input:
        # Display user message
        st.session_state.chat_history.append(
            {"role": "user", "content": user_input, "trace": None, "drugs": []}
        )
        with st.chat_message("user"):
            st.markdown(user_input)

        # Run the agent
        with st.chat_message("assistant"):
            with st.spinner("🧠 Agent is reasoning…"):
                response, trace, drugs = run_agent(user_input, st.session_state.agent_memory)

            st.markdown(response)

            if trace.strip():
                with st.expander("🧠 Agent Reasoning Trace", expanded=False):
                    st.markdown(trace)

        # Update memory
        st.session_state.agent_memory.append({
            "role": "user",
            "content": user_input,
            "drugs": drugs,
        })
        st.session_state.agent_memory.append({
            "role": "assistant",
            "content": response,
            "drugs": drugs,
        })
        # Keep memory bounded
        if len(st.session_state.agent_memory) > 20:
            st.session_state.agent_memory = st.session_state.agent_memory[-20:]

        # Save to chat history
        st.session_state.chat_history.append(
            {"role": "assistant", "content": response, "trace": trace, "drugs": drugs}
        )

    # ── Clear chat button ──
    st.markdown("")
    col_l, col_c, col_r = st.columns([1.2, 1, 1.2])
    with col_c:
        if st.button("🗑️  Clear Chat & Memory", use_container_width=True, key="clear_chat"):
            st.session_state.chat_history = []
            st.session_state.agent_memory = []
            st.rerun()

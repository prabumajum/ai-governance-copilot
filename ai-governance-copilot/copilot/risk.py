"""Deterministic AI risk helpers used as agent tools.

Why rule-based? Tools should be predictable and testable. The LLM decides WHEN to
call a tool and explains the result; the tool itself always gives the same answer.
"""

DISCLAIMER = "Indicative screening only — confirm with the full legal text and counsel."

# Keyword rules modelled on EU AI Act risk tiers (simplified on purpose).
PROHIBITED = {
    "social scoring": [["social scor"], ["citizen score"], ["trustworthiness score"]],
    "emotion recognition at work or school": [["emotion", "employee"], ["emotion", "workplace"],
                                               ["emotion", "student"], ["emotion", "school"]],
    "untargeted facial image scraping": [["scrap", "face"], ["scrap", "facial"]],
    "manipulative techniques": [["subliminal"], ["manipulat", "vulnerab"]],
}
HIGH_RISK = {
    "employment and recruitment": ["hiring", "recruit", "cv ", "cvs", "resume", "candidate", "promotion", "termination"],
    "credit and lending": ["credit", "loan", "lending", "creditworth"],
    "insurance pricing": ["life insurance", "health insurance", "insurance pricing", "premium pricing"],
    "education and exams": ["exam", "admission", "grading", "student assessment"],
    "essential services": ["welfare", "public benefit", "emergency call", "eligibility for benefits"],
    "biometrics": ["biometric", "facial recognition", "face recognition", "fingerprint"],
    "law enforcement": ["police", "law enforcement", "crime prediction"],
    "migration and border control": ["visa", "asylum", "border control", "immigration"],
    "critical infrastructure": ["power grid", "water supply", "traffic control", "electricity network"],
    "medical": ["diagnos", "medical device", "patient triage", "treatment recommendation"],
}
LIMITED_RISK = ["chatbot", "virtual assistant", "customer support bot", "deepfake", "synthetic",
                "generate image", "image generation", "generated content", "content generation",
                "voice clone", "emotion recognition"]

OBLIGATIONS = {
    "Prohibited": ["Do not deploy in the EU", "Escalate to legal and the AI governance committee"],
    "High risk": ["Full AI impact assessment (ISO/IEC 42005)", "Human oversight with a named owner",
                  "Bias and accuracy testing before release", "Technical documentation and logging",
                  "Register in the risk register; review at least yearly"],
    "Limited risk (transparency)": ["Tell users they are interacting with AI",
                                    "Label or watermark AI-generated content",
                                    "Basic risk assessment and monitoring"],
    "Minimal risk": ["Record in the AI inventory", "Standard risk assessment", "AI literacy training for users"],
}


def classify_use_case(description: str) -> dict:
    """Screen a described AI use case into a risk tier with the reasons."""
    text = " " + (description or "").lower() + " "

    reasons = [name for name, combos in PROHIBITED.items()
               if any(all(word in text for word in combo) for combo in combos)]
    if reasons:
        tier = "Prohibited"
    else:
        reasons = [area for area, words in HIGH_RISK.items() if any(w in text for w in words)]
        if reasons:
            tier = "High risk"
        else:
            reasons = [w for w in LIMITED_RISK if w in text]
            tier = "Limited risk (transparency)" if reasons else "Minimal risk"
            if not reasons:
                reasons = ["no high-risk or transparency triggers found"]

    return {"tier": tier, "matched": reasons, "obligations": OBLIGATIONS[tier], "note": DISCLAIMER}


def score_risk(likelihood: int, impact: int) -> dict:
    """Likelihood x impact on 1-5 scales, banded the ISO/IEC 42001 way."""
    for name, value in (("likelihood", likelihood), ("impact", impact)):
        if not isinstance(value, int) or not 1 <= value <= 5:
            raise ValueError(f"{name} must be a whole number from 1 to 5, got {value!r}")
    score = likelihood * impact
    if score <= 6:
        band, treatment = "Low", "Accept and monitor"
    elif score <= 12:
        band, treatment = "Medium", "Treat, or accept with AI governance committee sign-off"
    else:
        band, treatment = "High", "Must treat before go-live; residual risk needs executive sign-off"
    return {"score": score, "band": band, "treatment": treatment}


def draft_risk_entry(system_name: str, risk_description: str, likelihood: int, impact: int) -> dict:
    """Build one risk-register row plus a Markdown table for display."""
    scored = score_risk(int(likelihood), int(impact))
    row = {
        "AI system": system_name,
        "Risk": risk_description,
        "Likelihood": likelihood,
        "Impact": impact,
        "Score": scored["score"],
        "Band": scored["band"],
        "Treatment": scored["treatment"],
        "Owner": "To be assigned",
    }
    header = "| " + " | ".join(row) + " |"
    divider = "| " + " | ".join("---" for _ in row) + " |"
    values = "| " + " | ".join(str(v) for v in row.values()) + " |"
    return {**row, "markdown": "\n".join([header, divider, values])}

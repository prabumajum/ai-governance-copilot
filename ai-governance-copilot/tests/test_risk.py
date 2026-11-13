import pytest

from copilot import risk


@pytest.mark.parametrize("description, tier", [
    ("A social scoring system for citizens", "Prohibited"),
    ("Emotion recognition to monitor employee mood", "Prohibited"),
    ("AI that screens CVs for hiring", "High risk"),
    ("Model that decides loan approvals", "High risk"),
    ("A customer support chatbot on our website", "Limited risk (transparency)"),
    ("Spam filter for the internal mailbox", "Minimal risk"),
])
def test_classify_use_case(description, tier):
    assert risk.classify_use_case(description)["tier"] == tier


@pytest.mark.parametrize("likelihood, impact, band", [(1, 1, "Low"), (2, 3, "Low"),
                                                      (3, 4, "Medium"), (4, 4, "High"), (5, 5, "High")])
def test_score_bands(likelihood, impact, band):
    assert risk.score_risk(likelihood, impact)["band"] == band


def test_score_rejects_out_of_range():
    with pytest.raises(ValueError):
        risk.score_risk(0, 6)


def test_draft_entry_has_markdown_table():
    entry = risk.draft_risk_entry("Loan bot", "Wrong interest rates", 3, 4)
    assert entry["Score"] == 12 and entry["Band"] == "Medium"
    assert entry["markdown"].startswith("| AI system |")

import pytest

from copilot.knowledge import KNOWLEDGE_DIR, load_chunks


def test_chunks_cover_every_file():
    chunks = load_chunks()
    files = {p.name for p in KNOWLEDGE_DIR.glob("*.md")}
    assert {c["source"] for c in chunks} == files
    assert all(c["text"] and c["section"] for c in chunks)
    assert len({c["id"] for c in chunks}) == len(chunks)


def test_chunks_keep_title_and_section_context():
    chunk = next(c for c in load_chunks() if c["section"] == "Penalties")
    assert chunk["text"].startswith("EU AI Act essentials — Penalties:")


def test_semantic_search_finds_the_right_document():
    pytest.importorskip("fastembed")
    pytest.importorskip("qdrant_client")
    from copilot.knowledge import get_knowledge_base
    hits = get_knowledge_base().search("maximum fines for prohibited AI practices", k=3)
    assert hits[0]["source"] == "eu_ai_act.md"
    assert hits[0]["score"] >= hits[-1]["score"]

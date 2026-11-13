"""Evaluation harness: run a golden set of questions and score the agent.

    python evals/run_evals.py                   # full agent evals (needs a Gemini key)
    python evals/run_evals.py --retrieval-only  # RAG retrieval evals only (no key needed)

Checks per question:
  - keywords:  expected facts appear in the answer
  - tool:      the agent chose the right tool
  - citation:  the expected source file was retrieved
  - guardrail: injection blocked / personal data redacted
Results are printed as a table and saved to evals/results.json.
"""
import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

GOLDEN = json.loads((ROOT / "evals" / "golden_set.json").read_text(encoding="utf-8"))


def retrieval_evals(k: int = 4) -> float:
    """hit@k: is the expected source among the top-k retrieved chunks?"""
    from copilot.knowledge import get_knowledge_base
    kb = get_knowledge_base()
    cases = [c for c in GOLDEN if c.get("expect_source")]
    hits = 0
    for case in cases:
        sources = [h["source"] for h in kb.search(case["question"], k=k)]
        ok = case["expect_source"] in sources
        hits += ok
        print(f"{'PASS' if ok else 'FAIL'}  {case['id']:<22} top-{k}: {sources}")
    score = hits / len(cases)
    print(f"\nRetrieval hit@{k}: {hits}/{len(cases)} = {score:.0%}")
    return score


def score_case(case: dict, result: dict) -> dict:
    checks = {}
    answer = result["answer"].lower()
    if case.get("expect_keywords"):
        checks["keywords"] = all(k.lower() in answer for k in case["expect_keywords"])
    if case.get("expect_tool"):
        checks["tool"] = case["expect_tool"] in result["tools_used"]
    if case.get("expect_source"):
        checks["citation"] = case["expect_source"] in result["sources"]
    if "expect_blocked" in case:
        checks["guardrail"] = result["blocked"] == case["expect_blocked"]
    if case.get("expect_redacted"):
        checks["guardrail"] = any(case["expect_redacted"] in e for e in result["guard_events"])
    return checks


def agent_evals(delay: float) -> float:
    from copilot.agent import build_graph, run_turn
    graph = build_graph()
    rows, passed = [], 0
    for case in GOLDEN:
        for attempt in range(3):  # retry on free-tier rate limits (HTTP 429)
            try:
                result = run_turn(graph, case["question"])
                break
            except Exception as error:
                if "429" in str(error) and attempt < 2:
                    time.sleep(30)
                    continue
                result = {"answer": f"ERROR: {error}", "tools_used": [], "sources": [],
                          "guard_events": [], "blocked": False, "latency_s": 0}
                break
        checks = score_case(case, result)
        ok = all(checks.values())
        passed += ok
        rows.append({"id": case["id"], "pass": ok, "checks": checks,
                     "latency_s": result["latency_s"], "tools_used": result["tools_used"]})
        detail = "  ".join(f"{name}={'ok' if v else 'X'}" for name, v in checks.items())
        print(f"{'PASS' if ok else 'FAIL'}  {case['id']:<24} {result['latency_s']:>5}s  {detail}")
        time.sleep(delay)  # stay under the free-tier requests-per-minute limit

    score = passed / len(GOLDEN)
    avg_latency = sum(r["latency_s"] for r in rows) / len(rows)
    print(f"\nAgent evals: {passed}/{len(GOLDEN)} passed = {score:.0%}   avg latency {avg_latency:.1f}s")
    (ROOT / "evals" / "results.json").write_text(json.dumps(
        {"score": score, "avg_latency_s": round(avg_latency, 2), "cases": rows}, indent=2))
    return score


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--retrieval-only", action="store_true", help="only test RAG retrieval")
    parser.add_argument("--delay", type=float, default=6.0, help="seconds between questions")
    parser.add_argument("--min-score", type=float, default=0.0, help="exit 1 if score is lower")
    args = parser.parse_args()

    final = retrieval_evals() if args.retrieval_only else agent_evals(args.delay)
    sys.exit(0 if final >= args.min_score else 1)

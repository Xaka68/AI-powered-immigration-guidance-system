"""E2 — Comparison runner: generic LLM vs. journey-guided (our system).

For each question in test_questions.csv:
  - GENERIC: ask the LLM directly (no journey, no retrieval) — the baseline.
  - GUIDED:  drive the real /chat pipeline (router -> graph -> retrieval) to a
             grounded answer, auto-selecting the first offered chip when the
             system asks a clarifying question (options-first).

Writes data/eval/comparison.md. Run:
    PYTHONPATH=backend/src python data/eval/run_eval.py
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

from core.llm import complete
from core.types import ChatRequest
from orchestration.loader import load_journeys
from orchestration.pipeline import run_turn

ROOT = Path(__file__).resolve().parents[2]
CSV = ROOT / "data" / "eval" / "test_questions.csv"
OUT = ROOT / "data" / "eval" / "comparison.md"

_HUMAN = {"talk_to_human", "human", "talk_to_counselor", "counselor"}


def generic(question: str) -> str:
    """Baseline: a plain LLM answer with no grounding (what a generic chatbot does)."""
    try:
        return complete(
            "You are a general assistant. Answer the user's question directly and "
            "concisely in the user's language.",
            question,
        ).strip().replace("\n", " ")
    except Exception as exc:
        return f"(LLM error: {exc})"


def guided(question: str, max_turns: int = 5) -> dict:
    """Drive the pipeline, auto-tapping the first non-handoff chip until we reach
    a grounded answer or a handoff. Returns a summary dict."""
    resp = run_turn(ChatRequest(message=question), load_journeys())
    clarifications = 0
    for _ in range(max_turns):
        if resp.requires_handoff:
            break
        if resp.answer and resp.answer.short_answer:
            break
        chips = [o for o in resp.options if o.id not in _HUMAN]
        if not chips:
            break
        clarifications += 1
        resp = run_turn(
            ChatRequest(option_id=chips[0].id, session=resp.session), load_journeys()
        )
    ans = resp.answer.short_answer if resp.answer else ""
    return {
        "journey": resp.journey_id or "(none)",
        "clarifications": clarifications,
        "handoff": resp.requires_handoff,
        "answer": (ans or "").replace("\n", " "),
        "sources": [f"{s.title} ({s.last_updated or 'n/a'})" for s in resp.sources],
    }


def main() -> None:
    rows = list(csv.DictReader(open(CSV, encoding="utf-8")))
    lines = [
        "# E2 — Generic LLM vs. Journey-Guided (Integreat Compass)",
        "",
        f"Ran {len(rows)} questions from `test_questions.csv` through both a plain "
        "LLM and our pipeline. The system is **options-first** (it clarifies before "
        "answering) and **source-grounded** (every answer cites live Integreat pages).",
        "",
    ]
    for r in rows:
        q = r["question"]
        print(f"running {r['id']}: {q[:50]}...")
        g = guided(q)
        base = generic(q)
        srcs = "; ".join(g["sources"]) or "—"
        lines += [
            f"## {r['id']} — {q}",
            f"- **lang/expected journey:** {r['language']} / `{r['expected_journeys']}`",
            f"- **Generic LLM (no grounding):** {base[:400]}",
            f"- **Journey-guided →** journey `{g['journey']}`, "
            f"clarifying questions asked: {g['clarifications']}, "
            f"handoff: {g['handoff']}",
            f"  - **grounded answer:** {(g['answer'] or '(reached handoff / clarification)')[:400]}",
            f"  - **sources cited:** {srcs}",
            "",
        ]
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()

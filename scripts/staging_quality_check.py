from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from casts.resume_ingestor.graph import resume_ingestor_graph
from casts.resume_ingestor.modules.models import get_generation_model


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run staging quality check")
    parser.add_argument(
        "--resume-file",
        default="docs/samples/staging_resume.txt",
        help="Path to plaintext resume sample",
    )
    parser.add_argument(
        "--allow-fallback",
        action="store_true",
        help="Allow deterministic fallback when LLM is unavailable",
    )
    return parser.parse_args()


def _provider_name() -> str:
    return os.getenv("INTERVIEWGRAPH_LLM_PROVIDER", "openai").strip().lower()


def _has_provider_key() -> bool:
    provider = _provider_name()
    if provider == "openai":
        return bool(os.getenv("OPENAI_API_KEY", "").strip())
    if provider == "anthropic":
        return bool(os.getenv("ANTHROPIC_API_KEY", "").strip())
    return False


def _quality_report(result: dict[str, object]) -> dict[str, object]:
    questions = result.get("questions", [])
    errors = result.get("errors", [])
    generation_mode = str(result.get("generation_mode", "fallback"))

    if not isinstance(questions, list):
        questions = []
    if not isinstance(errors, list):
        errors = []

    categories = []
    with_evidence_terms = 0
    for item in questions:
        if not isinstance(item, dict):
            continue
        category = item.get("category")
        question = str(item.get("question", "")).lower()
        if isinstance(category, str):
            categories.append(category)

        if any(
            term in question
            for term in ("project", "production", "trade-off", "scale", "impact")
        ):
            with_evidence_terms += 1

    unique_categories = sorted(set(categories))
    return {
        "generation_mode": generation_mode,
        "question_count": len(questions),
        "unique_categories": unique_categories,
        "category_count": len(unique_categories),
        "questions_with_context_terms": with_evidence_terms,
        "error_count": len(errors),
    }


def _as_int(value: object, default: int = 0) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return default


def main() -> int:
    args = _parse_args()
    resume_path = Path(args.resume_file)
    if not resume_path.exists():
        print(f"Resume sample not found: {resume_path}")
        return 2

    model = get_generation_model()
    llm_ready = model is not None and _has_provider_key()
    if not llm_ready and not args.allow_fallback:
        provider = _provider_name()
        print(
            "LLM is not configured. Set provider/model vars and API key, then rerun. "
            f"provider={provider}"
        )
        return 2

    resume_text = resume_path.read_text(encoding="utf-8")
    graph = resume_ingestor_graph()
    result = graph.invoke({"resume_text": resume_text})
    report = _quality_report(result)

    print(
        json.dumps(
            {"llm_ready": llm_ready, "report": report}, ensure_ascii=True, indent=2
        )
    )

    question_count = _as_int(report.get("question_count"), 0)
    category_count = _as_int(report.get("category_count"), 0)

    generation_mode = str(report.get("generation_mode", "fallback"))

    if question_count != 15:
        return 1

    min_categories = 3 if llm_ready else 2
    if category_count < min_categories:
        return 1

    if llm_ready and generation_mode != "llm":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""[Optional] Prompt templates tailored to the Resume Ingestor graph.

Guidelines:
    - Create LangChain `PromptTemplate` or LCEL prompt definitions.
    - Consume these templates from the chain/node modules.

Official document URL:
    - Messages: https://docs.langchain.com/oss/python/langchain/messages
    - OpenAI prompt engineering: https://platform.openai.com/docs/guides/prompt-engineering
    - Gemini prompt engineering: https://ai.google.dev/gemini-api/docs/prompting-strategies?hl=ko
    - Claude prompt engineering: https://docs.claude.com/en/docs/build-with-claude/prompt-engineering
"""

from __future__ import annotations

import json


def build_question_generation_messages(
    *,
    raw_text: str,
    sections: dict[str, object],
    signals: dict[str, object],
) -> list[dict[str, str]]:
    """Builds a schema-constrained prompt for interview question generation."""

    system_content = (
        "You generate resume-grounded interview questions. "
        "Return only valid JSON. Do not include markdown fences or extra text."
    )

    section_payload = {
        key: value
        for key, value in sections.items()
        if isinstance(value, str) and value.strip()
    }

    signal_payload = {
        "skills": signals.get("skills", []),
        "projects": signals.get("projects", []),
        "keywords": signals.get("keywords", []),
        "evidence": signals.get("evidence", []),
    }

    schema_hint = {
        "questions": [
            {
                "id": "q01",
                "category": "tech",
                "difficulty": 3,
                "question": "string",
                "expected_points": ["string"],
                "followups": ["string"],
            }
        ]
    }

    user_content = (
        "Generate exactly 15 interview questions.\n"
        "Rules:\n"
        "1) Categories must be one of: tech, project, system, deep-dive.\n"
        "2) Difficulty must be integer 1-5.\n"
        "3) Each question must be anchored to resume evidence (skills/projects/experience).\n"
        "4) Avoid generic wording and duplicates.\n"
        "5) Include 3 expected_points and 2 followups per item.\n"
        "6) Output strict JSON only with top-level key 'questions'.\n\n"
        f"Raw resume text:\n{raw_text[:6000]}\n\n"
        f"Parsed sections:\n{json.dumps(section_payload, ensure_ascii=True)}\n\n"
        f"Extracted signals:\n{json.dumps(signal_payload, ensure_ascii=True)}\n\n"
        f"Output JSON shape example:\n{json.dumps(schema_hint, ensure_ascii=True)}"
    )

    return [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_content},
    ]

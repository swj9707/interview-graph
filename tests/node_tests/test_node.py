"""Test nodes for the Resume Ingestor graph."""

from __future__ import annotations

from casts.resume_ingestor.modules.nodes import (
    ExtractSignalsNode,
    ExtractTextNode,
    FormatOutputNode,
    GenerateQuestionsNode,
    ParseSectionsNode,
    RateDifficultyNode,
    ValidateQuestionsNode,
)


def test_extract_text_node_uses_inline_resume_text() -> None:
    node = ExtractTextNode()
    result = node({"resume_text": "Python backend engineer"})

    assert result["raw_text"] == "Python backend engineer"
    assert result["errors"] == []


def test_parse_sections_node_splits_by_headers() -> None:
    node = ParseSectionsNode()
    result = node(
        {
            "raw_text": (
                "Summary\n"
                "Backend engineer with 6 years of experience\n"
                "Skills\n"
                "Python, FastAPI, AWS\n"
                "Projects\n"
                "Built interview automation service\n"
            ),
            "errors": [],
        }
    )

    assert "sections" in result
    assert (
        result["sections"]["summary"] == "Backend engineer with 6 years of experience"
    )
    assert result["sections"]["skills"] == "Python, FastAPI, AWS"
    assert result["sections"]["projects"] == "Built interview automation service"


def test_parse_sections_node_returns_error_without_raw_text() -> None:
    node = ParseSectionsNode()
    result = node({"raw_text": "", "errors": []})

    assert len(result["errors"]) == 1
    assert result["errors"][0]["code"] == "MISSING_RAW_TEXT"


def test_extract_signals_node_extracts_skills_projects_keywords() -> None:
    node = ExtractSignalsNode()
    result = node(
        {
            "sections": {
                "summary": "Backend engineer focusing on payment platforms",
                "skills": "Python, FastAPI, AWS, Docker",
                "projects": (
                    "Built fraud detection service using FastAPI\n"
                    "Designed event-driven payment pipeline"
                ),
            },
            "errors": [],
        }
    )

    assert result["signals"]["skills"] == ["Python", "FastAPI", "AWS", "Docker"]
    assert result["signals"]["projects"] == [
        "Built fraud detection service using FastAPI",
        "Designed event-driven payment pipeline",
    ]
    assert "fastapi" in result["signals"]["keywords"]
    assert "payment" in result["signals"]["keywords"]


def test_extract_signals_node_returns_error_without_sections() -> None:
    node = ExtractSignalsNode()
    result = node({"sections": {}, "errors": []})

    assert result["signals"] == {
        "skills": [],
        "projects": [],
        "keywords": [],
        "evidence": [],
    }
    assert len(result["errors"]) == 1
    assert result["errors"][0]["code"] == "MISSING_SECTIONS"


def test_generate_questions_node_creates_15_structured_items(monkeypatch) -> None:
    monkeypatch.setattr(
        "casts.resume_ingestor.modules.nodes.get_generation_model_with_reason",
        lambda: (None, "missing_credentials"),
    )
    node = GenerateQuestionsNode()
    result = node(
        {
            "raw_text": "Backend engineer with production API and cloud infra experience",
            "sections": {
                "summary": "Backend engineer",
                "projects": "Built interview graph service",
            },
            "signals": {
                "skills": ["Python", "FastAPI", "AWS"],
                "projects": ["Built interview graph service"],
                "keywords": ["backend", "api", "scalability"],
                "evidence": ["Built interview graph service used by recruiting teams"],
            },
            "errors": [],
        }
    )

    assert len(result["questions"]) == 15
    first = result["questions"][0]
    assert first["id"] == "q01"
    assert first["category"] in {"tech", "project", "system", "deep-dive"}
    assert first["difficulty"] == 0
    assert isinstance(first["question"], str)
    assert len(first["expected_points"]) >= 1
    assert len(first["followups"]) >= 1


def test_generate_questions_node_uses_llm_when_available(monkeypatch) -> None:
    node = GenerateQuestionsNode()

    class FakeResponse:
        content = (
            '{"questions":[{"id":"qx","category":"tech","difficulty":4,'
            '"question":"How did you scale FastAPI for burst traffic?",'
            '"expected_points":["Autoscaling","Bottleneck analysis","SLO impact"],'
            '"followups":["What failed first?","How did you validate?", "extra"]}]}'
        )

    class FakeModel:
        def invoke(self, _messages):
            return FakeResponse()

    monkeypatch.setattr(
        "casts.resume_ingestor.modules.nodes.get_generation_model_with_reason",
        lambda: (FakeModel(), "ready"),
    )

    result = node(
        {
            "raw_text": "Senior backend engineer",
            "sections": {"summary": "Senior backend engineer"},
            "signals": {
                "skills": ["FastAPI"],
                "projects": ["Built interview graph service"],
                "keywords": ["scalability"],
                "evidence": ["Scaled API for recruiting platform"],
            },
            "errors": [],
        }
    )

    assert len(result["questions"]) == 1
    assert result["questions"][0]["id"] == "q01"
    assert result["questions"][0]["category"] == "tech"
    assert result["questions"][0]["difficulty"] == 4
    assert len(result["questions"][0]["expected_points"]) == 3
    assert len(result["questions"][0]["followups"]) == 2


def test_rate_difficulty_node_assigns_1_to_5_scale() -> None:
    node = RateDifficultyNode()
    generated_questions = [
        {
            "id": f"q{idx:02d}",
            "category": "tech" if idx % 2 == 0 else "deep-dive",
            "difficulty": 0,
            "question": f"Question {idx}",
            "expected_points": ["Point A"],
            "followups": ["Follow-up A"],
        }
        for idx in range(1, 16)
    ]
    result = node({"questions": generated_questions, "errors": []})

    assert len(result["questions"]) == 15
    difficulties = [q["difficulty"] for q in result["questions"]]
    assert all(isinstance(d, int) and 1 <= d <= 5 for d in difficulties)


def test_format_output_node_renders_markdown() -> None:
    node = FormatOutputNode()
    result = node(
        {
            "questions": [
                {
                    "id": "q01",
                    "category": "tech",
                    "difficulty": 3,
                    "question": "How did you design your API error model?",
                    "expected_points": ["Consistency", "Client usability"],
                    "followups": ["How did you version errors?"],
                }
            ],
            "errors": [],
        }
    )

    assert result["questions"][0]["id"] == "q01"
    assert "# Interview Questions" in result["markdown"]
    assert "Difficulty: 3" in result["markdown"]
    assert "Expected points:" in result["markdown"]


def test_validate_questions_node_removes_duplicates_and_normalizes_ids() -> None:
    node = ValidateQuestionsNode()
    duplicate_question = {
        "id": "qx",
        "category": "tech",
        "difficulty": 3,
        "question": "How did you use FastAPI in production?",
        "expected_points": ["Context"],
        "followups": ["What was hard?"],
    }

    result = node(
        {
            "signals": {
                "skills": ["FastAPI", "Python"],
                "projects": ["Built hiring pipeline service"],
                "keywords": ["backend"],
            },
            "questions": [duplicate_question, duplicate_question],
            "errors": [],
        }
    )

    assert len(result["questions"]) == 15
    assert result["questions"][0]["id"] == "q01"
    assert result["questions"][1]["id"] == "q02"


def test_validate_questions_node_rewrites_generic_question_using_evidence() -> None:
    node = ValidateQuestionsNode()
    result = node(
        {
            "signals": {
                "skills": ["Kubernetes"],
                "projects": ["Realtime fraud detection"],
                "keywords": ["scalability"],
            },
            "questions": [
                {
                    "id": "q01",
                    "category": "system",
                    "difficulty": 4,
                    "question": "Tell me about your experience.",
                    "expected_points": ["Something"],
                    "followups": ["More details?"],
                }
            ],
            "errors": [],
        }
    )

    assert len(result["questions"]) == 15
    rewritten = result["questions"][0]["question"].lower()
    assert "kubernetes" in rewritten or "realtime fraud detection" in rewritten

"""Test nodes for the Resume Ingestor graph."""

from __future__ import annotations

from casts.resume_ingestor.modules.nodes import (
    ExtractSignalsNode,
    ExtractTextNode,
    ParseSectionsNode,
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

    assert result["signals"] == {"skills": [], "projects": [], "keywords": []}
    assert len(result["errors"]) == 1
    assert result["errors"][0]["code"] == "MISSING_SECTIONS"

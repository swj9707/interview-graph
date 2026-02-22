"""Test the Resume Ingestor graph.

Official document URL:
    https://docs.langchain.com/oss/python/langgraph/test"""

from __future__ import annotations

from casts.resume_ingestor.graph import resume_ingestor_graph


def test_graph_extracts_text_from_resume_text() -> None:
    graph = resume_ingestor_graph()
    result = graph.invoke(
        {"resume_text": "Senior Backend Engineer with Python and AWS"}
    )

    assert len(result["questions"]) == 15
    assert all(1 <= q["difficulty"] <= 5 for q in result["questions"])
    assert result["markdown"] == ""
    assert result["errors"] == []


def test_graph_returns_error_when_input_missing() -> None:
    graph = resume_ingestor_graph()
    result = graph.invoke({})

    assert result["questions"] == []
    assert result["markdown"] == ""
    assert len(result["errors"]) == 1
    assert result["errors"][0]["code"] == "MISSING_INPUT"


def test_graph_pipeline_completes_with_sectioned_resume_text() -> None:
    graph = resume_ingestor_graph()
    result = graph.invoke(
        {
            "resume_text": (
                "Summary\n"
                "Backend engineer\n"
                "Skills\n"
                "Python, FastAPI, AWS\n"
                "Projects\n"
                "Built interview tooling\n"
            )
        }
    )

    assert len(result["questions"]) == 15
    assert result["questions"][0]["id"] == "q01"
    assert all(1 <= q["difficulty"] <= 5 for q in result["questions"])
    assert result["markdown"] == ""
    assert result["errors"] == []

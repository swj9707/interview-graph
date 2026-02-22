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

    assert result["questions"] == []
    assert result["markdown"] == ""
    assert result["errors"] == []


def test_graph_returns_error_when_input_missing() -> None:
    graph = resume_ingestor_graph()
    result = graph.invoke({})

    assert result["questions"] == []
    assert result["markdown"] == ""
    assert len(result["errors"]) == 1
    assert result["errors"][0]["code"] == "MISSING_INPUT"

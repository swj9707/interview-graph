"""Test the Resume Ingestor graph.

Official document URL:
    https://docs.langchain.com/oss/python/langgraph/test"""

from __future__ import annotations

from casts.resume_ingestor.graph import resume_ingestor_graph


def test_graph_produces_message() -> None:
    graph = resume_ingestor_graph()

    # 최소 상태로 그래프 실행
    result = graph.invoke({"query": "I'm joining Act"})

    # SampleNode가 message 키를 생성하는지 확인
    assert "messages" in result
    assert result["messages"] == "Welcome to the Act!"

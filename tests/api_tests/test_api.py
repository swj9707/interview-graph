from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_generate_interview_questions_from_text() -> None:
    response = client.post(
        "/api/v1/interview-questions",
        json={
            "resume_text": (
                "Summary\n"
                "Backend engineer\n"
                "Skills\n"
                "Python, FastAPI, AWS\n"
                "Projects\n"
                "Built interview tooling\n"
            )
        },
    )

    payload = response.json()
    assert response.status_code == 200
    assert len(payload["questions"]) == 15
    assert "# Interview Questions" in payload["markdown"]
    assert payload["errors"] == []


def test_generate_interview_questions_requires_input() -> None:
    response = client.post("/api/v1/interview-questions", json={})
    assert response.status_code == 400


def test_upload_requires_pdf() -> None:
    response = client.post(
        "/api/v1/interview-questions/upload",
        files={"file": ("resume.txt", b"not pdf", "text/plain")},
    )
    assert response.status_code == 400

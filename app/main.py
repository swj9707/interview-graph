from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel, Field
from pypdf import PdfReader

from casts.resume_ingestor.graph import resume_ingestor_graph


def _load_runtime_env() -> None:
    """Loads local env files for API runtime when available."""

    try:
        from dotenv import load_dotenv
    except Exception:
        return

    project_root = Path(__file__).resolve().parents[1]
    load_dotenv(project_root / ".env", override=False)
    load_dotenv(project_root / ".env.local", override=False)


_load_runtime_env()

app = FastAPI(title="InterviewGraph API", version="0.1.0")


class GenerateRequest(BaseModel):
    resume_text: str | None = Field(default=None)
    resume_path: str | None = Field(default=None)


class GenerateResponse(BaseModel):
    questions: list[dict[str, object]]
    markdown: str
    errors: list[dict[str, object]]
    generation_mode: str = "fallback"


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/v1/interview-questions", response_model=GenerateResponse)
def generate_interview_questions(payload: GenerateRequest) -> GenerateResponse:
    if not payload.resume_text and not payload.resume_path:
        raise HTTPException(
            status_code=400,
            detail="Provide either resume_text or resume_path.",
        )

    graph = resume_ingestor_graph()
    result = graph.invoke(payload.model_dump(exclude_none=True))

    return GenerateResponse(
        questions=result.get("questions", []),
        markdown=result.get("markdown", ""),
        errors=result.get("errors", []),
        generation_mode=str(result.get("generation_mode", "fallback")),
    )


@app.post("/api/v1/interview-questions/upload", response_model=GenerateResponse)
async def generate_from_pdf(file: Annotated[UploadFile, File(...)]) -> GenerateResponse:
    filename = file.filename or ""
    if file.content_type != "application/pdf" and not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF uploads are supported.")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    try:
        reader = PdfReader(BytesIO(content))
        extracted_pages = [page.extract_text() or "" for page in reader.pages]
    except Exception as exc:  # pypdf raises library-specific parse errors
        raise HTTPException(status_code=400, detail="Failed to parse PDF.") from exc

    resume_text = "\n".join(extracted_pages).strip()
    if not resume_text:
        raise HTTPException(
            status_code=422,
            detail="No extractable text found in uploaded PDF.",
        )

    graph = resume_ingestor_graph()
    result = graph.invoke({"resume_text": resume_text})

    return GenerateResponse(
        questions=result.get("questions", []),
        markdown=result.get("markdown", ""),
        errors=result.get("errors", []),
        generation_mode=str(result.get("generation_mode", "fallback")),
    )

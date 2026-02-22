# 🙋‍♂️ InterviewGraph

InterviewGraph is a LangGraph-based service that generates structured interview questions from resume content.

It accepts either resume text or a PDF file, extracts relevant signals, and returns 15 questions with difficulty ratings.

The response includes both structured JSON and Markdown for interviewer-friendly review.

> This project was developed through Act-Operator.
>
> [😺 Act-Operator Github](https://github.com/Proact0/act-operator)

## What It Does

- Accepts resume text or PDF input
- Parses resume sections (summary, skills, experience, projects, education)
- Extracts signals (skills, projects, keywords)
- Generates 15 interview questions
- Rates question difficulty (1-5)
- Formats output as JSON and Markdown

## Architecture (MVP)

Pipeline:

`extract_text -> parse_sections -> extract_signals -> generate_questions -> rate_difficulty -> format_output`

## Quick Start (Local)

1. Install dependencies:

```bash
uv sync --all-packages
```

1. Run API server:

```bash
uv run uvicorn app.main:app --reload
```

1. Open API docs:

- `http://127.0.0.1:8000/docs`

## API Usage

- `POST /api/v1/interview-questions` for text input
- `POST /api/v1/interview-questions/upload` for PDF upload (multipart/form-data)

Example JSON payload:

```json
{
  "resume_text": "Summary ... Skills ... Projects ..."
}
```

## Container Usage

Build image:

```bash
docker build -t interviewgraph:local .
```

Run container:

```bash
docker run --rm -p 8000:8000 interviewgraph:local
```

Open docs:

- `http://127.0.0.1:8000/docs`

## GHCR Publishing

This repository includes `.github/workflows/publish-ghcr.yml`.

- On push to `main`, the workflow builds and publishes to `ghcr.io/<owner>/<repo>`.
- On push tag `v*`, it also publishes versioned tags.
- You can manually trigger publishing with `workflow_dispatch`.

Pull from GHCR:

```bash
docker pull ghcr.io/<owner>/<repo>:latest
docker run --rm -p 8000:8000 ghcr.io/<owner>/<repo>:latest
```

## Current Scope (MVP)

- Text-extractable PDF support
- Resume-grounded question generation pipeline
- Structured error payloads

## Out of Scope (MVP)

- OCR for scanned PDFs
- Vector DB / RAG
- Multi-agent orchestration
- Mock interview answer scoring

## License

Apache License 2.0 - see [LICENSE](https://www.apache.org/licenses/LICENSE-2.0) for details.

# 🙋‍♂️ InterviewGraph

<div align="center">
  <picture>
    <img src=".github/images/logo/interview-graph-logo.png" alt="InterviewGraph logo" width="500">
  </picture>
</div>

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

`extract_text -> parse_sections -> extract_signals -> generate_questions -> rate_difficulty -> validate_questions -> format_output`

## Quick Start (Local)

1. Install dependencies:

```bash
uv sync --all-packages
```

1. Run API server:

```bash
uv run uvicorn app.main:app --reload
```

1. Configure LLM provider (for production-quality generation):

```bash
cp .env.example .env
```

Then set `INTERVIEWGRAPH_LLM_PROVIDER`, `INTERVIEWGRAPH_LLM_MODEL`, and the matching API key.

1. Open API docs:

- `http://127.0.0.1:8000/docs`

## API Usage

- `POST /api/v1/interview-questions` for text input
- `POST /api/v1/interview-questions/upload` for PDF upload (multipart/form-data)
- Response includes `generation_mode` (`llm` or `fallback`)

Example JSON payload:

```json
{
  "resume_text": "Summary ... Skills ... Projects ..."
}
```

## Production LLM Setup

- Runtime variables:
  - `INTERVIEWGRAPH_LLM_PROVIDER`: `openai` or `anthropic`
  - `INTERVIEWGRAPH_LLM_MODEL`: model id (for example `gpt-4o-mini`)
  - `INTERVIEWGRAPH_LLM_TEMPERATURE`: float value
- Required key by provider:
  - `openai` -> `OPENAI_API_KEY`
  - `anthropic` -> `ANTHROPIC_API_KEY`

If provider config or API key is missing, generation falls back to deterministic question templates.

## Staging Quality Check

Run a smoke quality check using a sample resume:

```bash
PYTHONPATH=. uv run python scripts/staging_quality_check.py --resume-file docs/samples/staging_resume.txt
```

For local environments without API keys, use fallback mode:

```bash
PYTHONPATH=. uv run python scripts/staging_quality_check.py --allow-fallback
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

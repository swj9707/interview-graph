You are working inside a LangGraph-based Python project.

Create project planning documentation for a new AI service named "InterviewGraph".

Your task:
Generate two markdown documents:

1) README.md (high-level overview)
2) docs/PLAN.md (detailed product & technical planning document)

The project name is:
InterviewGraph

The core idea:
InterviewGraph takes a resume PDF as input and generates structured, difficulty-rated interview questions based on the resume content.

====================================
README.md REQUIREMENTS
====================================

README.md must include:

1. Project Title
2. Short Description (3~5 lines)
3. Core Features (bullet points)
4. Architecture Overview (high-level explanation of LangGraph pipeline)
5. Example Flow (PDF → Questions)
6. Tech Stack (Python, LangGraph, FastAPI, LLM provider)
7. MVP Scope
8. Future Roadmap (short bullet list)
9. How to Run (placeholder instructions acceptable)

Tone:

- Professional
- Clear
- Developer-focused
- No marketing exaggeration

====================================
docs/PLAN.md REQUIREMENTS
====================================

PLAN.md must include structured sections:

# 1. Project Vision

- Why this project exists
- Target users

# 2. User Scenarios

- Primary scenario: resume upload → question generation
- Failure scenario: text extraction failure

# 3. Functional Requirements

Include:

- PDF input handling
- Resume section parsing
- Signal extraction (skills, projects, keywords)
- Interview question generation (15 questions)
- Difficulty rating (1~5)
- Structured JSON output
- Markdown output

# 4. Non-Functional Requirements

Include:

- Privacy considerations (no raw resume logging)
- LLM output schema validation
- Error handling & retry
- Stateless default design

# 5. LangGraph Architecture Design

List required nodes:

- extract_text
- parse_sections
- extract_signals
- generate_questions
- rate_difficulty
- format_output

Describe:

- State design (raw_text, sections, signals, questions, markdown, errors)
- Linear pipeline for MVP
- Possible conditional branch for error handling

# 6. Data Model Design

Define structured interview question format:

- id
- category (tech | project | system | deep-dive)
- difficulty (1~5)
- question
- expected_points
- followups

# 7. MVP Definition of Done

Clearly define what counts as completed MVP.

# 8. Out of Scope (for MVP)

Explicitly list:

- OCR
- Vector DB / RAG
- Multi-agent system
- Mock interview answer evaluation

# 9. Development Phases

Phase 1: Schema & PDF extraction
Phase 2: Section parsing & signal extraction
Phase 3: Question generation & rating
Phase 4: API integration

====================================

Formatting Rules:

- Use clean markdown formatting
- Use clear headers
- No emojis
- No casual tone
- No unnecessary verbosity

Do not generate code.
Only generate the two markdown documents.

If docs/ directory does not exist, create it logically in output structure.

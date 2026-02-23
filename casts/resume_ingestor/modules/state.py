"""State schemas for the Resume Ingestor graph.

Official document URL:
    - State: https://docs.langchain.com/oss/python/langgraph/graph-api#state
"""

from langgraph.graph import MessagesState
from typing_extensions import NotRequired, TypedDict


class ResumeSectionMap(TypedDict):
    """Parsed resume sections used by downstream nodes."""

    summary: NotRequired[str]
    skills: NotRequired[str]
    experience: NotRequired[str]
    projects: NotRequired[str]
    education: NotRequired[str]


class ResumeSignals(TypedDict):
    """Normalized interview signals extracted from resume content."""

    skills: list[str]
    projects: list[str]
    keywords: list[str]
    evidence: list[str]


class InterviewQuestion(TypedDict):
    """Structured question model for InterviewGraph output."""

    id: str
    category: str
    difficulty: int
    question: str
    expected_points: list[str]
    followups: list[str]


class ErrorItem(TypedDict):
    """Node-level error payload for safe API responses."""

    node: str
    code: str
    message: str
    retryable: bool


class InputState(TypedDict):
    """Input schema for graph invocation."""

    resume_path: NotRequired[str]
    resume_text: NotRequired[str]


class OutputState(TypedDict):
    """Output schema for graph responses."""

    questions: list[InterviewQuestion]
    markdown: str
    errors: list[ErrorItem]
    generation_mode: str
    generation_reason: str


class State(MessagesState):
    """Full graph state passed between nodes."""

    resume_path: str | None
    resume_text: str | None
    raw_text: str
    sections: ResumeSectionMap
    signals: ResumeSignals
    questions: list[InterviewQuestion]
    markdown: str
    errors: list[ErrorItem]
    generation_mode: str
    generation_reason: str

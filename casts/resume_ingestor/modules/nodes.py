"""Node implementations for the Resume Ingestor graph."""

from __future__ import annotations

from pathlib import Path

from casts.base_node import BaseNode


def _error_item(
    node: str, code: str, message: str, retryable: bool
) -> dict[str, object]:
    return {
        "node": node,
        "code": code,
        "message": message,
        "retryable": retryable,
    }


class ExtractTextNode(BaseNode):
    """Phase 1 node that loads raw resume text from input.

    MVP behavior:
    - Uses `resume_text` directly when provided.
    - Falls back to reading text from `resume_path`.
    - Returns structured error metadata when extraction cannot proceed.
    """

    def execute(self, state):
        resume_text = state.get("resume_text")
        resume_path = state.get("resume_path")

        if isinstance(resume_text, str) and resume_text.strip():
            return {
                "raw_text": resume_text.strip(),
                "sections": {},
                "signals": {"skills": [], "projects": [], "keywords": []},
                "questions": [],
                "markdown": "",
                "errors": [],
            }

        if isinstance(resume_path, str) and resume_path.strip():
            path = Path(resume_path)
            if not path.exists() or not path.is_file():
                return {
                    "raw_text": "",
                    "sections": {},
                    "signals": {"skills": [], "projects": [], "keywords": []},
                    "questions": [],
                    "markdown": "",
                    "errors": [
                        _error_item(
                            node="extract_text",
                            code="FILE_NOT_FOUND",
                            message="Provided resume_path does not exist.",
                            retryable=False,
                        )
                    ],
                }

            try:
                loaded_text = path.read_text(encoding="utf-8").strip()
            except OSError:
                return {
                    "raw_text": "",
                    "sections": {},
                    "signals": {"skills": [], "projects": [], "keywords": []},
                    "questions": [],
                    "markdown": "",
                    "errors": [
                        _error_item(
                            node="extract_text",
                            code="READ_FAILED",
                            message="Failed to read resume_path as UTF-8 text.",
                            retryable=True,
                        )
                    ],
                }

            if not loaded_text:
                return {
                    "raw_text": "",
                    "sections": {},
                    "signals": {"skills": [], "projects": [], "keywords": []},
                    "questions": [],
                    "markdown": "",
                    "errors": [
                        _error_item(
                            node="extract_text",
                            code="EMPTY_TEXT",
                            message="No text content was extracted from resume input.",
                            retryable=True,
                        )
                    ],
                }

            return {
                "raw_text": loaded_text,
                "sections": {},
                "signals": {"skills": [], "projects": [], "keywords": []},
                "questions": [],
                "markdown": "",
                "errors": [],
            }

        return {
            "raw_text": "",
            "sections": {},
            "signals": {"skills": [], "projects": [], "keywords": []},
            "questions": [],
            "markdown": "",
            "errors": [
                _error_item(
                    node="extract_text",
                    code="MISSING_INPUT",
                    message="Provide either resume_text or resume_path.",
                    retryable=False,
                )
            ],
        }

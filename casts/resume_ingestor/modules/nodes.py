"""Node implementations for the Resume Ingestor graph."""

from __future__ import annotations

import re
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


class ParseSectionsNode(BaseNode):
    """Phase 2 node that maps raw resume text to logical sections."""

    _HEADER_MAP: dict[str, str] = {
        "summary": "summary",
        "profile": "summary",
        "about": "summary",
        "skills": "skills",
        "technical skills": "skills",
        "experience": "experience",
        "work experience": "experience",
        "professional experience": "experience",
        "projects": "projects",
        "project": "projects",
        "education": "education",
        "academic background": "education",
    }

    _EXPECTED_SECTIONS: tuple[str, ...] = (
        "summary",
        "skills",
        "experience",
        "projects",
        "education",
    )

    def execute(self, state):
        raw_text = state.get("raw_text")
        existing_errors = list(state.get("errors", []))

        if existing_errors:
            return {"sections": {}}

        if not isinstance(raw_text, str) or not raw_text.strip():
            return {
                "sections": {},
                "errors": existing_errors
                + [
                    _error_item(
                        node="parse_sections",
                        code="MISSING_RAW_TEXT",
                        message="Cannot parse sections without raw_text.",
                        retryable=False,
                    )
                ],
            }

        section_buffers: dict[str, list[str]] = {
            key: [] for key in self._EXPECTED_SECTIONS
        }
        current_section = "summary"

        for line in raw_text.splitlines():
            cleaned = line.strip()
            if not cleaned:
                continue

            normalized_header = re.sub(r"[:\-]+$", "", cleaned).strip().lower()
            if normalized_header in self._HEADER_MAP:
                current_section = self._HEADER_MAP[normalized_header]
                continue

            section_buffers[current_section].append(cleaned)

        parsed_sections = {
            name: "\n".join(lines).strip()
            for name, lines in section_buffers.items()
            if lines
        }

        return {"sections": parsed_sections}

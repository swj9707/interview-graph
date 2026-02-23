"""Node implementations for the Resume Ingestor graph."""

from __future__ import annotations

import re
from collections import Counter
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


class ExtractSignalsNode(BaseNode):
    """Phase 2 node that extracts skills, projects, and keywords from sections."""

    _STOPWORDS: set[str] = {
        "a",
        "an",
        "and",
        "as",
        "at",
        "be",
        "by",
        "for",
        "from",
        "in",
        "into",
        "is",
        "of",
        "on",
        "or",
        "the",
        "to",
        "with",
        "using",
        "years",
        "year",
        "experience",
    }

    def execute(self, state):
        existing_errors = list(state.get("errors", []))
        if existing_errors:
            return {"signals": {"skills": [], "projects": [], "keywords": []}}

        sections = state.get("sections")
        if not isinstance(sections, dict) or not sections:
            return {
                "signals": {"skills": [], "projects": [], "keywords": []},
                "errors": existing_errors
                + [
                    _error_item(
                        node="extract_signals",
                        code="MISSING_SECTIONS",
                        message="Cannot extract signals without parsed sections.",
                        retryable=False,
                    )
                ],
            }

        skills = self._extract_skills(sections.get("skills", ""))
        projects = self._extract_projects(sections.get("projects", ""))
        keywords = self._extract_keywords(sections)

        return {
            "signals": {
                "skills": skills,
                "projects": projects,
                "keywords": keywords,
            }
        }

    def _extract_skills(self, text: str) -> list[str]:
        if not isinstance(text, str) or not text.strip():
            return []
        normalized = text.replace("\n", ",")
        candidates = [part.strip(" -\t") for part in normalized.split(",")]
        return self._dedupe([token for token in candidates if token])

    def _extract_projects(self, text: str) -> list[str]:
        if not isinstance(text, str) or not text.strip():
            return []
        lines = [line.strip(" -*\t") for line in text.splitlines()]
        candidates = [line for line in lines if line]
        return self._dedupe(candidates)

    def _extract_keywords(self, sections: dict[str, object]) -> list[str]:
        corpus = " ".join(
            str(value) for value in sections.values() if isinstance(value, str)
        ).lower()
        tokens = re.findall(r"[a-zA-Z][a-zA-Z0-9+#.-]{1,}", corpus)
        filtered = [token for token in tokens if token not in self._STOPWORDS]

        ranked = Counter(filtered)
        # Deterministic ordering: highest frequency first, then lexical.
        sorted_tokens = sorted(ranked.items(), key=lambda item: (-item[1], item[0]))
        return [token for token, _count in sorted_tokens[:12]]

    def _dedupe(self, values: list[str]) -> list[str]:
        seen: set[str] = set()
        deduped: list[str] = []
        for value in values:
            key = value.lower()
            if key in seen:
                continue
            seen.add(key)
            deduped.append(value)
        return deduped


class GenerateQuestionsNode(BaseNode):
    """Phase 3 node that creates 15 structured interview questions."""

    _CATEGORIES: tuple[str, ...] = ("tech", "project", "system", "deep-dive")

    def execute(self, state):
        existing_errors = list(state.get("errors", []))
        if existing_errors:
            return {"questions": []}

        signals = state.get("signals")
        if not isinstance(signals, dict):
            return {
                "questions": [],
                "errors": existing_errors
                + [
                    _error_item(
                        node="generate_questions",
                        code="MISSING_SIGNALS",
                        message="Cannot generate questions without extracted signals.",
                        retryable=False,
                    )
                ],
            }

        skills = self._as_list(signals.get("skills"))
        projects = self._as_list(signals.get("projects"))
        keywords = self._as_list(signals.get("keywords"))

        prompts = self._build_prompt_seeds(skills, projects, keywords)
        questions = [
            self._make_question(index=idx + 1, seed=seed)
            for idx, seed in enumerate(prompts[:15])
        ]
        return {"questions": questions}

    def _as_list(self, value: object) -> list[str]:
        if not isinstance(value, list):
            return []
        return [item for item in value if isinstance(item, str) and item.strip()]

    def _build_prompt_seeds(
        self, skills: list[str], projects: list[str], keywords: list[str]
    ) -> list[tuple[str, str]]:
        seeds: list[tuple[str, str]] = []

        for skill in skills:
            seeds.append(("tech", f"{skill}"))
            seeds.append(("system", f"{skill}"))

        for project in projects:
            seeds.append(("project", f"{project}"))
            seeds.append(("deep-dive", f"{project}"))

        for keyword in keywords:
            seeds.append(("deep-dive", f"{keyword}"))

        if not seeds:
            seeds = [
                ("tech", "core backend skills"),
                ("project", "recent project ownership"),
                ("system", "service architecture"),
                ("deep-dive", "engineering trade-offs"),
            ]

        while len(seeds) < 15:
            seeds.extend(seeds)
        return seeds

    def _make_question(self, index: int, seed: tuple[str, str]) -> dict[str, object]:
        category, topic = seed
        prompt_map = {
            "tech": f"How have you applied {topic} in production, and what limitations did you face?",
            "project": f"Walk through the project '{topic}' and explain your personal contribution.",
            "system": f"If you redesign a system centered on {topic}, what architecture would you choose and why?",
            "deep-dive": f"Describe a hard technical decision involving {topic} and how you validated it.",
        }
        question_text = prompt_map.get(
            category,
            f"Explain your practical experience with {topic} and key outcomes.",
        )

        return {
            "id": f"q{index:02d}",
            "category": category if category in self._CATEGORIES else "tech",
            "difficulty": 0,
            "question": question_text,
            "expected_points": [
                "Problem context and constraints",
                "Technical choices and trade-offs",
                "Measured outcome and lessons learned",
            ],
            "followups": [
                "What would you do differently now?",
                "How did you measure success for this decision?",
            ],
        }


class RateDifficultyNode(BaseNode):
    """Phase 3 node that assigns 1-5 difficulty ratings to questions."""

    _CATEGORY_BASE: dict[str, int] = {
        "tech": 2,
        "project": 3,
        "system": 4,
        "deep-dive": 4,
    }

    def execute(self, state):
        existing_errors = list(state.get("errors", []))
        if existing_errors:
            return {"questions": []}

        questions = state.get("questions")
        if not isinstance(questions, list) or not questions:
            return {
                "questions": [],
                "errors": existing_errors
                + [
                    _error_item(
                        node="rate_difficulty",
                        code="MISSING_QUESTIONS",
                        message="Cannot rate difficulty without generated questions.",
                        retryable=False,
                    )
                ],
            }

        rated_questions: list[dict[str, object]] = []
        for index, question in enumerate(questions):
            if not isinstance(question, dict):
                continue

            category = str(question.get("category", "tech"))
            base = self._CATEGORY_BASE.get(category, 3)
            variation = index % 3
            difficulty = max(1, min(5, base - 1 + variation))

            updated = dict(question)
            updated["difficulty"] = difficulty
            rated_questions.append(updated)

        return {"questions": rated_questions}


class ValidateQuestionsNode(BaseNode):
    """Quality gate for generated questions before formatting output."""

    _CATEGORY_BASE: dict[str, int] = {
        "tech": 2,
        "project": 3,
        "system": 4,
        "deep-dive": 4,
    }

    def execute(self, state):
        existing_errors = list(state.get("errors", []))
        if existing_errors:
            questions = state.get("questions")
            return {"questions": questions if isinstance(questions, list) else []}

        questions = state.get("questions")
        if not isinstance(questions, list):
            return {
                "questions": [],
                "errors": existing_errors
                + [
                    _error_item(
                        node="validate_questions",
                        code="INVALID_QUESTIONS",
                        message="Questions payload is not a list.",
                        retryable=False,
                    )
                ],
            }

        typed_questions = [item for item in questions if isinstance(item, dict)]
        if not typed_questions:
            return {
                "questions": [],
                "errors": existing_errors
                + [
                    _error_item(
                        node="validate_questions",
                        code="EMPTY_QUESTIONS",
                        message="No questions available for quality validation.",
                        retryable=False,
                    )
                ],
            }

        evidence_terms = self._extract_evidence_terms(state.get("signals"))

        deduped_questions: list[dict[str, object]] = []
        seen_questions: set[str] = set()
        duplicate_count = 0
        for question in typed_questions:
            normalized = self._normalize_text(str(question.get("question", "")))
            if not normalized:
                duplicate_count += 1
                continue
            if normalized in seen_questions:
                duplicate_count += 1
                continue
            seen_questions.add(normalized)
            deduped_questions.append(dict(question))

        generic_count = 0
        for idx, question in enumerate(deduped_questions):
            if self._is_generic_question(
                str(question.get("question", "")), evidence_terms
            ):
                generic_count += 1
                topic = (
                    evidence_terms[idx % len(evidence_terms)]
                    if evidence_terms
                    else "your recent resume experience"
                )
                category = str(question.get("category", "tech"))
                question["question"] = self._build_contextual_question(category, topic)

        fill_count = max(0, 15 - len(deduped_questions))
        if fill_count:
            deduped_questions.extend(
                self._build_fallback_questions(fill_count, evidence_terms)
            )

        validated_questions = deduped_questions[:15]
        validated_questions = [
            self._normalize_question(index + 1, question)
            for index, question in enumerate(validated_questions)
        ]

        distribution_issue = self._distribution_issue(validated_questions)

        notes: list[str] = []
        if duplicate_count:
            notes.append(f"removed {duplicate_count} duplicate/empty questions")
        if generic_count:
            notes.append(f"rewrote {generic_count} generic questions")
        if fill_count:
            notes.append(f"added {fill_count} fallback questions")
        if distribution_issue:
            notes.append(distribution_issue)

        return {"questions": validated_questions}

    def _normalize_text(self, text: str) -> str:
        normalized = re.sub(r"\s+", " ", text.strip().lower())
        return re.sub(r"[^a-z0-9 ]+", "", normalized)

    def _extract_evidence_terms(self, signals: object) -> list[str]:
        if not isinstance(signals, dict):
            return []

        merged: list[str] = []
        for key in ("skills", "projects", "keywords"):
            value = signals.get(key)
            if isinstance(value, list):
                merged.extend(
                    item.strip()
                    for item in value
                    if isinstance(item, str) and item.strip()
                )

        seen: set[str] = set()
        evidence: list[str] = []
        for item in merged:
            lowered = item.lower()
            if lowered in seen:
                continue
            seen.add(lowered)
            evidence.append(item)
        return evidence

    def _is_generic_question(self, question: str, evidence_terms: list[str]) -> bool:
        normalized_question = question.lower()
        if len(normalized_question.strip()) < 25:
            return True
        if not evidence_terms:
            return False

        return not any(term.lower() in normalized_question for term in evidence_terms)

    def _build_contextual_question(self, category: str, topic: str) -> str:
        prompts = {
            "tech": f"When applying {topic}, what production constraints shaped your implementation choices?",
            "project": f"In your project work on {topic}, what outcome did you own directly and how did you deliver it?",
            "system": f"If scaling a system around {topic}, what architecture trade-offs would you prioritize and why?",
            "deep-dive": f"Describe the hardest technical trade-off you made involving {topic}, including validation steps and impact.",
        }
        return prompts.get(
            category,
            f"Describe a concrete engineering decision you made involving {topic} and the resulting impact.",
        )

    def _build_fallback_questions(
        self, count: int, evidence_terms: list[str]
    ) -> list[dict[str, object]]:
        categories = ("tech", "project", "system", "deep-dive")
        fallback: list[dict[str, object]] = []

        for idx in range(count):
            category = categories[idx % len(categories)]
            topic = (
                evidence_terms[idx % len(evidence_terms)]
                if evidence_terms
                else "your recent engineering work"
            )
            fallback.append(
                {
                    "id": "",
                    "category": category,
                    "difficulty": self._CATEGORY_BASE[category],
                    "question": self._build_contextual_question(category, topic),
                    "expected_points": [
                        "Specific context from the resume",
                        "Decision rationale and trade-offs",
                        "Measured outcomes and lessons learned",
                    ],
                    "followups": [
                        "What risks did you consider?",
                        "How would you improve this approach now?",
                    ],
                }
            )

        return fallback

    def _normalize_question(
        self, index: int, question: dict[str, object]
    ) -> dict[str, object]:
        normalized = dict(question)
        category = str(normalized.get("category", "tech"))
        if category not in self._CATEGORY_BASE:
            category = "tech"
        normalized["category"] = category

        difficulty = normalized.get("difficulty", self._CATEGORY_BASE[category])
        if not isinstance(difficulty, int) or not 1 <= difficulty <= 5:
            difficulty = self._CATEGORY_BASE[category]
        normalized["difficulty"] = difficulty

        normalized["id"] = f"q{index:02d}"

        expected_points = normalized.get("expected_points")
        if not isinstance(expected_points, list) or not expected_points:
            normalized["expected_points"] = [
                "Specific context from the resume",
                "Technical rationale and trade-offs",
                "Outcome and retrospective insight",
            ]

        followups = normalized.get("followups")
        if not isinstance(followups, list) or not followups:
            normalized["followups"] = [
                "What constraints most influenced your decision?",
                "What would you change if rebuilding this today?",
            ]

        if (
            not isinstance(normalized.get("question"), str)
            or not str(normalized.get("question", "")).strip()
        ):
            normalized["question"] = self._build_contextual_question(
                category, "your recent engineering work"
            )

        return normalized

    def _distribution_issue(self, questions: list[dict[str, object]]) -> str | None:
        categories = [str(item.get("category", "tech")) for item in questions]
        unique_categories = set(categories)
        if len(unique_categories) < 3:
            return "category distribution is narrow"

        difficult_values = [
            self._safe_difficulty_value(item.get("difficulty")) for item in questions
        ]
        if max(difficult_values) - min(difficult_values) < 2:
            return "difficulty spread is too small"

        return None

    def _safe_difficulty_value(self, value: object) -> int:
        if isinstance(value, int):
            return max(1, min(5, value))
        if isinstance(value, str) and value.isdigit():
            return max(1, min(5, int(value)))
        return 1


class FormatOutputNode(BaseNode):
    """Final node that renders markdown from structured questions."""

    def execute(self, state):
        questions = state.get("questions")
        errors = state.get("errors")

        if not isinstance(errors, list):
            errors = []

        if not isinstance(questions, list):
            return {
                "questions": [],
                "markdown": "",
                "errors": errors
                + [
                    _error_item(
                        node="format_output",
                        code="INVALID_QUESTIONS",
                        message="Questions payload is not a list.",
                        retryable=False,
                    )
                ],
            }

        markdown = self._render_markdown(questions)
        return {"questions": questions, "markdown": markdown}

    def _render_markdown(self, questions: list[object]) -> str:
        lines: list[str] = ["# Interview Questions", ""]

        for item in questions:
            if not isinstance(item, dict):
                continue

            question_id = str(item.get("id", ""))
            category = str(item.get("category", "tech"))
            difficulty = item.get("difficulty", "N/A")
            question_text = str(item.get("question", ""))
            expected_points = item.get("expected_points", [])
            followups = item.get("followups", [])

            lines.append(f"## {question_id} [{category}] (Difficulty: {difficulty})")
            lines.append(question_text)

            lines.append("")
            lines.append("Expected points:")
            if isinstance(expected_points, list) and expected_points:
                for point in expected_points:
                    lines.append(f"- {point}")
            else:
                lines.append("- N/A")

            lines.append("")
            lines.append("Follow-ups:")
            if isinstance(followups, list) and followups:
                for followup in followups:
                    lines.append(f"- {followup}")
            else:
                lines.append("- N/A")

            lines.append("")

        return "\n".join(lines).rstrip()

"""Query-complexity classifier for LiteLLM Gateway routing.

Analyses user input and decides which model group should handle
the request:
    fast-faq    — simple, single-intent queries (order status, FAQ, stock)
    deep-support— complex, multi-step, or ambiguous queries
"""

from __future__ import annotations

import re
import logging
from dataclasses import dataclass, field

from config.settings import LITELLM_FAST_MODEL, LITELLM_DEEP_MODEL

logger = logging.getLogger(__name__)

# -----------------------
# Route Decision
# -----------------------

@dataclass
class RouteDecision:
    """Result of the query-complexity classifier."""

    route_hint: str          # model-group name (e.g. "fast-faq")
    confidence: float        # 0.0 – 1.0
    reasoning: str           # human-readable explanation
    fallback_route: str = "" # model-group to try on failure


# -----------------------
# Keyword / pattern sets
# -----------------------

_SIMPLE_PATTERNS: list[re.Pattern[str]] = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"\border(?: status|s?)\b",
        r"\btrack(?:ing)?\b",
        r"\bwhere is my\b",
        r"\breturn policy\b",
        r"\brefund\b",
        r"\bwarranty\b",
        r"\bin stock\b",
        r"\bavailab(?:le|ility)\b",
        r"\bprice\b",
        r"\bspecs?\b",
        r"\bspecifications?\b",
        r"\bshipping\b",
        r"\bdelivery\b",
        r"\bpayment methods?\b",
        r"\bhow (?:do|can) I\b",
        r"\bcancel(?:lation)?\b",
        r"\bhi\b",
        r"\bhello\b",
        r"\bthanks?\b",
        r"\bthank you\b",
    ]
]

_COMPLEX_SIGNALS: list[re.Pattern[str]] = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"\bcompare\b",
        r"\bvs\.?\b",
        r"\bdifference between\b",
        r"\bbetter\b",
        r"\brecommend\b",
        r"\bsugg?est\b",
        r"\bcomplaint\b",
        r"\bescalat\w*\b",
        r"\bfrustrat\w*\b",
        r"\bangry\b",
        r"\bunhappy\b",
        r"\bdisappoint\w*\b",
        r"\bwrong item\b",
        r"\bdamaged\b",
        r"\bmissing\b",
        r"\bmultiple\b",
        r"\bbulk\b",
        r"\bwholesale\b",
        r"\bcustom\b",
        r"\bexplain\b",
        r"\bwhy\b",
    ]
]

# Threshold: messages above this word count lean toward deep-support.
_LENGTH_THRESHOLD = 40

# If more than this many question marks, likely a complex query.
_QUESTION_MARK_THRESHOLD = 2


# -----------------------
# Classifier
# -----------------------

def classify_query(user_input: str) -> RouteDecision:
    """Classify *user_input* and return a :class:`RouteDecision`.

    The classifier combines three heuristic signals:
        1. Pattern matching against known simple / complex phrases.
        2. Message length (word count).
        3. Punctuation density (question marks).
    """

    text = user_input.strip()
    if not text:
        return RouteDecision(
            route_hint=LITELLM_FAST_MODEL,
            confidence=1.0,
            reasoning="Empty input — defaulting to fast model.",
            fallback_route=LITELLM_DEEP_MODEL,
        )

    simple_hits = sum(1 for p in _SIMPLE_PATTERNS if p.search(text))
    complex_hits = sum(1 for p in _COMPLEX_SIGNALS if p.search(text))

    word_count = len(text.split())
    question_marks = text.count("?")

    # --- scoring ----------------------------------------------------------
    score = 0.0  # positive → deep, negative → fast

    # pattern balance
    score += (complex_hits - simple_hits) * 0.20

    # long messages skew complex
    if word_count > _LENGTH_THRESHOLD:
        score += 0.25

    # many question marks skew complex
    if question_marks > _QUESTION_MARK_THRESHOLD:
        score += 0.15

    # --- decision ---------------------------------------------------------
    if score >= 0.15:
        confidence = min(0.5 + abs(score), 1.0)
        return RouteDecision(
            route_hint=LITELLM_DEEP_MODEL,
            confidence=round(confidence, 2),
            reasoning=(
                f"Complex signal (score={score:+.2f}): "
                f"{complex_hits} complex hit(s), {simple_hits} simple hit(s), "
                f"{word_count} words, {question_marks} '?'."
            ),
            fallback_route=LITELLM_FAST_MODEL,
        )

    confidence = min(0.5 + abs(score), 1.0)
    return RouteDecision(
        route_hint=LITELLM_FAST_MODEL,
        confidence=round(confidence, 2),
        reasoning=(
            f"Simple signal (score={score:+.2f}): "
            f"{simple_hits} simple hit(s), {complex_hits} complex hit(s), "
            f"{word_count} words, {question_marks} '?'."
        ),
        fallback_route=LITELLM_DEEP_MODEL,
    )

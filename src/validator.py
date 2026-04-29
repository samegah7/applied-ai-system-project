"""
Automated validation of Claude's recommendation responses.

Three checks run after every generation:

  1. Grounding check  - did Claude mention at least one song from the retrieved list?
  2. Hallucination check - did Claude invent song titles not in the retrieved list?
     (looks for short quoted strings that are not retrieved song titles)
  3. Length sanity - is the response a reasonable paragraph (20-300 words)?

A confidence score (0.0-1.0) is derived from the three checks:
  grounding passes   -> +0.50
  no hallucinations  -> +0.30
  reasonable length  -> +0.20

A fourth check, consistency, is available separately and compares two responses
for the same profile to measure stability across runs.
"""

import re
from typing import TypedDict

from .logger import logger


class ValidationReport(TypedDict):
    profile: str
    passed: bool
    grounded: bool
    songs_mentioned: list[str]
    potential_hallucinations: list[str]
    word_count: int
    reasonable_length: bool


def validate_response(
    response: str,
    retrieved_songs: list[dict],
    profile_name: str = "Unknown",
) -> ValidationReport:
    """
    Validate a Claude response against the list of retrieved songs.
    Returns a ValidationReport dict and logs any issues found.
    """
    retrieved_titles = {s["title"] for s in retrieved_songs}

    # Check 1: Grounding — at least one retrieved song title appears in the response
    mentioned = [
        title for title in retrieved_titles if title.lower() in response.lower()
    ]
    is_grounded = len(mentioned) > 0

    # Check 2: Hallucination — quoted strings that look like song titles but
    # are not in the retrieved set (short: ≤7 words, not a common phrase)
    quoted = re.findall(r'"([^"]{3,60})"', response)
    hallucinated = [
        q for q in quoted
        if q not in retrieved_titles and len(q.split()) <= 7
    ]

    # Check 3: Length sanity
    word_count = len(response.split())
    is_reasonable_length = 20 <= word_count <= 300

    passed = is_grounded and not hallucinated and is_reasonable_length

    report: ValidationReport = {
        "profile": profile_name,
        "passed": passed,
        "grounded": is_grounded,
        "songs_mentioned": mentioned,
        "potential_hallucinations": hallucinated,
        "word_count": word_count,
        "reasonable_length": is_reasonable_length,
    }

    if passed:
        logger.info(
            f"[{profile_name}] Validation PASSED "
            f"(mentioned: {mentioned}, words: {word_count})"
        )
    else:
        if not is_grounded:
            logger.warning(
                f"[{profile_name}] Validation: response not grounded — "
                "no retrieved song titles found in output"
            )
        if hallucinated:
            logger.warning(
                f"[{profile_name}] Validation: possible hallucinations — {hallucinated}"
            )
        if not is_reasonable_length:
            logger.warning(
                f"[{profile_name}] Validation: unusual response length ({word_count} words)"
            )

    return report


def check_consistency(response_a: str, response_b: str, profile_name: str = "Unknown") -> float:
    """
    Rough consistency score between two responses for the same profile.
    Returns the Jaccard similarity of their word sets (0.0 = nothing in common,
    1.0 = identical vocabulary). Logs the result.

    Used when running a profile twice to measure output stability.
    """
    words_a = set(response_a.lower().split())
    words_b = set(response_b.lower().split())
    if not words_a and not words_b:
        return 1.0
    score = round(len(words_a & words_b) / len(words_a | words_b), 3)
    logger.info(f"[{profile_name}] Consistency score: {score:.3f} (Jaccard word overlap)")
    return score


def confidence_score(report: ValidationReport) -> float:
    """
    Numeric reliability score for a single response (0.0-1.0).
      +0.50 if grounded (response references at least one retrieved song)
      +0.30 if no hallucinated titles detected
      +0.20 if response length is in the expected range
    """
    score = 0.0
    if report["grounded"]:
        score += 0.50
    if not report["potential_hallucinations"]:
        score += 0.30
    if report["reasonable_length"]:
        score += 0.20
    return round(score, 2)


def format_report(report: ValidationReport) -> str:
    status = "PASSED" if report["passed"] else "FAILED"
    confidence = confidence_score(report)
    mentioned = ", ".join(report["songs_mentioned"]) or "none"
    issues = []
    if not report["grounded"]:
        issues.append("not grounded")
    if report["potential_hallucinations"]:
        issues.append(f"possible hallucinations: {report['potential_hallucinations']}")
    if not report["reasonable_length"]:
        issues.append(f"unusual length ({report['word_count']} words)")
    issue_str = " | ".join(issues) if issues else "none"
    return (
        f"  Validation : {status}  |  confidence: {confidence:.2f}"
        f"  |  songs mentioned: {mentioned}"
        + (f"  |  issues: {issue_str}" if issues else "")
    )

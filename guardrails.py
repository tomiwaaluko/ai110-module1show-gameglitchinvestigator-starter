"""
Guardrails: input validation, output sanitization, and rate limiting
for the AI Game Intelligence System.
"""

import re
import time
from typing import Optional


_last_call_times: list[float] = []
MAX_CALLS_PER_MINUTE = 20


def validate_guess(raw: str, low: int, high: int) -> tuple[bool, Optional[int], Optional[str]]:
    """
    Validate a raw guess string.

    Returns: (is_valid, guess_int, error_message)
    """
    if not raw or not raw.strip():
        return False, None, "Please enter a number before submitting."

    cleaned = raw.strip()

    if len(cleaned) > 20:
        return False, None, "Input too long. Please enter a valid number."

    if not re.match(r"^-?\d+(\.\d+)?$", cleaned):
        return False, None, f"'{cleaned}' is not a valid number. Please enter digits only."

    try:
        if "." in cleaned:
            guess_int = int(float(cleaned))
        else:
            guess_int = int(cleaned)
    except ValueError:
        return False, None, "Could not parse that as a number."

    if guess_int < low or guess_int > high:
        return False, None, f"Your guess must be between {low} and {high}."

    return True, guess_int, None


def sanitize_ai_response(response: str, max_length: int = 500) -> str:
    """
    Sanitize AI response before display:
    - Truncate to max length
    - Strip dangerous content patterns
    - Ensure non-empty fallback
    """
    if not response or not response.strip():
        return "Keep using binary search - always guess the midpoint of your remaining range."

    sanitized = re.sub(
        r"(ignore|forget|disregard)\s+(previous|all|prior)",
        "",
        response,
        flags=re.IGNORECASE,
    )

    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length].rsplit(" ", 1)[0] + "..."

    return sanitized.strip()


def check_rate_limit() -> tuple[bool, Optional[str]]:
    """
    Check if we are within rate limits for AI API calls.

    Returns: (is_allowed, error_message)
    """
    global _last_call_times
    now = time.time()

    _last_call_times = [t for t in _last_call_times if now - t < 60]

    if len(_last_call_times) >= MAX_CALLS_PER_MINUTE:
        return False, f"Rate limit reached ({MAX_CALLS_PER_MINUTE} AI calls/minute). Please wait a moment."

    _last_call_times.append(now)
    return True, None


def validate_game_state(attempts: int, attempt_limit: int, status: str) -> tuple[bool, Optional[str]]:
    """Validate that the game state is coherent before processing a guess."""
    if status != "playing":
        return False, "Game is not active. Start a new game."
    if attempts < 0:
        return False, "Invalid attempt count."
    if attempts >= attempt_limit:
        return False, "No attempts remaining."
    return True, None

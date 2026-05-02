"""
Logger: structured JSONL session logger for the AI Game Intelligence System.
Records all game events and AI coaching interactions for evaluation.
"""

import json
import os
from datetime import datetime


LOG_FILE = os.path.join(os.path.dirname(__file__), "game_session_log.jsonl")


def log_event(event_type: str, data: dict) -> None:
    """
    Append a structured event to the JSONL log file.

    Event types: game_start, guess_submitted, ai_coaching, game_end, error
    """
    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "event_type": event_type,
        **data,
    }
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass


def log_game_start(difficulty: str, low: int, high: int, attempt_limit: int) -> None:
    log_event(
        "game_start",
        {
            "difficulty": difficulty,
            "range_low": low,
            "range_high": high,
            "attempt_limit": attempt_limit,
        },
    )


def log_guess(guess: int, outcome: str, attempt_number: int, score: int) -> None:
    log_event(
        "guess_submitted",
        {
            "guess": guess,
            "outcome": outcome,
            "attempt_number": attempt_number,
            "current_score": score,
        },
    )


def log_ai_coaching(
    guess: int,
    outcome: str,
    coaching_tip: str,
    confidence: float,
    reasoning_steps: list[str],
    rag_sources: list[str],
    latency_ms: int,
) -> None:
    log_event(
        "ai_coaching",
        {
            "guess": guess,
            "outcome": outcome,
            "coaching_tip": coaching_tip,
            "confidence_score": confidence,
            "reasoning_steps": reasoning_steps,
            "rag_sources_used": rag_sources,
            "api_latency_ms": latency_ms,
        },
    )


def log_game_end(status: str, final_score: int, total_attempts: int, secret: int) -> None:
    log_event(
        "game_end",
        {
            "status": status,
            "final_score": final_score,
            "total_attempts": total_attempts,
            "secret_was": secret,
        },
    )


def log_error(component: str, error_message: str) -> None:
    log_event(
        "error",
        {
            "component": component,
            "error": error_message,
        },
    )


def read_recent_events(n: int = 20) -> list[dict]:
    """Read the most recent N events from the log."""
    if not os.path.exists(LOG_FILE):
        return []
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
        events = []
        for line in lines[-n:]:
            try:
                events.append(json.loads(line.strip()))
            except json.JSONDecodeError:
                pass
        return events
    except Exception:
        return []

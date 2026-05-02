"""
AI Coach: Agentic workflow engine for the Game Glitch Investigator.

The agent runs a 5-step reasoning chain on every guess:
  Step 1: ANALYZE   - evaluate guess efficiency vs. binary search optimal
  Step 2: RETRIEVE  - fetch relevant strategy chunks from RAG knowledge base
  Step 3: PLAN      - compute optimal next guess and calculate confidence
  Step 4: ADVISE    - call Gemini API with few-shot specialized prompt
  Step 5: VALIDATE  - guardrail-check the response before returning

Returns a structured CoachResult with tip, confidence, and reasoning trace.
"""

import os
import time
from dataclasses import dataclass, field
from typing import Optional

import google.generativeai as genai
from dotenv import load_dotenv

from guardrails import check_rate_limit, sanitize_ai_response
from logger import log_ai_coaching, log_error
from rag_retriever import retrieve


load_dotenv()

SYSTEM_PROMPT = """You are Coach Binary, an expert AI game coach specializing in number-guessing strategy and binary search optimization. You are embedded in the "Game Glitch Investigator" educational app.

Your coaching style:
- Direct and specific: always tell the player their exact optimal next guess
- Encouraging but honest: acknowledge mistakes without being harsh
- Educational: briefly explain WHY binary search works when relevant
- Concise: responses must be 2-4 sentences maximum

Examples of good coaching responses:

Player guessed 75, range was 1-100, secret was lower:
"Good instinct starting near the top! Since the secret is lower than 75, your new range is 1-74. The optimal next guess is 37 - exactly the midpoint of that range. Binary search cuts your search space in half every time."

Player guessed 40, range was 1-100, optimal was 50:
"You're close to optimal - 50 would have been the perfect midpoint of your 1-100 range. Still, 40 leaves a workable range. Next, guess 20 if told 'Too Low', or 64 if told 'Too High'. Always split what's left."

Player has only 1 attempt left:
"This is your last chance - don't guess randomly! Based on your remaining range, your best guess is the midpoint. Make it count."

You always end your response with the player's single most important action: what number to guess next if they can."""


@dataclass
class CoachResult:
    """Structured output from the AI coaching agent."""

    tip: str
    confidence: float
    reasoning_trace: list[str] = field(default_factory=list)
    rag_sources: list[str] = field(default_factory=list)
    optimal_next_guess: Optional[int] = None
    error: Optional[str] = None


def _step1_analyze(
    guess: int,
    outcome: str,
    history: list,
    low: int,
    high: int,
    attempts_left: int,
) -> dict:
    """
    Step 1: ANALYZE
    Evaluate the player's guess against the binary search optimal.
    Returns analysis context dict.
    """
    optimal = low + (high - low) // 2
    deviation = abs(guess - optimal)
    range_size = high - low + 1

    if deviation == 0:
        efficiency = "perfect"
    elif deviation <= range_size * 0.1:
        efficiency = "good"
    elif deviation <= range_size * 0.25:
        efficiency = "average"
    else:
        efficiency = "poor"

    numeric_history = [item for item in history if isinstance(item, int)]
    if len(numeric_history) >= 2:
        diffs = [abs(numeric_history[i] - numeric_history[i - 1]) for i in range(1, len(numeric_history))]
        avg_diff = sum(diffs) / len(diffs)
        if avg_diff < range_size * 0.1:
            strategy_detected = "linear_search"
        elif avg_diff >= range_size * 0.3:
            strategy_detected = "binary_search"
        else:
            strategy_detected = "mixed"
    else:
        strategy_detected = "unknown"

    urgency = "critical" if attempts_left <= 2 else "normal"

    return {
        "guess": guess,
        "outcome": outcome,
        "optimal_guess": optimal,
        "deviation": deviation,
        "efficiency": efficiency,
        "strategy_detected": strategy_detected,
        "range_size": range_size,
        "attempts_left": attempts_left,
        "urgency": urgency,
    }


def _step2_retrieve(analysis: dict) -> tuple[list[dict], list[str]]:
    """
    Step 2: RETRIEVE
    Query the RAG knowledge base for relevant strategy context.
    Returns (chunks, source_names).
    """
    query_parts = [f"number guessing game strategy {analysis['outcome'].lower()}"]

    if analysis["efficiency"] == "poor" or analysis["strategy_detected"] == "linear_search":
        query_parts.append("binary search midpoint strategy inefficient guessing")
    if analysis["urgency"] == "critical":
        query_parts.append("last attempt urgent guessing strategy")
    if analysis["outcome"] == "Win":
        query_parts.append("winning strategy efficiency scoring")

    query = " ".join(query_parts)
    chunks = retrieve(query, n_results=3)
    sources = list({c["source"] for c in chunks if c.get("source") != "error"})

    return chunks, sources


def _step3_plan(analysis: dict, current_low: int, current_high: int) -> tuple[int, float]:
    """
    Step 3: PLAN
    Compute the optimal next guess and a confidence score.
    Confidence is based on remaining attempts vs. remaining range size.
    Returns (optimal_next_guess, confidence_score).
    """
    import math

    guess = analysis["guess"]
    outcome = analysis["outcome"]

    if outcome == "Too High":
        new_low, new_high = current_low, guess - 1
    elif outcome == "Too Low":
        new_low, new_high = guess + 1, current_high
    else:
        new_low, new_high = guess, guess

    if new_low > new_high:
        optimal_next = guess
        confidence = 1.0
    else:
        optimal_next = new_low + (new_high - new_low) // 2
        remaining_range = new_high - new_low + 1
        attempts_left = analysis["attempts_left"]

        if attempts_left <= 0:
            confidence = 0.0
        else:
            guesses_needed = math.ceil(math.log2(remaining_range + 1)) if remaining_range > 1 else 1
            if guesses_needed <= attempts_left:
                confidence = min(
                    1.0,
                    0.7 + 0.3 * (attempts_left - guesses_needed) / max(attempts_left, 1),
                )
            else:
                confidence = max(0.1, attempts_left / guesses_needed * 0.6)

    return optimal_next, round(confidence, 2)


def _step4_advise(analysis: dict, rag_chunks: list[dict], optimal_next: int, confidence: float) -> str:
    """
    Step 4: ADVISE
    Call Gemini API with the few-shot specialized prompt and structured context.
    Returns coaching tip string.
    """
    is_allowed, rate_error = check_rate_limit()
    if not is_allowed:
        return f"[Rate limited] {rate_error} Tip: always guess the midpoint of your remaining range."

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return (
            "AI coaching unavailable (no API key set). "
            f"Tip: Optimal next guess is {optimal_next}. "
            "Always guess the midpoint of your remaining range."
        )

    rag_context = "\n\n".join(
        f"[From {c['source']}]: {c['text'][:400]}"
        for c in rag_chunks[:2]
        if c.get("text") and "error" not in c.get("source", "")
    )

    full_prompt = f"""{SYSTEM_PROMPT}

Current game situation:
- Player guessed: {analysis['guess']}
- Outcome: {analysis['outcome']}
- Guess efficiency vs. binary search optimal: {analysis['efficiency']} (optimal was {analysis['optimal_guess']}, deviation: {analysis['deviation']})
- Strategy pattern detected: {analysis['strategy_detected']}
- Attempts remaining after this guess: {analysis['attempts_left']}
- Urgency level: {analysis['urgency']}
- Computed optimal next guess: {optimal_next}
- Win confidence: {confidence:.0%}

Relevant strategy knowledge:
{rag_context if rag_context else "Use binary search: always guess the midpoint."}

Provide a coaching tip for this player. Remember to end with their specific next recommended guess: {optimal_next}."""

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            generation_config=genai.GenerationConfig(max_output_tokens=200),
        )
        response = model.generate_content(full_prompt)
        return response.text
    except Exception as e:
        log_error("ai_coach._step4_advise", str(e))
        return f"API error. Tip: Optimal next guess is {optimal_next} - split your remaining range in half."


def _step5_validate(raw_tip: str, optimal_next: int) -> str:
    """
    Step 5: VALIDATE
    Sanitize the AI response and ensure the optimal next guess is mentioned.
    """
    sanitized = sanitize_ai_response(raw_tip, max_length=400)

    if str(optimal_next) not in sanitized and optimal_next > 0:
        sanitized += f" Your optimal next guess: {optimal_next}."

    return sanitized


def get_coaching(
    guess: int,
    outcome: str,
    history: list,
    low: int,
    high: int,
    attempts_left: int,
    difficulty: str,
) -> CoachResult:
    """
    Main entry point: run the 5-step agentic coaching workflow.

    Always returns a CoachResult. Failures are handled gracefully with
    fallback messages rather than exceptions.
    """
    reasoning_trace = []
    start_time = time.time()

    try:
        analysis = _step1_analyze(guess, outcome, history, low, high, attempts_left)
        reasoning_trace.append(
            f"[ANALYZE] Guess {guess} vs. optimal {analysis['optimal_guess']} - "
            f"efficiency: {analysis['efficiency']}, strategy: {analysis['strategy_detected']}, "
            f"urgency: {analysis['urgency']}"
        )

        rag_chunks, rag_sources = _step2_retrieve(analysis)
        reasoning_trace.append(
            f"[RETRIEVE] Fetched {len(rag_chunks)} chunks from RAG. "
            f"Sources: {', '.join(rag_sources) if rag_sources else 'none'}"
        )

        optimal_next, confidence = _step3_plan(analysis, low, high)
        reasoning_trace.append(
            f"[PLAN] Optimal next guess: {optimal_next}. Win confidence: {confidence:.0%}."
        )

        raw_tip = _step4_advise(analysis, rag_chunks, optimal_next, confidence)
        reasoning_trace.append(
            f"[ADVISE] Gemini API called with {len(rag_chunks)} RAG chunks as context."
        )

        final_tip = _step5_validate(raw_tip, optimal_next)
        reasoning_trace.append(
            f"[VALIDATE] Response sanitized and verified. Length: {len(final_tip)} chars."
        )

        latency_ms = int((time.time() - start_time) * 1000)
        log_ai_coaching(
            guess=guess,
            outcome=outcome,
            coaching_tip=final_tip,
            confidence=confidence,
            reasoning_steps=reasoning_trace,
            rag_sources=rag_sources,
            latency_ms=latency_ms,
        )

        return CoachResult(
            tip=final_tip,
            confidence=confidence,
            reasoning_trace=reasoning_trace,
            rag_sources=rag_sources,
            optimal_next_guess=optimal_next,
        )

    except Exception as e:
        error_msg = f"Agent failed: {e}"
        log_error("ai_coach.get_coaching", error_msg)
        return CoachResult(
            tip="Coaching unavailable. Always guess the midpoint of your remaining range.",
            confidence=0.5,
            reasoning_trace=reasoning_trace + [f"[ERROR] {error_msg}"],
            error=error_msg,
        )

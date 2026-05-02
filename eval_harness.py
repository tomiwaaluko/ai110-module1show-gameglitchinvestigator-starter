"""
Evaluation Harness: Automated test runner for the AI Game Intelligence System.
Stretch Goal (+2 pts): Runs predefined game scenarios and prints a scored summary.

Usage:
    python eval_harness.py

Does NOT require the Streamlit server or Gemini API to be running.
Tests: logic correctness, guardrails, RAG retrieval, analysis step, planning step.
"""

import sys
import time
from dataclasses import dataclass


@dataclass
class TestResult:
    name: str
    passed: bool
    confidence: float = 1.0
    notes: str = ""
    latency_ms: int = 0


def run_test(name: str, fn) -> TestResult:
    start = time.time()
    try:
        confidence, notes = fn()
        latency = int((time.time() - start) * 1000)
        return TestResult(name=name, passed=True, confidence=confidence, notes=notes, latency_ms=latency)
    except AssertionError as e:
        latency = int((time.time() - start) * 1000)
        return TestResult(name=name, passed=False, confidence=0.0, notes=str(e), latency_ms=latency)
    except Exception as e:
        latency = int((time.time() - start) * 1000)
        return TestResult(name=name, passed=False, confidence=0.0, notes=f"Exception: {e}", latency_ms=latency)


def test_check_guess_win():
    from logic_utils import check_guess

    result = check_guess(50, 50)
    assert result == "Win", f"Expected 'Win', got '{result}'"
    return 1.0, "check_guess(50, 50) == 'Win'"


def test_check_guess_too_high():
    from logic_utils import check_guess

    result = check_guess(75, 50)
    assert result == "Too High", f"Expected 'Too High', got '{result}'"
    return 1.0, "check_guess(75, 50) == 'Too High'"


def test_check_guess_too_low():
    from logic_utils import check_guess

    result = check_guess(25, 50)
    assert result == "Too Low", f"Expected 'Too Low', got '{result}'"
    return 1.0, "check_guess(25, 50) == 'Too Low'"


def test_get_range_easy():
    from logic_utils import get_range_for_difficulty

    low, high = get_range_for_difficulty("Easy")
    assert low == 1 and high == 20, f"Expected (1,20), got ({low},{high})"
    return 1.0, "Easy mode range is 1-20"


def test_get_range_normal():
    from logic_utils import get_range_for_difficulty

    low, high = get_range_for_difficulty("Normal")
    assert low == 1 and high == 100, f"Expected (1,100), got ({low},{high})"
    return 1.0, "Normal mode range is 1-100"


def test_get_range_hard():
    from logic_utils import get_range_for_difficulty

    low, high = get_range_for_difficulty("Hard")
    assert low == 1 and high == 500, f"Expected (1,500), got ({low},{high})"
    return 1.0, "Hard mode range is 1-500"


def test_score_win_first_attempt():
    from logic_utils import update_score

    score = update_score(0, "Win", 1)
    assert score == 90, f"Expected 90 (100 - 10*1), got {score}"
    return 1.0, "Win on attempt 1 gives score 90"


def test_score_too_high_penalty():
    from logic_utils import update_score

    score = update_score(0, "Too High", 1)
    assert score == -5, f"Expected -5, got {score}"
    return 1.0, "Too High gives -5 penalty"


def test_guardrail_valid_input():
    from guardrails import validate_guess

    ok, val, err = validate_guess("42", 1, 100)
    assert ok is True and val == 42
    return 1.0, "Valid input '42' accepted"


def test_guardrail_out_of_range():
    from guardrails import validate_guess

    ok, val, err = validate_guess("999", 1, 100)
    assert ok is False
    return 1.0, "Out-of-range '999' rejected"


def test_guardrail_text_input():
    from guardrails import validate_guess

    ok, val, err = validate_guess("banana", 1, 100)
    assert ok is False
    return 1.0, "Text input 'banana' rejected"


def test_analysis_perfect_guess():
    from ai_coach import _step1_analyze

    analysis = _step1_analyze(50, "Too High", [], 1, 100, 5)
    assert analysis["efficiency"] == "perfect"
    assert analysis["optimal_guess"] == 50
    return 1.0, "Perfect binary search guess detected"


def test_analysis_poor_guess():
    from ai_coach import _step1_analyze

    analysis = _step1_analyze(2, "Too Low", [], 1, 100, 5)
    assert analysis["efficiency"] == "poor"
    return 0.9, "Poor efficiency guess detected"


def test_plan_too_high_midpoint():
    from ai_coach import _step3_plan

    analysis = {"guess": 75, "outcome": "Too High", "attempts_left": 4}
    optimal, conf = _step3_plan(analysis, 1, 100)
    assert optimal == 37, f"Expected 37 (midpoint of 1-74), got {optimal}"
    return conf, "Optimal guess after Too High at 75 is 37"


def test_plan_too_low_midpoint():
    from ai_coach import _step3_plan

    analysis = {"guess": 25, "outcome": "Too Low", "attempts_left": 4}
    optimal, conf = _step3_plan(analysis, 1, 100)
    assert optimal == 63, f"Expected 63 (midpoint of 26-100), got {optimal}"
    return conf, "Optimal guess after Too Low at 25 is 63"


def test_rag_indexed():
    from rag_retriever import get_document_count

    count = get_document_count()
    assert count > 0, "RAG collection empty! Check data/ directory."
    return 1.0, f"RAG has {count} indexed document chunks"


def test_rag_retrieval_returns_results():
    from rag_retriever import retrieve

    results = retrieve("binary search midpoint strategy number guessing", n_results=2)
    assert len(results) >= 1
    assert len(results[0].get("text", "")) > 10
    return 1.0, f"RAG returned {len(results)} relevant chunks"


def test_binary_search_simulation():
    from logic_utils import check_guess, get_range_for_difficulty
    import random

    wins = 0
    total_games = 10
    total_guesses = 0

    for _ in range(total_games):
        low, high = get_range_for_difficulty("Normal")
        secret = random.randint(low, high)
        guesses = 0
        max_guesses = 8
        found = False

        while guesses < max_guesses:
            guess = low + (high - low) // 2
            guesses += 1
            result = check_guess(guess, secret)
            if result == "Win":
                wins += 1
                total_guesses += guesses
                found = True
                break
            if result == "Too High":
                high = guess - 1
            else:
                low = guess + 1

        if not found:
            total_guesses += guesses

    win_rate = wins / total_games
    avg_guesses = total_guesses / total_games

    assert wins == total_games, f"Binary search failed to win {total_games - wins} games!"
    assert avg_guesses <= 7, f"Average guesses {avg_guesses:.1f} exceeds 7 (log2(100))"

    return win_rate, f"Binary search won {wins}/{total_games} games in avg {avg_guesses:.1f} guesses"


ALL_TESTS = [
    ("Logic: check_guess win", test_check_guess_win),
    ("Logic: check_guess too high", test_check_guess_too_high),
    ("Logic: check_guess too low", test_check_guess_too_low),
    ("Logic: range Easy", test_get_range_easy),
    ("Logic: range Normal", test_get_range_normal),
    ("Logic: range Hard", test_get_range_hard),
    ("Logic: score win first attempt", test_score_win_first_attempt),
    ("Logic: score Too High penalty", test_score_too_high_penalty),
    ("Guardrail: valid input", test_guardrail_valid_input),
    ("Guardrail: out of range", test_guardrail_out_of_range),
    ("Guardrail: text input", test_guardrail_text_input),
    ("Agent: analysis perfect guess", test_analysis_perfect_guess),
    ("Agent: analysis poor guess", test_analysis_poor_guess),
    ("Agent: plan Too High midpoint", test_plan_too_high_midpoint),
    ("Agent: plan Too Low midpoint", test_plan_too_low_midpoint),
    ("RAG: documents indexed", test_rag_indexed),
    ("RAG: retrieval returns results", test_rag_retrieval_returns_results),
    ("Simulation: binary search", test_binary_search_simulation),
]


def main():
    print("\n" + "=" * 70)
    print("  AI GAME INTELLIGENCE SYSTEM - EVALUATION HARNESS")
    print("  AI110 Module 9 | Game Glitch Investigator Extension")
    print("=" * 70 + "\n")

    results = []
    for name, fn in ALL_TESTS:
        print(f"  Running: {name} ...", end=" ", flush=True)
        result = run_test(name, fn)
        results.append(result)
        status = "PASS" if result.passed else "FAIL"
        print(f"{status} ({result.latency_ms}ms)")
        if not result.passed:
            print(f"         -> {result.notes}")

    passed = sum(1 for r in results if r.passed)
    failed = len(results) - passed
    avg_conf = sum(r.confidence for r in results if r.passed) / max(passed, 1)
    avg_latency = sum(r.latency_ms for r in results) / len(results)

    print("\n" + "=" * 70)
    print(f"  RESULTS: {passed}/{len(results)} tests passed")
    print(f"  CONFIDENCE (passing tests): {avg_conf:.0%} average")
    print(f"  LATENCY: {avg_latency:.0f}ms average per test")

    if failed > 0:
        print(f"\n  FAILURES ({failed}):")
        for r in results:
            if not r.passed:
                print(f"    - {r.name}: {r.notes}")
    else:
        print("\n  All tests passed. System is reliable.")

    print("=" * 70 + "\n")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

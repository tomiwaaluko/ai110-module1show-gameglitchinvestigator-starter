# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A CodePath AI-110 Module 1 assignment: an intentionally buggy Streamlit number-guessing game. Students debug and fix the game, then refactor logic into `logic_utils.py` and make tests pass.

## Commands

- **Install dependencies:** `pip install -r requirements.txt`
- **Run the app:** `python -m streamlit run app.py`
- **Run tests:** `pytest`
- **Run a single test:** `pytest tests/test_game_logic.py::test_winning_guess`

## Architecture

- `app.py` — Streamlit UI and game loop. Contains the buggy implementations of all game functions inline.
- `logic_utils.py` — Stub file with `NotImplementedError` placeholders. Students must move fixed logic here from `app.py`.
- `tests/test_game_logic.py` — Pytest tests that import from `logic_utils` and validate `check_guess()`. Tests expect `check_guess` to return just the outcome string (e.g., `"Win"`, `"Too High"`, `"Too Low"`), not a tuple.

## Known Intentional Bugs in app.py

These are the bugs students need to find and fix:

1. **Inverted hints** (`check_guess`): "Go HIGHER" is shown when guess is too high, and vice versa (lines 37-40).
2. **Type coercion bug** (lines 158-161): On even attempts, the secret is cast to `str`, causing type mismatch comparisons.
3. **Difficulty ranges wrong** (`get_range_for_difficulty`): Hard mode uses 1-50 (easier than Normal's 1-100).
4. **Score calculation off-by-one** (`update_score`): Win points use `attempt_number + 1` instead of `attempt_number`.
5. **Inconsistent score penalty**: "Too High" on even attempts gives +5 instead of -5.
6. **Display bug** (line 110): Info bar always says "between 1 and 100" regardless of difficulty.

## Key Detail for Refactoring

Tests expect `check_guess` to return a single string outcome, but `app.py`'s version returns a `(outcome, message)` tuple. The refactored `logic_utils.check_guess` must return just the outcome string to match test expectations.

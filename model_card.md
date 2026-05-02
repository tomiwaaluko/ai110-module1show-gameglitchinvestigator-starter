# Model Card: AI Game Intelligence System

**Base Project:** Game Glitch Investigator (AI110 Module 1)  
**Extended For:** AI110 Module 9 - Show What You Know: Applied AI System  
**Author:** Tomiwa Aluko  
**Date:** May 2026

## What This System Does

This system extends a Streamlit number-guessing game into an AI-powered coaching application. On each player guess, an agentic AI workflow analyzes the guess's efficiency against binary search, retrieves relevant strategy content from a three-document RAG knowledge base, computes the next optimal guess, and calls the Gemini API to generate a natural-language coaching tip.

## AI Feature Used

**Primary:** Agentic Workflow - a five-step observable reasoning chain: Analyze, Retrieve, Plan, Advise, Validate.  
**Secondary:** Retrieval-Augmented Generation - ChromaDB vector search over three curated knowledge-base documents.

## Limitations and Biases

The knowledge base strongly favors binary search. That is mathematically optimal for this game, but the coach may be too prescriptive for learners who benefit from discovery. Confidence scoring also assumes the current full difficulty range unless future work derives a tighter range from all prior hints.

The Gemini API is an external dependency. When the key is missing, quota is exhausted, or the API fails, the system falls back to rule-based tips. The fallback is reliable but less adaptive than model-generated coaching.

## Potential Misuse

A player could use the reasoning trace to get optimal guesses without engaging with the learning goal. In a deployed classroom setting, that trace should be instructor-only or hidden until the round ends.

A malicious user could try prompt-injection text as a guess. The guardrails reject non-numeric input, sanitize AI responses, and pass structured numeric context to the model instead of raw user text.

API keys must not be committed. The repository ignores `.env`, and deployment should use platform secrets.

## Testing Surprises

The main testing surprise was that retrieval can be noisy when strategy and debugging documents share words like "win" and "score." More specific query construction in the retrieve step improves the relevance of returned chunks.

The binary-search simulation confirmed that the original game logic is reliable: simulated Normal-mode games can be solved within the expected logarithmic attempt count.

## AI Collaboration During This Project

A helpful AI suggestion was using `math.ceil(math.log2(remaining_range + 1))` to estimate how many guesses remain under optimal play. That made confidence scoring easy to explain.

A flawed suggestion was persisting the vector database by default. For Streamlit and a small local knowledge base, an in-memory index is simpler and avoids duplicate-document issues across reruns.

## What This Project Taught Me About AI

An agent is most useful when each step has a clear input, output, and failure mode. The model call is only one part of the system; retrieval, validation, fallbacks, logging, and tests are what make it reliable enough to present as applied AI engineering.

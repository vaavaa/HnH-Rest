# Prompt Spec v1 — Persona Enforcement & Versioned Prompt Assembly

## Problem

HnH generates deterministic personality vectors (32D + activity + stress),
but LLMs do not natively respect numeric weights or behavioral constraints.

Without a formal prompt specification layer:
- personality weights drift
- stylistic enforcement weakens over time
- replay determinism breaks
- regression testing becomes impossible

## Goal

Introduce a versioned Prompt Specification system that:

1. Converts personality vectors into semantic traits.
2. Enforces behavior via explicit constraints (not descriptive hints).
3. Supports deterministic prompt assembly.
4. Provides versioned bundles for reproducibility.
5. Enables audit + replay of all rendered prompts.

This change introduces Prompt Spec v1 as a first-class system component.
# hnh-rest

**hnh-rest** is the REST layer for the HnH (Human Needs Human) ecosystem.

It provides a versioned Prompt Specification system and deterministic prompt rendering
on top of `hnh-core`, enabling controlled personality enforcement for AI agents.

---

## Purpose

While `hnh-core` calculates personality state (natal, transits, 32D behavior, lifecycle),
`hnh-rest` ensures that LLMs:

- Respect personality weights
- Follow explicit behavioral constraints
- Produce reproducible outputs
- Support audit and replay

This service acts as a **Prompt Registry + Renderer** for AI agent systems.

---

## Core Responsibilities

- Versioned Prompt Templates
- Immutable Prompt Bundles
- Deterministic Prompt Assembly
- Persona Enforcement Contracts
- Audit & Replay Support
- Performance-optimized JSON (orjson)
- Async PostgreSQL support

---

## Architecture


hnh-core
↓
Personality Adapter
↓
hnh-rest (Prompt Registry + Renderer)
↓
LLM


`hnh-rest` does not calculate personality —
it enforces how personality is delivered to language models.

---

## Why It Exists

Numeric personality vectors alone are not sufficient for LLM control.

This service ensures:

- Structured constraint enforcement
- Version-controlled prompt evolution
- Stable AI behavior over time
- Regression-testable personality rendering

---

## Status

Part of the HnH open-source ecosystem.

See `hnh-core` for personality engine.
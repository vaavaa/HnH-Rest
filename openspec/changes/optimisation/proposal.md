# Optimisation — Performance pass + non-DB prompt generator

**Repo**: HnH-Rest  
**Change ID**: `optimisation`  
**Branch**: `spec/optimisation`  
**Date**: 2026-02-23  
**Status**: Proposed  

Scope: optimise the Prompt Registry/Renderer path and add a non-DB generator that reuses the same deterministic rules.

---

## Why

The current Prompt Spec v1 implementation states determinism and performance intentions (orjson, fixed assembly order, etc.) but does not fully realise them in code. The contract of Prompt Spec v1 (deterministic assembly, semantic_traits/activity/stress/task inputs, audit/replay) must remain intact. This change delivers a measurable performance pass and an alternative entry point that can render prompts without the DB, using the same deterministic rules.

---

## What Changes

- **Performance**: Enforce ORJSON (or orjson) in API and hot paths; remove remaining `json.dumps`/`json.loads` from the render path. Ensure single join for assembly, no N+1 DB queries, optional LRU cache for bundle/template resolution and compiled constraints.
- **Architecture**: Introduce a sources layer (TemplateSource, BundleSource) and a single shared renderer; DB and non-DB differ only by source adapters.
- **New**: Non-DB Prompt Generator — `PromptGenerator` with `render_from_bundle` (DB sources) and `render_inline` (inline sources); same rules, same hashes, no DB required. Useful for tests, CLI, offline pipelines, future MCP adapter.
- **Audit**: Pluggable audit sink (DB vs null); audit MUST NOT affect prompt hash.
- **Testing**: Parity tests (DB vs inline same content → same hash); determinism tests; coverage gate for prompt subsystem; optional micro-benchmark or time-budget smoke test.

No breaking changes to the existing Prompt Spec v1 API contract or data model.

---

## Capabilities

### New capabilities

- `optimisation`: Performance optimisation of the prompt render path (ORJSON, allocations, DB queries, optional cache) plus a non-DB prompt generator with the same deterministic rules and hash parity. Spec: `specs/optimisation/spec.md`.

### Modified capabilities

- None (prompt-spec-v1 requirements and API contract unchanged).

---

## Impact

- **Code**: `hnh_rest/services/prompts/` (renderer, new generator, sources, audit adapters), `hnh_rest/web/api/` (prompts routes — response class, any serialisation).
- **Dependencies**: orjson already used or to be standard for API/render; no new runtime deps.
- **APIs**: No change to request/response shapes; behaviour remains backward compatible.
- **Systems**: Optional in-process LRU cache (bounded, async-safe); DB usage unchanged except for possible query tuning.

# Optimisation spec — Performance pass + non-DB prompt generator

**Change ID**: `optimisation`

---

## 1. Compatibility & invariants (MUST)

### 1.1 Deterministic assembly (MUST)

- Assembly order MUST remain fixed: **system → personality → activity → task**. Final prompt MUST be `"\n\n".join(parts)` with stable normalization.
- No randomness, no timestamps, no unordered container iteration without sorting.

### 1.2 Prompt input contract (MUST)

The prompt layer MUST accept only the derived payload (no raw vector_32):

- `semantic_traits: {...}`
- `activity_level: float`
- `stress: float`
- `task: string`

### 1.3 Audit / replay (MUST)

- If DB audit is enabled, audit records MUST be written in a consistent format and replay MUST reconstruct identical prompt text for matching inputs.
- Audit writing MUST NOT influence the prompt hash; audit is best-effort after the render result is computed (e.g. do not block response on audit write).

---

## 2. Performance requirements (MUST / SHOULD)

### 2.1 JSON & serialisation

- API MUST use `ORJSONResponse` as default response class (or explicit per route).
- Internal JSON handling in the render hot path MUST avoid `json.dumps` / `json.loads`; use `orjson` when serialisation is needed.

### 2.2 Hot-path allocations (MUST)

- No string concatenation inside loops for prompt assembly.
- Use `list.append` + `"\n\n".join(parts)` exactly once per render.

### 2.3 DB access (SHOULD, when DB mode)

- Use async SQLAlchemy sessions end-to-end.
- Avoid N+1: one bundle lookup and one batched template fetch (or single join) per render.
- Indexed lookups for `(bundle_id, semver)` and `(template_id, semver)` MUST remain used.

### 2.4 Caching (SHOULD)

- In-process cache for:
  - bundle resolution by `(bundle_id, bundle_version)`
  - template resolution by `(template_id, template_version)`
  - compiled/normalised constraint structures (format per Prompt Spec v1; see `openspec/changes/prompt-spec-v1/specs/prompt-spec/spec.md`)
- Cache MUST be bounded (e.g. LRU) and safe for async (no global mutable dict without appropriate synchronisation). In-memory, per-process; invalidation by size/eviction only (no TTL required by this spec).

---

## 3. New feature: non-DB prompt generator

### 3.1 Motivation

A deterministic generator callable without DB for: unit tests without Postgres, offline prompt building (CLI, pipelines), and a future MCP adapter that supplies bundle/templates externally.

### 3.2 Data types for sources

Sources return data that the renderer consumes. Use either existing ORM models (read-only view) or explicit data transfer types with the same logical fields:

- **Template**: at least `id`, `content`, and constraint-related data (format per Prompt Spec v1). In code these may be the existing `PromptTemplate` model or a dataclass/protocol with those attributes.
- **Bundle**: at least bundle identity and the four template IDs in assembly order. In code these may be the existing `PromptBundle` model or a dataclass/protocol with those attributes.

Implementations MUST ensure that inline data produces the same render and hash as DB-sourced data when content and identity match.

### 3.3 Source protocols (MUST)

Introduce small, explicit protocols (duck typing allowed):

- **TemplateSource**: `async get_template(template_id: str, semver: str) -> <template data>`  
  Returns data with at least: content, and constraint info per Prompt Spec v1.

- **BundleSource**: `async get_bundle(bundle_id: str, semver: str) -> <bundle data>`  
  Returns data with at least: the four template IDs in fixed assembly order.

Implementations:

- `DbTemplateSource`, `DbBundleSource` (wrap current DB services).
- `InlineTemplateSource`, `InlineBundleSource` (parameter-driven, no DB).

### 3.4 PromptGenerator (MUST)

A class `PromptGenerator` that:

- Depends on `BundleSource`, `TemplateSource`, and the shared deterministic renderer.
- Exposes `async render_from_bundle(bundle_id, bundle_version, input_payload) -> RenderResult`.
- Exposes `async render_inline(bundle_data, templates_data, input_payload) -> RenderResult`.
- Returns the same `prompt_hash` (and prompt text) for equivalent content in DB vs inline mode.

### 3.5 Audit sink (MUST / SHOULD)

- In DB mode, use `DbAuditSink` (writes to DB).
- In inline mode, default to `NullAuditSink` (no-op) or allow injecting any sink.
- Audit MUST NOT influence the prompt hash.

---

## 4. Testing requirements

### 4.1 Determinism parity (MUST)

- For a known bundle and templates: render via DB sources and via inline sources (same content); assert `prompt` and `prompt_hash` are identical.

### 4.2 Optimisation guardrails (SHOULD)

- Optional: micro-benchmark (e.g. pytest-benchmark) or a cheap “time budget” smoke test for the render endpoint.
- Static guard: the renderer module MUST NOT use `json.dumps`/`json.loads` in the render path (use orjson or equivalent).

### 4.3 Coverage (MUST)

- Target: **≥ 99%** line coverage for the **prompt subsystem**.
- **Prompt subsystem** is defined as: `hnh_rest/web/api/prompts*`, `hnh_rest/services/prompts/**`, and any DB models/schemas used only by prompts (e.g. prompt_audit, prompt_bundle, prompt_template, and their Pydantic schemas for prompts). CI MUST fail if this scope’s coverage drops below the target.
- If 99% is unreachable in a first pass, the change MAY define a lower minimum (e.g. 95%) for this scope and document the gap; the scope (list of modules/paths) MUST still be defined.

---

## 5. Compiled constraints (reference)

“Compiled constraints” in this change mean a normalised, cacheable representation of the constraint structure defined in Prompt Spec v1. Caching is optional (SHOULD); the representation is keyed by template (or bundle) identity and used to avoid repeated parsing in the render path. No new constraint schema is introduced; the format remains that of prompt-spec-v1.

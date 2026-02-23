# Implementation tasks — Optimisation

**Change ID**: `optimisation`  
**Branch**: `spec/optimisation`

---

## Phase 0 — Baseline & measurement

- [ ] Add `openspec/changes/optimisation/perf_baseline.md`: record machine, Python version, uv settings, Postgres version, and how the render endpoint was measured.
- [ ] Add a simple load script (k6 or Locust) or a `pytest-benchmark` target for `/v1/prompts/render` (or equivalent render URL).

---

## Phase 1 — Enforce ORJSON in API and render path

- [ ] Confirm `default_response_class = ORJSONResponse` at app level (and in prod config).
- [ ] Ensure prompts routes use `response_class=ORJSONResponse` where appropriate.
- [ ] Replace any remaining `json.dumps`/`json.loads` in the prompt request/render path with orjson (or remove unnecessary conversions).

---

## Phase 2 — Renderer hot-path optimisation

- [ ] Verify assembly uses a list + single `"\n\n".join(parts)`; no concatenation inside loops.
- [ ] Ensure semantic_traits rendering is deterministic (sorted keys) and avoids extra allocations (no unnecessary intermediate dict copies).
- [ ] Introduce a compiled/normalised representation for constraints (per Prompt Spec v1 schema) and cache it (e.g. LRU) for repeated use; see spec section 5 and design.

---

## Phase 3 — DB query optimisation (async)

- [ ] Ensure render path uses one bundle query + one template batch query (or a single join) — no N+1.
- [ ] Confirm indexes are used (document in `perf_baseline.md` or design if needed).
- [ ] Optionally tune pool settings in `settings.py` (pool_size, max_overflow) for local dev.

---

## Phase 4 — Non-DB prompt generator

- [ ] Introduce `BundleSource` and `TemplateSource` protocols (duck typing allowed); data types as in spec section 3.2.
- [ ] Implement `DbBundleSource` and `DbTemplateSource` (wrap existing DB access).
- [ ] Implement `InlineBundleSource` and `InlineTemplateSource`.
- [ ] Implement `PromptGenerator` with `render_from_bundle` and `render_inline`.
- [ ] Add `NullAuditSink` and pluggable audit sink for generator.

---

## Phase 5 — Tests

- [ ] Parity test: same content via DB sources vs inline sources → same `prompt` and `prompt_hash`.
- [ ] Isolated unit tests for inline sources (no DB).
- [ ] Determinism test for semantic_traits ordering in renderer.
- [ ] Coverage gate: prompt subsystem (see spec section 4.3) ≥ 99% (or agreed lower minimum); fail CI if below. Scope: `hnh_rest/web/api/prompts*`, `hnh_rest/services/prompts/**`, and prompt-only models/schemas.
- [ ] Optional: micro-benchmark or time-budget smoke test; static check that renderer does not use `json.dumps`/`json.loads` in render path.

---

## Phase 6 — Full test suite

- [ ] Run full test suite locally (e.g. `pytest -vv .`) and via docker-compose (DB + app); all pass before performance re-check.

---

## Phase 7 — Performance re-check

- [ ] Re-run baseline measurement; record improvement in `perf_baseline.md`.
- [ ] Confirm no determinism regressions.

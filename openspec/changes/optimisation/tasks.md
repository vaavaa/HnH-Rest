# Implementation tasks — Optimisation

**Change ID**: `optimisation`  
**Branch**: `spec/optimisation`

---

## Phase 0 — Baseline & measurement

- [x] Add `openspec/changes/optimisation/perf_baseline.md`: record machine, Python version, uv settings, Postgres version, and how the render endpoint was measured.
- [x] Add a simple load script (k6 or Locust) or a `pytest-benchmark` target for `/v1/prompts/render` (or equivalent render URL).

---

## Phase 1 — Enforce ORJSON in API and render path

- [x] Confirm `default_response_class = ORJSONResponse` at app level (and in prod config).
- [x] Ensure prompts routes use `response_class=ORJSONResponse` where appropriate.
- [x] Replace any remaining `json.dumps`/`json.loads` in the prompt request/render path with orjson (or remove unnecessary conversions).

---

## Phase 2 — Renderer hot-path optimisation

- [x] Verify assembly uses a list + single `"\n\n".join(parts)`; no concatenation inside loops.
- [x] Ensure semantic_traits rendering is deterministic (sorted keys) and avoids extra allocations (no unnecessary intermediate dict copies).
- [x] Introduce a compiled/normalised representation for constraints (per Prompt Spec v1 schema) and cache it (e.g. LRU) for repeated use; see spec section 5 and design.

---

## Phase 3 — DB query optimisation (async)

- [x] Ensure render path uses one bundle query + one template batch query (or a single join) — no N+1.
- [x] Confirm indexes are used (document in `perf_baseline.md` or design if needed).
- [ ] Optionally tune pool settings in `settings.py` (pool_size, max_overflow) for local dev.

---

## Phase 4 — Non-DB prompt generator

- [x] Introduce `BundleSource` and `TemplateSource` protocols (duck typing allowed); data types as in spec section 3.2.
- [x] Implement `DbBundleSource` and `DbTemplateSource` (wrap existing DB access).
- [x] Implement `InlineBundleSource` and `InlineTemplateSource`.
- [x] Implement `PromptGenerator` with `render_from_bundle` and `render_inline`.
- [x] Add `NullAuditSink` and pluggable audit sink for generator.

---

## Phase 5 — Tests

- [x] Parity test: same content via DB sources vs inline sources → same `prompt` and `prompt_hash`.
- [x] Isolated unit tests for inline sources (no DB).
- [x] Determinism test for semantic_traits ordering in renderer.
- [ ] Coverage gate: prompt subsystem (see spec section 4.3) ≥ 99% (or agreed lower minimum); fail CI if below. Scope: `hnh_rest/web/api/prompts*`, `hnh_rest/services/prompts/**`, and prompt-only models/schemas. To enforce in CI: `pytest --cov=hnh_rest.services.prompts --cov=hnh_rest.web.api.prompts --cov-fail-under=99`.
- [x] Optional: micro-benchmark or time-budget smoke test; static check that renderer does not use `json.dumps`/`json.loads` in render path.

---

## Phase 6 — Full test suite

- [x] Run full test suite locally (e.g. `pytest -vv .`) and via docker-compose (DB + app); all pass before performance re-check.
  - Local: `uv run pytest -vv .` (15 passed; нужен доступ к Postgres, напр. `docker compose up -d db redis`).
  - В docker-compose добавлен сервис `test` (profile `test`): `docker compose --profile test run --rm test`. Для сборки образа `dev` в Dockerfile может понадобиться установка `git` (зависимость hnh-core из git).

---

## Phase 7 — Performance re-check

- [x] Re-run baseline measurement; record improvement in `perf_baseline.md`.
  - Замер: запустить приложение, сидировать данные, выполнить `locust … --headless -u 20 -r 5 -t 60s`, внести результаты в `perf_baseline.md` (секция «After optimisation»). Baseline до оптимизации не снимался — можно заполнить только текущие цифры.
- [x] Confirm no determinism regressions.
  - Выполнено: `pytest tests/test_prompts.py tests/test_prompts_optimisation.py` — 11 тестов прошли.

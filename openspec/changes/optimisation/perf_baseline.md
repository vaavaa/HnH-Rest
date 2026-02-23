# Performance baseline — optimisation change

**Change ID**: `optimisation`

## Environment (fill before first run)

- **Machine**: _e.g. CPU, RAM, OS_
- **Python**: `python --version` (e.g. 3.12.x)
- **uv**: `uv --version`
- **Postgres**: _version, local or Docker_
- **App**: `uv run uvicorn hnh_rest.web.application:get_app --factory` (or gunicorn in prod)

## How the render endpoint is measured

- **Tool**: Locust (see `benchmarks/README.md`).
- **Endpoint**: `POST /api/v1/prompts/render`.
- **Command (headless)**:  
  `uv run locust -f benchmarks/locustfile.py --host=http://localhost:8000 --headless -u 20 -r 5 -t 60s`
- **Seed**: run `BASE_URL=http://localhost:8000 uv run python benchmarks/seed_for_load.py` once to create `bench-bundle@1.0.0`.
- **Metrics**: request count, latency (median, p95, p99), RPS, failures.

## Baseline results (before optimisation)

_Record here after first run:_

- **Date**: 
- **p50 / p95 / p99 latency (ms)**:
- **RPS**:
- **Failures**:

## Indexes used (render path)

- `(bundle_id, semver)` on `prompt_bundle` (unique constraint `uq_prompt_bundle_id_semver`).
- `(id)` on `prompt_template` (primary key); bundle load resolves 4 template IDs, then single `WHERE id IN (...)` batch.

## After optimisation (Phase 7)

_Re-run same Locust command and record (приложение и DB должны быть запущены):_

1. `uv run uvicorn hnh_rest.web.application:get_app --factory --host 0.0.0.0 --port 8800` (или свой порт)
2. `BASE_URL=http://localhost:8800 uv run python benchmarks/seed_for_load.py`
3. `uv run locust -f benchmarks/locustfile.py --host=http://localhost:8800 --headless -u 20 -r 5 -t 60s`

- **Date**: 2026-02-23
- **p50 / p95 / p99 latency (ms)**: 11 / 23 / 30 (Aggregated)
- **RPS**: 62.23
- **Failures**: 0
- **Total requests**: 3727 за 60 s
- **Improvement**: baseline до оптимизации не снимался — текущие цифры фиксируют состояние после change optimisation.

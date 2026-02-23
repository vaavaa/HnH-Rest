# Load testing — Prompt Spec v1 render endpoint

Benchmark for `POST /api/v1/prompts/render` (Phase 7, tasks.md).

## Prerequisites

- App and DB running (e.g. `uv run uvicorn hnh_rest.web.application:get_app --factory`)
- Optional: Redis if enabled in settings

## 1. Seed data (once)

Creates 4 templates and bundle `bench-bundle@1.0.0` used by the locust scenario:

```bash
BASE_URL=http://localhost:8000 uv run python benchmarks/seed_for_load.py
```

Use a fresh DB or ensure no conflict with existing `bench-bundle` / template IDs.

## 2. Run Locust

**Web UI** (then open http://localhost:8089):

```bash
uv run locust -f benchmarks/locustfile.py --host=http://localhost:8000
```

**Headless** (e.g. 20 users, 5/s spawn, 60s):

```bash
uv run locust -f benchmarks/locustfile.py --host=http://localhost:8000 \
  --headless -u 20 -r 5 -t 60s
```

Results show request count, latency (median, p95, p99), failures, RPS.

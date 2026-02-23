#!/usr/bin/env -S uv run python
"""
Seed templates and one bundle for load testing POST /api/v1/prompts/render.

Requires the app and DB to be running. Example:
  BASE_URL=http://localhost:8000 uv run python benchmarks/seed_for_load.py

Creates:
- 4 templates (sys, persona, activity, task) at semver 1.0.0
- 1 bundle "bench-bundle" at 1.0.0 referencing them
"""

import os
import sys
import urllib.request
import json

BASE_URL = os.environ.get("BASE_URL", "http://localhost:8000").rstrip("/")
API = f"{BASE_URL}/api"


def request(method: str, path: str, body: dict | None = None) -> tuple[int, dict]:
    url = f"{API}{path}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.getcode(), json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, {"detail": e.read().decode()}
    except Exception as e:
        return -1, {"error": str(e)}


def main() -> int:
    templates = [
        {"template_id": "sys", "semver": "1.0.0", "role": "system", "content": "System: {{task}}"},
        {"template_id": "persona", "semver": "1.0.0", "role": "user", "content": "Persona {{activity_level}}"},
        {"template_id": "activity", "semver": "1.0.0", "role": "user", "content": "Activity {{stress}}"},
        {"template_id": "task", "semver": "1.0.0", "role": "user", "content": "Task: {{task}}"},
    ]
    ids = []
    for t in templates:
        code, out = request("POST", "/v1/prompts/templates", t)
        if code == 201:
            ids.append(out["id"])
        elif code == 409:
            print("Template already exists (run seed on empty DB or use existing bench-bundle).", file=sys.stderr)
            code2, _ = request("GET", "/v1/prompts/bundles/bench-bundle?semver=1.0.0")
            if code2 == 200:
                print("Bundle bench-bundle@1.0.0 exists. Ready for load test.")
                return 0
            return 1
        else:
            print(f"POST /templates failed: {code} {out}", file=sys.stderr)
            return 1

    if len(ids) != 4:
        print("Need 4 template IDs.", file=sys.stderr)
        return 1

    code, out = request(
        "POST",
        "/v1/prompts/bundles",
        {
            "bundle_id": "bench-bundle",
            "semver": "1.0.0",
            "system_template_id": ids[0],
            "personality_template_id": ids[1],
            "activity_template_id": ids[2],
            "task_template_id": ids[3],
        },
    )
    if code == 201:
        print("Seeded bench-bundle@1.0.0. Run: uv run locust -f benchmarks/locustfile.py --host=" + BASE_URL)
        return 0
    if code == 409:
        print("Bundle bench-bundle@1.0.0 already exists. Ready for load test.")
        return 0
    print(f"POST /bundles failed: {code} {out}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())

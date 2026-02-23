"""
Load test for POST /api/v1/prompts/render (Prompt Spec v1).

Run after seeding a bundle (see benchmarks/README.md):
  uv run locust -f benchmarks/locustfile.py --host=http://localhost:8000

Then open http://localhost:8089, set users/spawn rate, start.
Headless:
  uv run locust -f benchmarks/locustfile.py --host=http://localhost:8000 \
    --headless -u 20 -r 5 -t 60s
"""

import random
from locust import HttpUser, task, between


# Default bundle created by benchmarks/seed_for_load.py
BUNDLE_ID = "bench-bundle"
SEMVER = "1.0.0"


class RenderUser(HttpUser):
    """Simulates clients calling the render endpoint."""

    wait_time = between(0.1, 0.5)

    @task(10)
    def render_short_task(self) -> None:
        """Most frequent: short task text."""
        self.client.post(
            "/api/v1/prompts/render",
            json={
                "bundle_id": BUNDLE_ID,
                "semver": SEMVER,
                "semantic_traits": {"tone": "friendly"},
                "activity_level": round(random.uniform(0, 1), 2),
                "stress": round(random.uniform(0, 1), 2),
                "task": "Summarize the meeting notes.",
            },
            name="/render (short)",
        )

    @task(5)
    def render_medium_task(self) -> None:
        """Medium: longer task and traits."""
        self.client.post(
            "/api/v1/prompts/render",
            json={
                "bundle_id": BUNDLE_ID,
                "semver": SEMVER,
                "semantic_traits": {
                    "tone": random.choice(["formal", "casual", "friendly"]),
                    "detail_level": random.randint(1, 5),
                },
                "activity_level": 0.5,
                "stress": 0.2,
                "task": "Given the following context, produce a structured response with sections: Summary, Action items, and Next steps. " * 3,
            },
            name="/render (medium)",
        )

    @task(1)
    def render_minimal(self) -> None:
        """Minimal payload."""
        self.client.post(
            "/api/v1/prompts/render",
            json={
                "bundle_id": BUNDLE_ID,
                "semver": SEMVER,
                "task": "Go.",
            },
            name="/render (minimal)",
        )

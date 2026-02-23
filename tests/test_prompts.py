"""Phase 5 — Determinism & Replay tests for Prompt Spec v1."""

import asyncio

import pytest
from httpx import AsyncClient
from pydantic import ValidationError
from starlette import status

from hnh_rest.web.api.prompts.schema import BundleCreate, TemplateCreate


async def _create_templates(client: AsyncClient) -> list[str]:
    """Create 4 templates (system, personality, activity, task); return list of template IDs."""
    templates = [
        {"template_id": "sys", "semver": "1.0.0", "role": "system", "content": "System: {{task}}"},
        {"template_id": "persona", "semver": "1.0.0", "role": "user", "content": "Persona {{activity_level}}"},
        {"template_id": "activity", "semver": "1.0.0", "role": "user", "content": "Activity {{stress}}"},
        {"template_id": "task", "semver": "1.0.0", "role": "user", "content": "Task: {{task}}"},
    ]
    ids = []
    for t in templates:
        r = await client.post("/api/v1/prompts/templates", json=t)
        assert r.status_code == status.HTTP_201_CREATED, r.text
        ids.append(r.json()["id"])
    return ids


async def _create_bundle(
    client: AsyncClient,
    system_id: str,
    personality_id: str,
    activity_id: str,
    task_id: str,
    bundle_id: str = "test-bundle",
    semver: str = "1.0.0",
) -> None:
    """Create one bundle referencing the four template IDs."""
    r = await client.post(
        "/api/v1/prompts/bundles",
        json={
            "bundle_id": bundle_id,
            "semver": semver,
            "system_template_id": system_id,
            "personality_template_id": personality_id,
            "activity_template_id": activity_id,
            "task_template_id": task_id,
        },
    )
    assert r.status_code == status.HTTP_201_CREATED, r.text


@pytest.mark.anyio
async def test_deterministic_render_snapshot(client: AsyncClient) -> None:
    """Same input must produce identical rendered_prompt and hashes (deterministic assembly)."""
    ids = await _create_templates(client)
    await _create_bundle(client, ids[0], ids[1], ids[2], ids[3])

    payload = {
        "bundle_id": "test-bundle",
        "semver": "1.0.0",
        "semantic_traits": {"a": 1},
        "activity_level": 0.5,
        "stress": 0.2,
        "task": "hello",
    }
    r1 = await client.post("/api/v1/prompts/render", json=payload)
    r2 = await client.post("/api/v1/prompts/render", json=payload)
    assert r1.status_code == status.HTTP_200_OK
    assert r2.status_code == status.HTTP_200_OK

    j1, j2 = r1.json(), r2.json()
    assert j1["rendered_prompt"] == j2["rendered_prompt"]
    assert j1["bundle_hash"] == j2["bundle_hash"]
    assert j1["personality_hash"] == j2["personality_hash"]
    # Fixed order: system → personality → activity → task
    expected = "System: hello\n\nPersona 0.5\n\nActivity 0.2\n\nTask: hello"
    assert j1["rendered_prompt"] == expected


@pytest.mark.anyio
async def test_bundle_immutability(client: AsyncClient) -> None:
    """Creating the same (bundle_id, semver) twice must return 409."""
    ids = await _create_templates(client)
    await _create_bundle(client, ids[0], ids[1], ids[2], ids[3], bundle_id="immutable-bundle", semver="2.0.0")

    r = await client.post(
        "/api/v1/prompts/bundles",
        json={
            "bundle_id": "immutable-bundle",
            "semver": "2.0.0",
            "system_template_id": ids[0],
            "personality_template_id": ids[1],
            "activity_template_id": ids[2],
            "task_template_id": ids[3],
        },
    )
    assert r.status_code == status.HTTP_409_CONFLICT


async def _create_templates_race(client: AsyncClient) -> list[str]:
    """Create 4 templates with unique ids for race test (avoids polluting DB for other tests)."""
    templates = [
        {"template_id": "race-sys", "semver": "1.0.0", "role": "system", "content": "System: {{task}}"},
        {"template_id": "race-persona", "semver": "1.0.0", "role": "user", "content": "Persona {{activity_level}}"},
        {"template_id": "race-activity", "semver": "1.0.0", "role": "user", "content": "Activity {{stress}}"},
        {"template_id": "race-task", "semver": "1.0.0", "role": "user", "content": "Task: {{task}}"},
    ]
    ids = []
    for t in templates:
        r = await client.post("/api/v1/prompts/templates", json=t)
        assert r.status_code == status.HTTP_201_CREATED, r.text
        ids.append(r.json()["id"])
    return ids


@pytest.mark.anyio
async def test_no_race_when_publishing_bundle_version(
    client_per_request_session: AsyncClient,
) -> None:
    """Phase 7 — Concurrent create of same (bundle_id, semver): exactly one 201, rest 409, single row in DB."""
    client = client_per_request_session
    ids = await _create_templates_race(client)
    payload = {
        "bundle_id": "race-bundle",
        "semver": "3.0.0",
        "system_template_id": ids[0],
        "personality_template_id": ids[1],
        "activity_template_id": ids[2],
        "task_template_id": ids[3],
    }

    async def post_bundle() -> int:
        r = await client.post("/api/v1/prompts/bundles", json=payload)
        return r.status_code

    concurrency = 10
    results = await asyncio.gather(*[post_bundle() for _ in range(concurrency)])

    assert results.count(status.HTTP_201_CREATED) == 1, f"Expected exactly one 201, got {results}"
    assert results.count(status.HTTP_409_CONFLICT) == concurrency - 1

    get_r = await client.get("/api/v1/prompts/bundles/race-bundle?semver=3.0.0")
    assert get_r.status_code == status.HTTP_200_OK


@pytest.mark.anyio
async def test_constraint_validation_rejects_invalid(client: AsyncClient) -> None:
    """Template with invalid constraint structure must return 422."""
    r = await client.post(
        "/api/v1/prompts/templates",
        json={
            "template_id": "bad",
            "semver": "1.0.0",
            "role": "system",
            "content": "x",
            "constraints": {"FORBIDDEN_TOKENS": "not-a-list"},
        },
    )
    assert r.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.anyio
async def test_replay_consistency(client: AsyncClient) -> None:
    """After render, GET audit by bundle_hash must return the same rendered_prompt."""
    ids = await _create_templates(client)
    await _create_bundle(client, ids[0], ids[1], ids[2], ids[3], bundle_id="replay-bundle", semver="0.1.0")

    payload = {"bundle_id": "replay-bundle", "semver": "0.1.0", "task": "replay-me"}
    render_r = await client.post("/api/v1/prompts/render", json=payload)
    assert render_r.status_code == status.HTTP_200_OK
    bundle_hash = render_r.json()["bundle_hash"]
    rendered = render_r.json()["rendered_prompt"]

    audit_r = await client.get(f"/api/v1/audit/{bundle_hash}")
    assert audit_r.status_code == status.HTTP_200_OK
    assert audit_r.json()["rendered_prompt"] == rendered


@pytest.mark.anyio
async def test_hash_stability(client: AsyncClient) -> None:
    """Rendered prompt hash identical across runs for same input (bundle_hash + personality_hash stable)."""
    ids = await _create_templates(client)
    await _create_bundle(client, ids[0], ids[1], ids[2], ids[3], bundle_id="hash-bundle", semver="1.0.0")

    payload = {
        "bundle_id": "hash-bundle",
        "semver": "1.0.0",
        "semantic_traits": {"k": "v"},
        "activity_level": 0.0,
        "stress": 0.0,
        "task": "same",
    }
    r1 = await client.post("/api/v1/prompts/render", json=payload)
    r2 = await client.post("/api/v1/prompts/render", json=payload)
    assert r1.status_code == r2.status_code == status.HTTP_200_OK

    assert r1.json()["bundle_hash"] == r2.json()["bundle_hash"]
    assert r1.json()["personality_hash"] == r2.json()["personality_hash"]
    assert r1.json()["rendered_prompt"] == r2.json()["rendered_prompt"]


def test_semver_validation_strict() -> None:
    """Phase 8 — Semver must match major.minor.patch format (strict validation)."""
    TemplateCreate(
        template_id="t",
        semver="1.0.0",
        role="system",
        content="x",
    )
    with pytest.raises(ValidationError, match="semver"):
        TemplateCreate(
            template_id="t",
            semver="invalid",
            role="system",
            content="x",
        )
    with pytest.raises(ValidationError, match="semver"):
        TemplateCreate(
            template_id="t",
            semver="1.0",
            role="system",
            content="x",
        )
    # BundleCreate semver
    from uuid import uuid4

    uid = uuid4()
    BundleCreate(
        bundle_id="b",
        semver="2.1.0-alpha",
        system_template_id=uid,
        personality_template_id=uid,
        activity_template_id=uid,
        task_template_id=uid,
    )
    with pytest.raises(ValidationError, match="semver"):
        BundleCreate(
            bundle_id="b",
            semver="v1.0.0",
            system_template_id=uid,
            personality_template_id=uid,
            activity_template_id=uid,
            task_template_id=uid,
        )

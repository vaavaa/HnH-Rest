"""Phase 5 (optimisation change) — Parity, inline sources, determinism; no DB required."""

from pathlib import Path
from uuid import uuid4

import pytest

from hnh_rest.services.prompts.audit.null import NullAuditSink
from hnh_rest.services.prompts.prompt_generator import PromptGenerator
from hnh_rest.services.prompts.renderer import assemble_and_hash
from hnh_rest.services.prompts.sources.inline import (
    InlineBundleData,
    InlineBundleSource,
    InlineTemplateData,
    InlineTemplateSource,
)


@pytest.mark.anyio
async def test_parity_inline_vs_render_inline_same_hash() -> None:
    """Same content via render_from_bundle(inline sources) vs render_inline → same prompt and hashes."""
    u1, u2, u3, u4 = uuid4(), uuid4(), uuid4(), uuid4()
    parts = ["sys", "pers", "act", "task"]
    bundles = {
        ("parity-b", "1.0.0"): InlineBundleData("parity-b", "1.0.0", u1, u2, u3, u4),
    }
    templates = {
        u1: InlineTemplateData(u1, parts[0]),
        u2: InlineTemplateData(u2, parts[1]),
        u3: InlineTemplateData(u3, parts[2]),
        u4: InlineTemplateData(u4, parts[3]),
    }
    payload = {"x": 1}
    gen = PromptGenerator(
        InlineBundleSource(bundles),
        InlineTemplateSource(templates),
        NullAuditSink(),
    )

    r_from_bundle = await gen.render_from_bundle(
        "parity-b", "1.0.0", payload, 0.5, 0.2, "do it"
    )
    r_inline = await gen.render_inline(
        "parity-b", "1.0.0", parts, payload, 0.5, 0.2, "do it"
    )

    assert r_from_bundle.rendered_prompt == r_inline.rendered_prompt
    assert r_from_bundle.bundle_hash == r_inline.bundle_hash
    assert r_from_bundle.personality_hash == r_inline.personality_hash


@pytest.mark.anyio
async def test_inline_sources_no_db() -> None:
    """Inline sources return data without DB; get_templates_by_ids returns subset."""
    u1, u2 = uuid4(), uuid4()
    templates = {
        u1: InlineTemplateData(u1, "c1"),
        u2: InlineTemplateData(u2, "c2"),
    }
    src = InlineTemplateSource(templates)
    out = await src.get_templates_by_ids([u1, u2])
    assert len(out) == 2
    assert out[u1].content == "c1"
    assert out[u2].content == "c2"
    out_subset = await src.get_templates_by_ids([u1])
    assert list(out_subset) == [u1]

    bundles = {("b", "1.0.0"): InlineBundleData("b", "1.0.0", u1, u2, u1, u2)}
    bsrc = InlineBundleSource(bundles)
    b = await bsrc.get_bundle("b", "1.0.0")
    assert b is not None
    assert b.bundle_id == "b"
    assert b.semver == "1.0.0"
    assert await bsrc.get_bundle("missing", "1.0.0") is None


def test_determinism_semantic_traits_ordering() -> None:
    """Different dict key order for semantic_traits must yield same personality_hash."""
    parts = ["a", "b", "c", "d"]
    # Same logical payload, different insertion order
    traits1 = {"z": 3, "a": 1, "m": 2}
    traits2 = {"a": 1, "m": 2, "z": 3}
    p1 = assemble_and_hash("b", "1.0.0", parts, traits1, 0.5, 0.2, "task")
    p2 = assemble_and_hash("b", "1.0.0", parts, traits2, 0.5, 0.2, "task")
    assert p1[1] == p2[1]  # bundle_hash
    assert p1[2] == p2[2]  # personality_hash
    assert p1[0] == p2[0]  # rendered_prompt


def test_renderer_no_stdlib_json_in_hot_path() -> None:
    """Renderer module must not import or use stdlib json (use orjson in render path)."""
    renderer_path = Path(__file__).resolve().parent.parent / "hnh_rest" / "services" / "prompts" / "renderer.py"
    text = renderer_path.read_text()
    assert "import json" not in text and "from json" not in text, "renderer must not import stdlib json; use orjson"
    assert "orjson" in text

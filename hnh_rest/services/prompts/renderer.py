"""RendererService — deterministic prompt assembly and audit."""

import hashlib
from dataclasses import dataclass
from typing import Any

import orjson

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from hnh_rest.db.models.prompt_bundle import PromptBundle
from hnh_rest.db.models.prompt_template import PromptTemplate
from hnh_rest.services.prompts.constraints_cache import get_compiled_constraints


# Fixed assembly order (design: system → personality → activity → task)
ASSEMBLY_ORDER = (
    "system_template_id",
    "personality_template_id",
    "activity_template_id",
    "task_template_id",
)


@dataclass(frozen=True)
class _RenderContext:
    """Immutable context for placeholder substitution (no dict mutation)."""

    task: str
    activity_level: str
    stress: str
    semantic_traits_json: str


def _personality_hash(semantic_traits: dict[str, Any], activity_level: float, stress: float, task: str) -> str:
    """Deterministic hash of personality/render input for replay identity."""
    payload = {
        "semantic_traits": _sort_dict(semantic_traits),
        "activity_level": activity_level,
        "stress": stress,
        "task": task,
    }
    canonical = orjson.dumps(payload, option=orjson.OPT_SORT_KEYS)
    return hashlib.sha256(canonical).hexdigest()


def _bundle_hash(bundle_id: str, semver: str) -> str:
    """Deterministic hash identifying the bundle version."""
    return hashlib.sha256(f"{bundle_id}:{semver}".encode()).hexdigest()


def _sort_dict(d: dict[str, Any]) -> dict[str, Any]:
    """Recursively sort dict keys for canonical JSON."""
    return {k: _sort_dict(v) if isinstance(v, dict) else v for k, v in sorted(d.items())}


def _substitute(content: str, context: _RenderContext) -> str:
    """Replace {{key}} with context fields; no dict iteration, no injection."""
    content = content.replace("{{task}}", context.task)
    content = content.replace("{{activity_level}}", context.activity_level)
    content = content.replace("{{stress}}", context.stress)
    content = content.replace("{{semantic_traits}}", context.semantic_traits_json)
    return content


def assemble_and_hash(
    bundle_id: str,
    semver: str,
    parts_content: list[str],
    semantic_traits: dict[str, Any],
    activity_level: float,
    stress: float,
    task: str,
) -> tuple[str, str, str]:
    """
    Pure deterministic assembly: 4 content strings in order (system, personality, activity, task),
    plus payload. Returns (rendered_prompt, bundle_hash, personality_hash).
    Shared by DB and non-DB paths.
    """
    if len(parts_content) != 4:
        raise ValueError("parts_content must have exactly 4 parts (system, personality, activity, task)")
    traits_json = orjson.dumps(_sort_dict(semantic_traits), option=orjson.OPT_SORT_KEYS).decode()
    context = _RenderContext(
        task=task,
        activity_level=str(activity_level),
        stress=str(stress),
        semantic_traits_json=traits_json,
    )
    parts = [_substitute(c, context) for c in parts_content]
    rendered_prompt = "\n\n".join(parts)
    b_hash = _bundle_hash(bundle_id, semver)
    p_hash = _personality_hash(semantic_traits, activity_level, stress, task)
    return rendered_prompt, b_hash, p_hash


class RendererService:
    """Assemble prompts in deterministic order and record audit."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def render(
        self,
        bundle_id: str,
        semver: str,
        semantic_traits: dict[str, Any],
        activity_level: float,
        stress: float,
        task: str,
        engine_version: str | None = None,
        adapter_version: str | None = None,
    ) -> tuple[str, str, str]:
        """
        Load bundle and templates (single query for templates), assemble in fixed order.
        Order: system → personality → activity → task; parts joined by "\\n\\n".
        """
        bundle = await self._get_bundle(bundle_id, semver)
        if bundle is None:
            raise ValueError(f"Bundle not found: {bundle_id}@{semver}")

        template_ids = [getattr(bundle, attr) for attr in ASSEMBLY_ORDER]
        templates_map = await self._get_templates_by_ids(template_ids)
        for tid in template_ids:
            if tid not in templates_map:
                raise ValueError(f"Template not found: {tid}")

        for t in templates_map.values():
            get_compiled_constraints(t.template_id, t.semver, t.constraints)

        parts_content = [templates_map[tid].content for tid in template_ids]
        return assemble_and_hash(
            bundle_id, semver, parts_content,
            semantic_traits, activity_level, stress, task,
        )

    async def _get_bundle(self, bundle_id: str, semver: str) -> PromptBundle | None:
        """Load bundle by (bundle_id, semver). Indexed lookup."""
        result = await self._session.execute(
            select(PromptBundle).where(
                PromptBundle.bundle_id == bundle_id,
                PromptBundle.semver == semver,
            )
        )
        return result.scalar_one_or_none()

    async def _get_templates_by_ids(self, ids: list) -> dict:
        """Load multiple templates in one query; avoid N+1."""
        if not ids:
            return {}
        result = await self._session.execute(select(PromptTemplate).where(PromptTemplate.id.in_(ids)))
        rows = result.scalars().all()
        return {r.id: r for r in rows}
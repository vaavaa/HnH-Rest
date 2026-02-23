"""PromptGenerator — orchestration over sources, shared renderer, and audit sink."""

from dataclasses import dataclass
from typing import Any

from hnh_rest.services.prompts.protocols import AuditSink, BundleSource, TemplateSource
from hnh_rest.services.prompts.renderer import ASSEMBLY_ORDER, assemble_and_hash


@dataclass
class RenderResult:
    """Result of a render: prompt text and hashes."""

    rendered_prompt: str
    bundle_hash: str
    personality_hash: str


class PromptGenerator:
    """
    Renders prompts using configurable bundle/template sources and audit sink.
    Same deterministic rules and hashes for DB and inline modes.
    """

    def __init__(
        self,
        bundle_source: BundleSource,
        template_source: TemplateSource,
        audit_sink: AuditSink,
    ) -> None:
        self._bundle_source = bundle_source
        self._template_source = template_source
        self._audit_sink = audit_sink

    async def render_from_bundle(
        self,
        bundle_id: str,
        bundle_version: str,
        semantic_traits: dict[str, Any],
        activity_level: float,
        stress: float,
        task: str,
        engine_version: str | None = None,
        adapter_version: str | None = None,
    ) -> RenderResult:
        """Load bundle and templates from sources, assemble, audit, return result."""
        bundle = await self._bundle_source.get_bundle(bundle_id, bundle_version)
        if bundle is None:
            raise ValueError(f"Bundle not found: {bundle_id}@{bundle_version}")

        template_ids = [getattr(bundle, attr) for attr in ASSEMBLY_ORDER]
        templates_map = await self._template_source.get_templates_by_ids(template_ids)
        for tid in template_ids:
            if tid not in templates_map:
                raise ValueError(f"Template not found: {tid}")

        parts_content = [templates_map[tid].content for tid in template_ids]
        rendered_prompt, bundle_hash, personality_hash = assemble_and_hash(
            bundle_id, bundle_version, parts_content,
            semantic_traits, activity_level, stress, task,
        )
        await self._audit_sink.record(
            bundle_hash=bundle_hash,
            personality_hash=personality_hash,
            rendered_prompt=rendered_prompt,
            engine_version=engine_version,
            adapter_version=adapter_version,
        )
        return RenderResult(
            rendered_prompt=rendered_prompt,
            bundle_hash=bundle_hash,
            personality_hash=personality_hash,
        )

    async def render_inline(
        self,
        bundle_id: str,
        semver: str,
        parts_content: list[str],
        semantic_traits: dict[str, Any],
        activity_level: float,
        stress: float,
        task: str,
        engine_version: str | None = None,
        adapter_version: str | None = None,
    ) -> RenderResult:
        """
        Render from in-memory bundle identity and 4 template content strings (system, personality, activity, task).
        No DB. Same hash as render_from_bundle for equivalent content.
        """
        rendered_prompt, bundle_hash, personality_hash = assemble_and_hash(
            bundle_id, semver, parts_content,
            semantic_traits, activity_level, stress, task,
        )
        await self._audit_sink.record(
            bundle_hash=bundle_hash,
            personality_hash=personality_hash,
            rendered_prompt=rendered_prompt,
            engine_version=engine_version,
            adapter_version=adapter_version,
        )
        return RenderResult(
            rendered_prompt=rendered_prompt,
            bundle_hash=bundle_hash,
            personality_hash=personality_hash,
        )
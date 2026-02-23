"""Protocols for prompt sources (duck typing)."""

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class TemplateSource(Protocol):
    """Source of template data. Returned values must have .content and .id (for keying)."""

    async def get_template(self, template_id: str, semver: str) -> Any:
        """Return template data with at least .content (and optionally .id, .constraints)."""
        ...

    async def get_templates_by_ids(self, ids: list) -> dict:
        """Return dict id -> template data (with .content) for batch load. Used when bundle supplies UUIDs."""
        ...


@runtime_checkable
class BundleSource(Protocol):
    """Source of bundle data by (bundle_id, semver). Returned value must have 4 template IDs in order."""

    async def get_bundle(self, bundle_id: str, semver: str) -> Any:
        """Return bundle data with .bundle_id, .semver, .system_template_id, .personality_template_id, .activity_template_id, .task_template_id."""
        ...


@runtime_checkable
class AuditSink(Protocol):
    """Sink for audit records (DB or no-op). Must not affect prompt hash."""

    async def record(
        self,
        bundle_hash: str,
        personality_hash: str,
        rendered_prompt: str,
        engine_version: str | None = None,
        adapter_version: str | None = None,
    ) -> None:
        """Record a render for audit/replay. No-op allowed."""
        ...

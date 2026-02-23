"""Inline (in-memory) sources for bundles and templates — no DB."""

from dataclasses import dataclass
from typing import Any
from uuid import UUID


@dataclass
class InlineTemplateData:
    """Minimal template data for inline source."""

    id: UUID
    content: str
    template_id: str = ""
    semver: str = ""
    constraints: dict[str, Any] | None = None


@dataclass
class InlineBundleData:
    """Minimal bundle data for inline source — 4 template IDs in assembly order."""

    bundle_id: str
    semver: str
    system_template_id: UUID
    personality_template_id: UUID
    activity_template_id: UUID
    task_template_id: UUID


class InlineBundleSource:
    """Bundle source from in-memory dict. Key: (bundle_id, semver)."""

    def __init__(self, bundles: dict[tuple[str, str], InlineBundleData | Any]) -> None:
        self._bundles = bundles

    async def get_bundle(self, bundle_id: str, semver: str) -> InlineBundleData | Any | None:
        return self._bundles.get((bundle_id, semver))


class InlineTemplateSource:
    """Template source from in-memory dict. Key: template id (UUID). get_templates_by_ids for batch."""

    def __init__(self, templates_by_id: dict[UUID, InlineTemplateData | Any]) -> None:
        self._templates = templates_by_id

    async def get_template(self, template_id: str, semver: str) -> InlineTemplateData | Any | None:
        for t in self._templates.values():
            if getattr(t, "template_id", None) == template_id and getattr(t, "semver", None) == semver:
                return t
        return None

    async def get_templates_by_ids(self, ids: list) -> dict:
        return {tid: self._templates[tid] for tid in ids if tid in self._templates}

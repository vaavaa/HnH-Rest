"""DB-backed sources for bundles and templates."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from hnh_rest.db.models.prompt_bundle import PromptBundle
from hnh_rest.db.models.prompt_template import PromptTemplate
from hnh_rest.services.prompts.renderer import ASSEMBLY_ORDER


class DbBundleSource:
    """Bundle source that loads from the database."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_bundle(self, bundle_id: str, semver: str) -> PromptBundle | None:
        """Load bundle by (bundle_id, semver). Indexed lookup."""
        result = await self._session.execute(
            select(PromptBundle).where(
                PromptBundle.bundle_id == bundle_id,
                PromptBundle.semver == semver,
            )
        )
        return result.scalar_one_or_none()


class DbTemplateSource:
    """Template source that loads from the database."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_template(self, template_id: str, semver: str) -> PromptTemplate | None:
        """Load template by (template_id, semver)."""
        result = await self._session.execute(
            select(PromptTemplate).where(
                PromptTemplate.template_id == template_id,
                PromptTemplate.semver == semver,
            )
        )
        return result.scalar_one_or_none()

    async def get_templates_by_ids(self, ids: list) -> dict:
        """Load multiple templates in one query; avoid N+1."""
        if not ids:
            return {}
        result = await self._session.execute(select(PromptTemplate).where(PromptTemplate.id.in_(ids)))
        rows = result.scalars().all()
        return {r.id: r for r in rows}

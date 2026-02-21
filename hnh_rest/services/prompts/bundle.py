"""BundleService — create and read prompt bundles (immutable once created)."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from hnh_rest.db.models.prompt_bundle import PromptBundle


class BundleService:
    """Create and read prompt bundles. Bundles are immutable — no update/delete."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        bundle_id: str,
        semver: str,
        system_template_id: UUID,
        personality_template_id: UUID,
        activity_template_id: UUID,
        task_template_id: UUID,
    ) -> PromptBundle:
        """Create a new bundle. Raises if (bundle_id, semver) already exists. Once created, bundle is immutable."""
        bundle = PromptBundle(
            bundle_id=bundle_id,
            semver=semver,
            system_template_id=system_template_id,
            personality_template_id=personality_template_id,
            activity_template_id=activity_template_id,
            task_template_id=task_template_id,
        )
        self._session.add(bundle)
        await self._session.flush()
        await self._session.refresh(bundle)
        return bundle

    async def get_by_id(self, id: UUID) -> PromptBundle | None:
        """Get bundle by primary key."""
        result = await self._session.execute(select(PromptBundle).where(PromptBundle.id == id))
        return result.scalar_one_or_none()

    async def get_by_bundle_id_semver(self, bundle_id: str, semver: str) -> PromptBundle | None:
        """Get bundle by (bundle_id, semver)."""
        result = await self._session.execute(
            select(PromptBundle).where(
                PromptBundle.bundle_id == bundle_id,
                PromptBundle.semver == semver,
            )
        )
        return result.scalar_one_or_none()

    async def exists(self, bundle_id: str, semver: str) -> bool:
        """Check if a bundle with (bundle_id, semver) exists (for immutability: no overwrite)."""
        return await self.get_by_bundle_id_semver(bundle_id, semver) is not None

"""AuditService — append-only audit records for rendered prompts (replay support)."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from hnh_rest.db.models.prompt_audit import PromptAudit


class AuditService:
    """Create audit records. Records are immutable (append-only)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        bundle_hash: str,
        personality_hash: str,
        rendered_prompt: str,
        engine_version: str | None = None,
        adapter_version: str | None = None,
    ) -> PromptAudit:
        """Append an audit record for a render. No update/delete."""
        record = PromptAudit(
            bundle_hash=bundle_hash,
            personality_hash=personality_hash,
            engine_version=engine_version,
            adapter_version=adapter_version,
            rendered_prompt=rendered_prompt,
        )
        self._session.add(record)
        await self._session.flush()
        await self._session.refresh(record)
        return record

    async def get_by_id(self, id: UUID) -> PromptAudit | None:
        """Get audit record by primary key."""
        result = await self._session.execute(select(PromptAudit).where(PromptAudit.id == id))
        return result.scalar_one_or_none()

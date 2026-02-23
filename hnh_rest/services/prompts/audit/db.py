"""DB audit sink — writes to database via AuditService."""

from sqlalchemy.ext.asyncio import AsyncSession

from hnh_rest.services.prompts.audit.service import AuditService


class DbAuditSink:
    """Audit sink that writes to the database. Wraps AuditService."""

    def __init__(self, session: AsyncSession) -> None:
        self._service = AuditService(session)

    async def record(
        self,
        bundle_hash: str,
        personality_hash: str,
        rendered_prompt: str,
        engine_version: str | None = None,
        adapter_version: str | None = None,
    ) -> None:
        await self._service.create(
            bundle_hash=bundle_hash,
            personality_hash=personality_hash,
            rendered_prompt=rendered_prompt,
            engine_version=engine_version,
            adapter_version=adapter_version,
        )
        await self._service._session.flush()

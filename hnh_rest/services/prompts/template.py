"""TemplateService — CRUD for prompt templates."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from hnh_rest.db.models.prompt_template import PromptTemplate


class TemplateService:
    """Create and read prompt templates."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        template_id: str,
        semver: str,
        role: str,
        content: str,
        constraints: dict | None = None,
    ) -> PromptTemplate:
        """Create a new template. Raises if (template_id, semver) already exists."""
        template = PromptTemplate(
            template_id=template_id,
            semver=semver,
            role=role,
            content=content,
            constraints=constraints,
        )
        self._session.add(template)
        await self._session.flush()
        await self._session.refresh(template)
        return template

    async def get_by_id(self, id: UUID) -> PromptTemplate | None:
        """Get template by primary key."""
        result = await self._session.execute(select(PromptTemplate).where(PromptTemplate.id == id))
        return result.scalar_one_or_none()

    async def get_by_template_id_semver(self, template_id: str, semver: str) -> PromptTemplate | None:
        """Get template by (template_id, semver)."""
        result = await self._session.execute(
            select(PromptTemplate).where(
                PromptTemplate.template_id == template_id,
                PromptTemplate.semver == semver,
            )
        )
        return result.scalar_one_or_none()

    async def delete_by_id(self, id: UUID) -> bool:
        """Delete template by id. Returns True if deleted, False if not found."""
        template = await self.get_by_id(id)
        if template is None:
            return False
        await self._session.delete(template)
        await self._session.flush()
        return True

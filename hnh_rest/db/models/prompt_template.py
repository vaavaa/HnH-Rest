"""PromptTemplate model — versioned template unit."""

import uuid

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

from hnh_rest.db.base import Base


class PromptTemplate(Base):
    """Versioned prompt template with role, content, and machine-readable constraints."""

    __tablename__ = "prompt_template"

    id = sa.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    template_id = sa.Column(sa.String(255), nullable=False, index=True)
    semver = sa.Column(sa.String(64), nullable=False)
    role = sa.Column(sa.String(64), nullable=False)  # system | developer | user
    content = sa.Column(sa.Text(), nullable=False)
    constraints = sa.Column(JSONB, nullable=True)  # machine-readable enforcement schema
    created_at = sa.Column(sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)

    __table_args__ = (
        sa.UniqueConstraint("template_id", "semver", name="uq_prompt_template_id_semver"),
    )

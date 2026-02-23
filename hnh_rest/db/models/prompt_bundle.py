"""PromptBundle model — deterministic assembly of templates."""

import uuid

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

from hnh_rest.db.base import Base


class PromptBundle(Base):
    """Immutable bundle of template references; deterministic assembly order."""

    __tablename__ = "prompt_bundle"

    id = sa.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bundle_id = sa.Column(sa.String(255), nullable=False, index=True)
    semver = sa.Column(sa.String(64), nullable=False)
    system_template_id = sa.Column(UUID(as_uuid=True), sa.ForeignKey("prompt_template.id"), nullable=False)
    personality_template_id = sa.Column(UUID(as_uuid=True), sa.ForeignKey("prompt_template.id"), nullable=False)
    activity_template_id = sa.Column(UUID(as_uuid=True), sa.ForeignKey("prompt_template.id"), nullable=False)
    task_template_id = sa.Column(UUID(as_uuid=True), sa.ForeignKey("prompt_template.id"), nullable=False)
    tags = sa.Column(JSONB, nullable=False, server_default=sa.text("'[]'::jsonb"))
    created_at = sa.Column(sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)

    __table_args__ = (
        sa.UniqueConstraint("bundle_id", "semver", name="uq_prompt_bundle_id_semver"),
    )

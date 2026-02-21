"""PromptAudit model — audit record for rendered prompts (replay support)."""

import uuid

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from hnh_rest.db.base import Base


class PromptAudit(Base):
    """Immutable audit record: bundle_hash, personality_hash, versions, rendered text."""

    __tablename__ = "prompt_audit"

    id = sa.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bundle_hash = sa.Column(sa.String(64), nullable=False, index=True)
    personality_hash = sa.Column(sa.String(64), nullable=False, index=True)
    engine_version = sa.Column(sa.String(64), nullable=True)
    adapter_version = sa.Column(sa.String(64), nullable=True)
    rendered_prompt = sa.Column(sa.Text(), nullable=False)
    created_at = sa.Column(sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)

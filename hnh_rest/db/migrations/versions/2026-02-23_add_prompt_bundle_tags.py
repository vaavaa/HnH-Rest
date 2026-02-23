"""add prompt_bundle tags (bundle-model-tags)

Revision ID: b5f6a1b2c3d4
Revises: a1b2c3d4e5f6
Create Date: 2026-02-23

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "b5f6a1b2c3d4"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "prompt_bundle",
        sa.Column("tags", JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")),
    )


def downgrade() -> None:
    op.drop_column("prompt_bundle", "tags")

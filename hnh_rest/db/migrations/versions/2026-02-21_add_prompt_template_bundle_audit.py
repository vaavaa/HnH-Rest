"""add_prompt_template_bundle_audit

Revision ID: a1b2c3d4e5f6
Revises: 819cbf6e030b
Create Date: 2026-02-21

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

# revision identifiers, used by Alembic.
revision = "a1b2c3d4e5f6"
down_revision = "819cbf6e030b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Run the migration."""
    op.create_table(
        "prompt_template",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("template_id", sa.String(255), nullable=False),
        sa.Column("semver", sa.String(64), nullable=False),
        sa.Column("role", sa.String(64), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("constraints", JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_prompt_template_template_id", "prompt_template", ["template_id"], unique=False)
    op.create_unique_constraint("uq_prompt_template_id_semver", "prompt_template", ["template_id", "semver"])

    op.create_table(
        "prompt_bundle",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("bundle_id", sa.String(255), nullable=False),
        sa.Column("semver", sa.String(64), nullable=False),
        sa.Column("system_template_id", UUID(as_uuid=True), nullable=False),
        sa.Column("personality_template_id", UUID(as_uuid=True), nullable=False),
        sa.Column("activity_template_id", UUID(as_uuid=True), nullable=False),
        sa.Column("task_template_id", UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["system_template_id"], ["prompt_template.id"]),
        sa.ForeignKeyConstraint(["personality_template_id"], ["prompt_template.id"]),
        sa.ForeignKeyConstraint(["activity_template_id"], ["prompt_template.id"]),
        sa.ForeignKeyConstraint(["task_template_id"], ["prompt_template.id"]),
    )
    op.create_index("ix_prompt_bundle_bundle_id", "prompt_bundle", ["bundle_id"], unique=False)
    op.create_unique_constraint("uq_prompt_bundle_id_semver", "prompt_bundle", ["bundle_id", "semver"])

    op.create_table(
        "prompt_audit",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("bundle_hash", sa.String(64), nullable=False),
        sa.Column("personality_hash", sa.String(64), nullable=False),
        sa.Column("engine_version", sa.String(64), nullable=True),
        sa.Column("adapter_version", sa.String(64), nullable=True),
        sa.Column("rendered_prompt", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_prompt_audit_bundle_hash", "prompt_audit", ["bundle_hash"], unique=False)
    op.create_index("ix_prompt_audit_personality_hash", "prompt_audit", ["personality_hash"], unique=False)


def downgrade() -> None:
    """Undo the migration."""
    op.drop_index("ix_prompt_audit_personality_hash", table_name="prompt_audit")
    op.drop_index("ix_prompt_audit_bundle_hash", table_name="prompt_audit")
    op.drop_table("prompt_audit")
    op.drop_constraint("uq_prompt_bundle_id_semver", "prompt_bundle", type_="unique")
    op.drop_index("ix_prompt_bundle_bundle_id", table_name="prompt_bundle")
    op.drop_table("prompt_bundle")
    op.drop_constraint("uq_prompt_template_id_semver", "prompt_template", type_="unique")
    op.drop_index("ix_prompt_template_template_id", table_name="prompt_template")
    op.drop_table("prompt_template")

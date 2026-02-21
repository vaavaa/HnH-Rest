"""Pydantic schemas for Prompt Spec v1 API."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


# ---- Constraint structure (machine-readable enforcement schema) ----

class ConstraintSchema(BaseModel):
    """Machine-readable persona enforcement constraints. All fields optional."""

    FORBIDDEN_TOKENS: list[str] | None = None
    MAX_SENTENCE_LENGTH: int | None = Field(None, ge=1, le=1000)
    MAX_PARAGRAPHS: int | None = Field(None, ge=1, le=100)
    NO_EMOJI: bool | None = None
    ASSERTIVENESS_LEVEL: float | None = Field(None, ge=0.0, le=1.0)

    model_config = {"extra": "allow"}  # allow future constraint keys


def validate_constraint_structure(value: dict[str, Any] | None) -> dict[str, Any] | None:
    """Validate and normalize constraint dict; returns None for empty/None."""
    if value is None or not value:
        return None
    ConstraintSchema.model_validate(value)
    return value


# ---- Template creation ----

class TemplateCreate(BaseModel):
    """Schema for creating a prompt template."""

    template_id: str = Field(..., min_length=1, max_length=255)
    semver: str = Field(..., min_length=1, max_length=64)
    role: str = Field(..., pattern="^(system|developer|user)$")
    content: str = Field(..., min_length=1)
    constraints: dict[str, Any] | None = None

    model_config = {"extra": "forbid"}

    @model_validator(mode="after")
    def validate_constraint_structure(self) -> "TemplateCreate":
        """Ensure constraints match machine-readable enforcement schema if present."""
        if self.constraints is not None and self.constraints:
            ConstraintSchema.model_validate(self.constraints)
        return self


# ---- Bundle creation ----

class BundleCreate(BaseModel):
    """Schema for creating a prompt bundle (template references)."""

    bundle_id: str = Field(..., min_length=1, max_length=255)
    semver: str = Field(..., min_length=1, max_length=64)
    system_template_id: UUID
    personality_template_id: UUID
    activity_template_id: UUID
    task_template_id: UUID

    model_config = {"extra": "forbid"}


# ---- Render request (Personality Adapter contract) ----

class SemanticTraits(BaseModel):
    """Semantic traits derived from HnH engine (placeholder for hnh-core integration)."""

    model_config = {"extra": "allow"}


class RenderRequest(BaseModel):
    """Request body for POST /v1/prompts/render."""

    bundle_id: str = Field(..., min_length=1)
    bundle_version: str | None = Field(None, alias="semver")
    semantic_traits: dict[str, Any] = Field(default_factory=dict)
    activity_level: float = Field(0.0, ge=0.0, le=1.0)
    stress: float = Field(0.0, ge=0.0, le=1.0)
    task: str = Field("", max_length=4096)

    model_config = {"extra": "forbid", "populate_by_name": True}


# ---- Render response ----

class RenderResponse(BaseModel):
    """Response for POST /v1/prompts/render; deterministic assembly result + audit refs."""

    rendered_prompt: str
    bundle_hash: str
    personality_hash: str
    engine_version: str | None = None
    adapter_version: str | None = None

    model_config = {"extra": "forbid", "validate_assignment": False}


# ---- Response DTOs (read) ----

class TemplateRead(BaseModel):
    """Template as returned by API (read-only DTO)."""

    id: UUID
    template_id: str
    semver: str
    role: str
    content: str
    constraints: dict[str, Any] | None = None

    model_config = {"extra": "forbid", "from_attributes": True, "validate_assignment": False}


class BundleRead(BaseModel):
    """Bundle as returned by API (read-only DTO)."""

    id: UUID
    bundle_id: str
    semver: str
    system_template_id: UUID
    personality_template_id: UUID
    activity_template_id: UUID
    task_template_id: UUID

    model_config = {"extra": "forbid", "from_attributes": True, "validate_assignment": False}


class AuditRead(BaseModel):
    """Audit record as returned by API (read-only DTO)."""

    id: UUID
    bundle_hash: str
    personality_hash: str
    engine_version: str | None
    adapter_version: str | None
    rendered_prompt: str

    model_config = {"extra": "forbid", "from_attributes": True, "validate_assignment": False}

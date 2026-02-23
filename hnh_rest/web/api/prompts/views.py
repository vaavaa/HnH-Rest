"""Prompts API v1 — Prompt Registry & Renderer endpoints."""

import logging
import time
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from hnh_rest.db.dependencies import get_db_session
from hnh_rest.db.models.prompt_audit import PromptAudit
from hnh_rest.services.prompts import AuditService, BundleService, RendererService, TemplateService
from hnh_rest.web.api.prompts.metrics import prompt_render_latency_seconds, render_errors_total
from hnh_rest.web.api.prompts.schema import (
    AuditRead,
    BundleCreate,
    BundleRead,
    RenderRequest,
    RenderResponse,
    TemplateCreate,
    TemplateRead,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/prompts", tags=["prompts"])
router_audit = APIRouter(prefix="/v1/audit", tags=["audit"])


def _template_svc(session: AsyncSession = Depends(get_db_session)) -> TemplateService:
    return TemplateService(session)


def _bundle_svc(session: AsyncSession = Depends(get_db_session)) -> BundleService:
    return BundleService(session)


def _renderer_svc(session: AsyncSession = Depends(get_db_session)) -> RendererService:
    return RendererService(session)


def _audit_svc(session: AsyncSession = Depends(get_db_session)) -> AuditService:
    return AuditService(session)


@router.post("/templates", response_model=TemplateRead, status_code=201)
async def create_template(
    body: TemplateCreate,
    svc: TemplateService = Depends(_template_svc),
) -> TemplateRead:
    """Create a prompt template. Conflict if (template_id, semver) already exists."""
    if await svc.get_by_template_id_semver(body.template_id, body.semver) is not None:
        raise HTTPException(409, detail="Template with this template_id and semver already exists")
    try:
        template = await svc.create(
            template_id=body.template_id,
            semver=body.semver,
            role=body.role,
            content=body.content,
            constraints=body.constraints,
        )
        return TemplateRead.model_validate(template)
    except IntegrityError:
        raise HTTPException(409, detail="Template with this template_id and semver already exists")


@router.delete("/templates/{template_id}", status_code=204)
async def delete_template(
    template_id: UUID,
    svc: TemplateService = Depends(_template_svc),
    bundle_svc: BundleService = Depends(_bundle_svc),
) -> None:
    """Delete a template. Conflict if any bundle references this template."""
    if await bundle_svc.is_template_used(template_id):
        raise HTTPException(
            409,
            detail="Cannot delete template: one or more bundles reference this template",
        )
    deleted = await svc.delete_by_id(template_id)
    if not deleted:
        raise HTTPException(404, detail="Template not found")


@router.post("/bundles", response_model=BundleRead, status_code=201)
async def create_bundle(
    body: BundleCreate,
    svc: BundleService = Depends(_bundle_svc),
    template_svc: TemplateService = Depends(_template_svc),
) -> BundleRead:
    """Create a prompt bundle (immutable once created). All template IDs must exist. Conflict if (bundle_id, semver) exists."""
    for tid in (
        body.system_template_id,
        body.personality_template_id,
        body.activity_template_id,
        body.task_template_id,
    ):
        if await template_svc.get_by_id(tid) is None:
            raise HTTPException(404, detail=f"Template not found: {tid}")
    if await svc.exists(body.bundle_id, body.semver):
        raise HTTPException(409, detail="Bundle with this bundle_id and semver already exists")
    try:
        bundle = await svc.create(
            bundle_id=body.bundle_id,
            semver=body.semver,
            system_template_id=body.system_template_id,
            personality_template_id=body.personality_template_id,
            activity_template_id=body.activity_template_id,
            task_template_id=body.task_template_id,
        )
        return BundleRead.model_validate(bundle)
    except IntegrityError:
        raise HTTPException(409, detail="Bundle with this bundle_id and semver already exists")


@router.get("/bundles/{bundle_id}", response_model=BundleRead)
async def get_bundle(
    bundle_id: str,
    semver: str,
    svc: BundleService = Depends(_bundle_svc),
) -> BundleRead:
    """Get a bundle by bundle_id and semver."""
    bundle = await svc.get_by_bundle_id_semver(bundle_id, semver)
    if bundle is None:
        raise HTTPException(404, detail="Bundle not found")
    return BundleRead.model_validate(bundle)


@router.post("/render", response_model=RenderResponse)
async def render_prompt(
    body: RenderRequest,
    renderer: RendererService = Depends(_renderer_svc),
    audit_svc: AuditService = Depends(_audit_svc),
) -> RenderResponse:
    """Render a prompt: deterministic assembly (system → personality → activity → task), then audit."""
    semver = body.bundle_version or "0.1.0"
    t0 = time.perf_counter()
    try:
        rendered_prompt, bundle_hash, personality_hash = await renderer.render(
            bundle_id=body.bundle_id,
            semver=semver,
            semantic_traits=body.semantic_traits,
            activity_level=body.activity_level,
            stress=body.stress,
            task=body.task,
        )
    except ValueError as e:
        render_errors_total.inc()
        logger.warning("Render failed: %s", e)
        raise HTTPException(404, detail=str(e))
    elapsed = time.perf_counter() - t0
    prompt_render_latency_seconds.observe(elapsed)
    logger.info("Render completed in %.3fs bundle_id=%s semver=%s", elapsed, body.bundle_id, semver)
    await audit_svc.create(
        bundle_hash=bundle_hash,
        personality_hash=personality_hash,
        rendered_prompt=rendered_prompt,
    )
    return RenderResponse(
        rendered_prompt=rendered_prompt,
        bundle_hash=bundle_hash,
        personality_hash=personality_hash,
    )


@router_audit.get("/{bundle_hash}", response_model=AuditRead)
async def get_audit_by_bundle_hash(
    bundle_hash: str,
    session: AsyncSession = Depends(get_db_session),
) -> AuditRead:
    """Get latest audit record by bundle_hash (for replay)."""
    result = await session.execute(
        select(PromptAudit).where(PromptAudit.bundle_hash == bundle_hash).order_by(PromptAudit.created_at.desc()).limit(1)
    )
    row = result.scalar_one_or_none()
    if row is None:
        raise HTTPException(404, detail="Audit record not found")
    return AuditRead.model_validate(row)

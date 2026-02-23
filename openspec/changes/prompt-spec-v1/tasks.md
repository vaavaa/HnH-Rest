# Implementation Tasks — Prompt Spec v1

---

# Phase 1 — Models

- [x] Create SQLAlchemy models for PromptTemplate
- [x] Create SQLAlchemy models for PromptBundle
- [x] Create SQLAlchemy models for PromptAudit
- [x] Generate Alembic migration
- [x] Add DB indexes:
  - template_id + semver (unique)
  - bundle_id + semver (unique)
  - bundle_hash (indexed; audit table allows multiple rows per bundle_hash for replay)
  - personality_hash (indexed)

---

# Phase 2 — Schemas

- [x] Create Pydantic schema for template creation
- [x] Create schema for bundle creation
- [x] Create render request schema
- [x] Create render response schema
- [x] Validate constraint structure (machine-readable enforcement schema)

---

# Phase 3 — Services

- [x] Implement TemplateService
- [x] Implement BundleService
- [x] Implement RendererService
- [x] Implement AuditService
- [x] Ensure deterministic assembly order
- [x] Prevent mutation of published bundles

---

# Phase 4 — API

- [x] Add router under web/api/prompts
- [x] Register router in router.py
- [x] Use ORJSONResponse as default response class
- [x] Ensure strict response_model enforcement

---

# Phase 5 — Determinism & Replay

- [x] Snapshot test for deterministic render
- [x] Bundle immutability test
- [x] Constraint validation test
- [x] Replay consistency test
- [x] Hash stability test (rendered prompt hash identical across runs)

Coverage target: >= 98%

---

# Phase 6 — Performance & Optimization

## JSON & Serialization

- [x] Replace default JSON encoder with orjson
- [x] Set FastAPI default_response_class = ORJSONResponse
- [x] Ensure all large responses use ORJSONResponse explicitly
- [x] Avoid unnecessary dict() → json → dict() conversions
- [x] Avoid double serialization inside services

## Loop & Assembly Optimization

- [x] Avoid dynamic string concatenation in loops
- [x] Use preallocated list + "\n\n".join(parts)
- [x] Precompile template placeholders if using format()
- [x] Avoid repeated constraint parsing — pre-normalize constraints on insert
- [ ] Cache compiled constraint rules in memory (read-only LRU cache) — deferred (no expensive compilation in v1)

## Database

- [x] Switch to async SQLAlchemy engine
- [x] Use async session dependency
- [x] Use connection pooling (configure pool_size, max_overflow)
- [ ] Add read-only transaction mode for render endpoint — skipped (render does INSERT for audit)
- [x] Ensure indexed lookups for bundle resolution
- [x] Avoid N+1 queries in bundle loading

## Redis (if enabled)

- [ ] Cache frequently used bundles by (bundle_id, semver)
- [ ] Cache template resolution
- [ ] Add TTL-based caching for high-frequency render calls

## CPU / Memory

- [x] Avoid deepcopy in renderer
- [x] Avoid unnecessary Pydantic model reconstruction
- [x] Use Pydantic v2 model_config with:
      - validate_assignment=False (where safe)
      - arbitrary_types_allowed=False
- [x] Use frozen dataclasses for internal assembly structures

## Logging & Monitoring

- [x] Log render latency
- [ ] Log DB query time — deferred
- [x] Add Prometheus metrics:
      - prompt_render_latency_seconds
      - bundle_cache_hits_total
      - render_errors_total
- [x] Add percentile tracking (p50, p95, p99) — via histogram buckets

---

# Phase 7 — Concurrency & Scalability

- [x] Ensure all DB calls are async
- [x] Ensure Redis calls are async
- [x] Avoid blocking CPU in request path
- [ ] Benchmark render endpoint under load (locust or k6)
- [ ] Validate no race condition when publishing bundle versions

---

# Phase 8 — Security & Integrity

- [x] Prevent overwriting existing semver
- [x] Validate semver format strictly
- [x] Prevent template deletion if used by active bundle
- [x] Validate constraint schema before DB insert
- [x] Protect audit records from mutation

---

# Phase 9 — Version Control Discipline

- [ ] Create feature branch: feature/prompt-spec-v1
- [ ] Commit OpenSpec artifacts before implementation
- [ ] Commit each phase separately
- [ ] Do not modify spec after implementation begins (unless new change)
- [ ] All commits must reference change-id: prompt-spec-v1


# Future (not in v1 but tracked)

- [ ] MCP adapter layer
- [ ] Prompt diff tool
- [ ] Automated regression validator against LLM outputs
- [ ] Persona drift detector

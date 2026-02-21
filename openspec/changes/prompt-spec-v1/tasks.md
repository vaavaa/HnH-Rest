# Implementation Tasks — Prompt Spec v1

---

# Phase 1 — Models

- [ ] Create SQLAlchemy models for PromptTemplate
- [ ] Create SQLAlchemy models for PromptBundle
- [ ] Create SQLAlchemy models for PromptAudit
- [ ] Generate Alembic migration
- [ ] Add DB indexes:
  - template_id + semver (unique)
  - bundle_id + semver (unique)
  - bundle_hash (unique)
  - personality_hash (indexed)

---

# Phase 2 — Schemas

- [ ] Create Pydantic schema for template creation
- [ ] Create schema for bundle creation
- [ ] Create render request schema
- [ ] Create render response schema
- [ ] Validate constraint structure (machine-readable enforcement schema)

---

# Phase 3 — Services

- [ ] Implement TemplateService
- [ ] Implement BundleService
- [ ] Implement RendererService
- [ ] Implement AuditService
- [ ] Ensure deterministic assembly order
- [ ] Prevent mutation of published bundles

---

# Phase 4 — API

- [ ] Add router under web/api/prompts
- [ ] Register router in router.py
- [ ] Use ORJSONResponse as default response class
- [ ] Ensure strict response_model enforcement

---

# Phase 5 — Determinism & Replay

- [ ] Snapshot test for deterministic render
- [ ] Bundle immutability test
- [ ] Constraint validation test
- [ ] Replay consistency test
- [ ] Hash stability test (rendered prompt hash identical across runs)

Coverage target: >= 98%

---

# Phase 6 — Performance & Optimization

## JSON & Serialization

- [ ] Replace default JSON encoder with orjson
- [ ] Set FastAPI default_response_class = ORJSONResponse
- [ ] Ensure all large responses use ORJSONResponse explicitly
- [ ] Avoid unnecessary dict() → json → dict() conversions
- [ ] Avoid double serialization inside services

## Loop & Assembly Optimization

- [ ] Avoid dynamic string concatenation in loops
- [ ] Use preallocated list + "\n\n".join(parts)
- [ ] Precompile template placeholders if using format()
- [ ] Avoid repeated constraint parsing — pre-normalize constraints on insert
- [ ] Cache compiled constraint rules in memory (read-only LRU cache)

## Database

- [ ] Switch to async SQLAlchemy engine
- [ ] Use async session dependency
- [ ] Use connection pooling (configure pool_size, max_overflow)
- [ ] Add read-only transaction mode for render endpoint
- [ ] Ensure indexed lookups for bundle resolution
- [ ] Avoid N+1 queries in bundle loading

## Redis (if enabled)

- [ ] Cache frequently used bundles by (bundle_id, semver)
- [ ] Cache template resolution
- [ ] Add TTL-based caching for high-frequency render calls

## CPU / Memory

- [ ] Avoid deepcopy in renderer
- [ ] Avoid unnecessary Pydantic model reconstruction
- [ ] Use Pydantic v2 model_config with:
      - validate_assignment=False (where safe)
      - arbitrary_types_allowed=False
- [ ] Use frozen dataclasses for internal assembly structures

## Logging & Monitoring

- [ ] Log render latency
- [ ] Log DB query time
- [ ] Add Prometheus metrics:
      - prompt_render_latency_seconds
      - bundle_cache_hits_total
      - render_errors_total
- [ ] Add percentile tracking (p50, p95, p99)

---

# Phase 7 — Concurrency & Scalability

- [ ] Ensure all DB calls are async
- [ ] Ensure Redis calls are async
- [ ] Avoid blocking CPU in request path
- [ ] Benchmark render endpoint under load (locust or k6)
- [ ] Validate no race condition when publishing bundle versions

---

# Phase 8 — Security & Integrity

- [ ] Prevent overwriting existing semver
- [ ] Validate semver format strictly
- [ ] Prevent template deletion if used by active bundle
- [ ] Validate constraint schema before DB insert
- [ ] Protect audit records from mutation

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

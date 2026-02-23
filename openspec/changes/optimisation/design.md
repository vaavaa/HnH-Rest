# Design — Optimisation (performance + non-DB generator)

**Change ID**: `optimisation`  
**Branch**: `spec/optimisation`

Before implementing, read the project-level spec `openspec/specs/000-repo-and-deps.md` and the Prompt Spec v1 design/spec for data model and constraints.

---

## 1. Current baseline (from Prompt Spec v1)

- PromptTemplates + PromptBundles + Render + Audit.
- Fixed assembly order: system → personality → activity → task.
- Determinism contract (identical inputs → identical prompt text + hash).
- Renderer uses `_RenderContext` (dataclass) for substitution; assembly already uses a list of parts and a single `"\n\n".join(parts)`.
- Constraints: machine-readable structure per prompt-spec (see `openspec/changes/prompt-spec-v1/specs/prompt-spec/spec.md`); stored in template `constraints` (jsonb). Pre-normalisation at insertion time is from prompt-spec-v1; this change adds optional compiled representation and caching.

---

## 2. Proposed structure

### 2.1 New “sources” layer (thin adapters)

```
hnh_rest/services/prompts/
  renderer.py              # pure deterministic assembly (unchanged contract; internal use orjson where needed)
  prompt_generator.py       # orchestration: sources + renderer + audit
  sources/
    db.py                   # DbBundleSource, DbTemplateSource
    inline.py               # InlineBundleSource, InlineTemplateSource
  audit/
    db.py                   # DbAuditSink
    null.py                 # NullAuditSink
```

### 2.2 Reuse existing services

- Existing template/bundle DB access can be wrapped by `Db*Source`.
- The renderer stays pure and stateless; internal context remains a dataclass (e.g. `_RenderContext`) — avoid Pydantic in the inner render loop.
- Constraints: format and semantics are defined in Prompt Spec v1. “Compiled” representation here means a normalised/cacheable form of that structure (e.g. for fast validation); cache key by template/bundle identity.

### 2.3 Performance checklist

- ORJSONResponse as default (already in app); ensure prompts routes use it where appropriate; replace any `json.dumps`/`json.loads` in the render path with orjson.
- No string concatenation inside loops for assembly; keep `list.append` + single `"\n\n".join(parts)`.
- Pre-normalise constraints at insertion time (per prompt-spec-v1); cache compiled/normalised constraint structure in a bounded LRU, safe for async.
- Use async SQLAlchemy; one bundle query + one batched template query (or single join); explicit columns where it helps; rely on existing indexes for `(bundle_id, semver)` and `(template_id, semver)`.
- Optional: tune pool settings (pool_size, max_overflow) in settings for local dev.

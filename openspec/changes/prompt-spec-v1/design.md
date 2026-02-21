# Design — Prompt Registry & Renderer Service

## 1. Architecture

HnH Engine
    ↓
PersonalityAdapter
    ↓
PromptRenderer (this service)
    ↓
LLM

---

## 2. Service Responsibilities

The FastAPI service MUST:

1. Store PromptTemplates.
2. Store PromptBundles.
3. Render prompt packages.
4. Validate constraints.
5. Log audit records.
6. Guarantee deterministic assembly.

---

## 3. API Endpoints

POST /v1/prompts/templates
POST /v1/prompts/bundles
POST /v1/prompts/render
GET  /v1/prompts/bundles/{bundle_id}
GET  /v1/audit/{hash}

---

## 4. Database Models

### PromptTemplateModel
- id (UUID)
- template_id (str)
- semver (str)
- role (str)
- content (text)
- constraints (jsonb)
- created_at

### PromptBundleModel
- id (UUID)
- bundle_id (str)
- semver (str)
- system_template_id
- personality_template_id
- activity_template_id
- task_template_id
- created_at

### PromptAuditModel
- id (UUID)
- bundle_hash
- personality_hash
- engine_version
- adapter_version
- rendered_prompt (text)
- created_at

---

## 5. Deterministic Assembly

Assembly order MUST be fixed:

1. System template
2. Personality template
3. Activity template
4. Task template

Final prompt = "\n\n".join(parts)

No random tokens allowed.
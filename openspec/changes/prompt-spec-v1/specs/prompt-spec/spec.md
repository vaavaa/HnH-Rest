# Prompt Spec v1

## 1. Core Concepts

### 1.1 PromptTemplate

A versioned template unit.

Fields:
- template_id (string)
- semver (string)
- role (system|developer|user)
- content (string)
- constraints (structured rules)
- adapter_version (string)

### 1.2 PromptBundle

A deterministic assembly of templates.

Fields:
- bundle_id
- bundle_version (semver)
- system_template_id
- personality_template_id
- activity_template_id
- task_template_id

Bundle MUST be immutable once published.

---

## 2. Persona Enforcement Contract

LLM behavior MUST be governed by constraints.

Constraints override descriptive personality text.

Examples:

- FORBIDDEN_TOKENS: ["!", "extremely", "absolutely"]
- MAX_SENTENCE_LENGTH: 25 words
- MAX_PARAGRAPHS: 4
- NO_EMOJI: true
- ASSERTIVENESS_LEVEL: 0.4

Constraints MUST be machine-readable.

---

## 3. Personality Adapter Contract

LLM MUST NOT receive raw vector_32.

Input to prompt layer:

{
  "semantic_traits": {...},
  "activity_level": float,
  "stress": float,
  "task": string
}

Semantic traits MUST be derived from HnH engine.

---

## 4. Determinism

Given identical:

- personality_hash
- bundle_version
- adapter_version
- task_input

The rendered prompt MUST be identical.

---

## 5. Audit & Replay

Each rendered prompt MUST produce:

- prompt_bundle_hash
- personality_hash
- engine_version
- adapter_version
- created_at (ISO8601)

Replay MUST reconstruct identical prompt text.
# HnH-Rest — Source of Truth & Dependencies (SDD Addendum)

## 1) Where the REST module lives (Source of Truth)
**HnH-Rest is the canonical REST implementation.**
- The REST service code is located in this repository under the Python package: `hnh_rest/`.
- This repository is the primary (source-of-truth) for:
  - Prompt Registry + deterministic prompt rendering
  - Persona enforcement contracts
  - Audit/replay-friendly rendering pipeline

Practical takeaway:
- “Get REST” == clone/install **this** repo (HnH-Rest) and run the app from `hnh_rest/`.

## 2) Relationship to HnH-Core
HnH-Rest depends on HnH-Core as the personality engine.
- HnH-Core provides personality state computation (natal/transits/params/etc).
- HnH-Rest consumes that state and enforces how it is delivered to LLM prompts.

Import / module naming:
- HnH-Core Python module is expected to be imported as `hnh` (repo contains `hnh/`).
- HnH-Rest module is `hnh_rest` (repo contains `hnh_rest/`).

## 3) How to obtain/install dependencies (Development)
### Option A — two repos side-by-side (editable installs)
Recommended for active development:

1) Clone both repos рядом:
   - ../HnH-Core
   - ../HnH-Rest

2) Install core in editable mode, then rest:
   - `pip install -e ../HnH-Core`
   - `pip install -e .`  (inside HnH-Rest)

### Option B — pin HnH-Core by git tag/commit (reproducible)
Use when you want deterministic builds:

- `pip install "hnh-core @ git+https://github.com/vaavaa/HnH-Core@<tag_or_commit>"`
- `pip install -e .` (or build an image)

## 4) Production dependency policy (must be explicit)
HnH-Rest MUST pin HnH-Core:
- Either `hnh-core==X.Y.Z` (PyPI release)
- Or VCS pin `@<tag_or_commit>`
Rationale: prompt rendering must be reproducible and replayable, so dependency drift is unacceptable.

## 5) Versioning contract between Core and Rest
- HnH-Core follows SemVer (initially 0.y.z is OK).
- HnH-Rest pins compatible ranges:
  - if stable: `>=X.Y,<X.(Y+1)`
  - if early: pin to an exact tag/commit
Breaking changes in core must trigger a version bump + explicit rest update.
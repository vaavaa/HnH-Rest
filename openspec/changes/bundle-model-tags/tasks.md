# Implementation Tasks — Bundle Model Tags

---

# Phase 1 — Database

- [x] Добавить в модель `PromptBundle` поле `tags` (JSONB, not null, server_default `'[]'::jsonb`)
- [x] Создать миграцию Alembic: добавить столбец `tags`, для существующих строк установить `[]`
- [ ] При необходимости: GIN-индекс по `tags` для фильтрации (по объёму данных)

---

# Phase 2 — Schemas & validation

- [x] В `BundleCreate` добавить `tags: list[str] | None = None`; нормализация: уникальные непустые строки, max length тега (например 64)
- [x] В `BundleRead` добавить `tags: list[str]`
- [x] В `RenderRequest` добавить `model_type: str | None = None`

---

# Phase 3 — Services

- [x] BundleService.create: сохранять нормализованный `tags`
- [x] В месте разрешения бандла для render: при переданном непустом `model_type` проверять вхождение в `bundle.tags`; при отсутствии — исключение для маппинга в 400 с телом `{ "detail": "...", "code": "bundle_unsupported_model" }`

---

# Phase 4 — API

- [x] POST /v1/prompts/bundles: принимать `tags`, возвращать в ответе созданный бандл с `tags`
- [x] GET /v1/prompts/bundles/{bundle_id}: включать `tags` в ответ; опционально — query `?model_type=...` для фильтрации версий по тегу
- [x] POST /v1/prompts/render: принимать `model_type`, применять фильтрацию по тегу; при несовпадении — 400 с телом ошибки по формату из design (detail + code `bundle_unsupported_model`)

---

# Phase 5 — Tests

- [x] Создание бандла с `tags` и без; чтение бандла с `tags`
- [x] Render без `model_type` — поведение как раньше (в т.ч. бандл с `tags=[]`)
- [x] Render с `model_type`, совпадающим с тегом бандла — успех
- [x] Render с `model_type`, отсутствующим в `tags` бандла — 400 с телом detail + code `bundle_unsupported_model`
- [x] Render с пустой строкой `model_type` — проверка по тегам не выполняется (успех при найденном бандле)
- [x] Миграция: существующие бандлы с `tags=[]`; старые клиенты без `model_type` продолжают работать

---

# Branch & commits

- [ ] Ветка: `spec/bundle-model-tags` (или feature/bundle-model-tags по правилам репо)
- [ ] Каждый коммит с change-id: bundle-model-tags

# Performance — замер после перехода на xxhash (xxh3_128)

**Change ID**: `optimisation`  
**Относится к**: основной baseline в `perf_baseline.md`

Хеши в render path переведены с SHA-256 на xxh3_128 (библиотека `xxhash`). Замер — те же параметры Locust, что и в основном baseline.

## Параметры прогона

- **Command**: `uv run locust -f benchmarks/locustfile.py --host=http://localhost:8800 --headless -u 20 -r 5 -t 60s`
- **Date**: 2026-02-23

## Результаты (Aggregated)

| Метрика | Значение |
|--------|----------|
| **Total requests** | 3740 |
| **Failures** | 0 |
| **RPS** | 62.45 |
| **p50 (Med)** | 12 ms |
| **p95** | 22 ms |
| **p99** | 29 ms |
| **Avg** | 11 ms |
| **Min / Max** | 2 / 91 ms |

## Сравнение с предыдущим замером (orjson, до xxhash)

| Метрика | До xxhash | С xxh3_128 |
|--------|-----------|------------|
| Запросов за 60 s | 3727 | 3740 |
| RPS | 62.23 | 62.45 |
| p50 | 11 ms | 12 ms |
| p95 | 23 ms | 22 ms |
| p99 | 30 ms | 29 ms |

Разница в пределах погрешности одного прогона; p95/p99 чуть ниже с xxhash.

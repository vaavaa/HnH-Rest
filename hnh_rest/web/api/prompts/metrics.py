"""Prometheus metrics for Prompt Registry & Renderer."""

from prometheus_client import Counter, Histogram

prompt_render_latency_seconds = Histogram(
    "prompt_render_latency_seconds",
    "Time spent rendering a prompt",
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
)
render_errors_total = Counter(
    "render_errors_total",
    "Total render errors (e.g. bundle not found)",
)
bundle_cache_hits_total = Counter(
    "bundle_cache_hits_total",
    "Bundle cache hits (when cache is enabled)",
)

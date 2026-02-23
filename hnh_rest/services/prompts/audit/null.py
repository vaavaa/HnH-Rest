"""Null audit sink — no-op for inline / test usage."""


class NullAuditSink:
    """Audit sink that does nothing. Does not affect prompt hash."""

    async def record(
        self,
        bundle_hash: str,
        personality_hash: str,
        rendered_prompt: str,
        engine_version: str | None = None,
        adapter_version: str | None = None,
    ) -> None:
        """No-op."""
        pass

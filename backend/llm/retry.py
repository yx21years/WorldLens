"""Retry logic for LLM calls — stub for Phase 2."""


async def with_retry(func, max_retries: int = 3, backoff_base: float = 1.0):
    """Exponential backoff retry wrapper. Full implementation in Phase 2."""
    return await func()

class WorldLensError(Exception):
    """Base error for WorldLens AI."""

    def __init__(self, message: str, code: str = "UNKNOWN"):
        self.message = message
        self.code = code
        super().__init__(self.message)


class CollectionError(WorldLensError):
    """Errors during news collection."""
    pass


class SourceUnavailableError(CollectionError):
    """A news source is temporarily unreachable."""

    def __init__(self, source_name: str):
        super().__init__(f"Source '{source_name}' is unavailable", code="SOURCE_UNAVAILABLE")


class FetchTimeoutError(CollectionError):
    """HTTP request to a source timed out."""

    def __init__(self, source_name: str):
        super().__init__(f"Fetch timeout for source '{source_name}'", code="FETCH_TIMEOUT")


class FilterRejectionError(CollectionError):
    """An article was rejected by the quality filter."""

    def __init__(self, reason: str):
        super().__init__(f"Article filtered: {reason}", code="FILTER_REJECTED")


class LLMError(WorldLensError):
    """Errors from LLM provider interactions."""
    pass


class LLMProviderError(LLMError):
    """LLM provider API call failed."""

    def __init__(self, provider: str, detail: str):
        super().__init__(f"LLM provider '{provider}' error: {detail}", code="LLM_PROVIDER_ERROR")


class LLMRateLimitError(LLMError):
    """LLM provider rate limit exceeded."""

    def __init__(self, provider: str):
        super().__init__(f"Rate limit exceeded for '{provider}'", code="LLM_RATE_LIMIT")


class LLMResponseValidationError(LLMError):
    """LLM response did not match expected schema."""

    def __init__(self, detail: str):
        super().__init__(f"LLM response validation failed: {detail}", code="LLM_RESPONSE_INVALID")


class BriefingError(WorldLensError):
    """Errors during briefing generation."""
    pass


class BriefingGenerationError(BriefingError):
    """Failed to generate a daily briefing."""

    def __init__(self, detail: str):
        super().__init__(f"Briefing generation failed: {detail}", code="BRIEFING_GENERATION_ERROR")

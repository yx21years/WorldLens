import structlog


import structlog


def setup_logging(log_level: str = "INFO"):
    # Map log level strings to structlog-compatible integer levels
    level_map = {"DEBUG": 10, "INFO": 20, "WARNING": 30, "ERROR": 40, "CRITICAL": 50}
    level = level_map.get(log_level.upper(), 20)

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer() if log_level.upper() == "DEBUG" else structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = "worldlens"):
    return structlog.get_logger(name)


class KeyMasker:
    """Mask sensitive fields (API keys) in log output."""

    SENSITIVE_KEYS = {"LLM_API_KEY", "NEWSAPI_KEY", "api_key", "key", "token"}

    def __call__(self, logger, method_name, event_dict):
        for key in self.SENSITIVE_KEYS:
            if key in event_dict:
                val = event_dict[key]
                if isinstance(val, str) and len(val) > 4:
                    event_dict[key] = val[:4] + "****"
                else:
                    event_dict[key] = "****"
        return event_dict

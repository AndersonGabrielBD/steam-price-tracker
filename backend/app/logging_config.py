"""JSON structured logging, shared by the FastAPI process and the Celery
worker/beat processes. Each log line is a machine-parseable event instead of
a free-form string -- e.g. `logger.warning("game_not_found", appid=appid)`
instead of `"game %s not found" % appid`.
"""

import logging

import structlog


def configure_logging() -> None:
    logging.basicConfig(format="%(message)s", level=logging.INFO)
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

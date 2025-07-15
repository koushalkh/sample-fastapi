import logging
import sys
import structlog
from app.core.config import settings
from structlog.contextvars import merge_contextvars

def setup_logging():
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=settings.log_level,
    )

    structlog.configure(
        processors=[
            merge_contextvars, # This should be first
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.TimeStamper(key="@timestamp", fmt="iso"),
            structlog.processors.UnicodeDecoder(),
            structlog.stdlib.filter_by_level,
            structlog.processors.JSONRenderer(),
        ],
        context_class=structlog.threadlocal.wrap_dict(dict),
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter_with_context = structlog.stdlib.ProcessorFormatter(
        processor=structlog.processors.JSONRenderer(),
        foreign_pre_chain=[
            merge_contextvars, # This should be first
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.TimeStamper(key="@timestamp", fmt="iso"),
            structlog.processors.UnicodeDecoder(),
        ]
    )

    # Add context vars to log messages by below loggers
    for logger in ["uvicorn.access", "fastapi", "uvicorn", "uvicorn.error"]:
        log = logging.getLogger(logger)
        for h in log.handlers:  # pragma: no cover
            h.setFormatter(formatter_with_context)

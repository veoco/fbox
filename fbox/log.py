import logging

from pydantic import BaseModel

from fbox import settings


class LogConfig(BaseModel):
    LOGGER_NAME: str = "fbox"
    LOG_FORMAT: str = "%(levelprefix)s - %(message)s"
    LOG_LEVEL: str = "DEBUG" if settings.DEBUG else "INFO"

    version = 1
    disable_existing_loggers = False
    formatters = {
        "default": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": LOG_FORMAT,
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    }
    handlers = {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stderr",
        },
    }
    loggers = {
        LOGGER_NAME: {"handlers": ["default"], "level": LOG_LEVEL},
    }


logging.config.dictConfig(LogConfig().dict())
logger = logging.getLogger("fbox")

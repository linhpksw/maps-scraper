import logging.config

from pydantic import BaseSettings

class Settings(BaseSettings):
    class Config:
        env_file = ".env"


LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": True,
    "formatters": {
        "default": {
            "format": "%(message)s",
            "datefmt": "[%X]",
        }
    },
    "handlers": {
        "rich": {
            "level": "INFO",
            "formatter": "default",
            "class": "rich.logging.RichHandler",
            "rich_tracebacks": True,
        },
    },
    "root": {
        "level": "INFO",
        "handlers": ["rich"],
    },
}
logging.config.dictConfig(LOGGING_CONFIG)


settings = Settings()
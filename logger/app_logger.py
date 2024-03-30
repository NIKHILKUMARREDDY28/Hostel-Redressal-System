from loguru import logger as loguru_logger
from typing import Any

class AppLogger:
    def __init__(self):
        loguru_logger.add("logfile.log", rotation="1 day", retention="10 days",
                          format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                                 "<level>{level: <8}</level> | "
                                 "<cyan>{file}</cyan>:<cyan>{name}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>")

    async def log_info(self, *args: Any, **kwargs: Any):
        message = " ".join(map(str, args))
        loguru_logger.opt(depth=1).info(message, **kwargs)
        await loguru_logger.complete()

    def log_info_sync(self, *args: Any, **kwargs: Any):
        message = " ".join(map(str, args))
        loguru_logger.opt(depth=1).info(message, **kwargs)

    async def log_error(self, *args: Any, **kwargs: Any):
        message = " ".join(map(str, args))
        loguru_logger.opt(depth=1).error(message, **kwargs)
        await loguru_logger.complete()

    async def log_debug(self, *args: Any, **kwargs: Any):
        message = " ".join(map(str, args))
        loguru_logger.opt(depth=1).debug(message, **kwargs)
        await loguru_logger.complete()

    async def log_warning(self, *args: Any, **kwargs: Any):
        message = " ".join(map(str, args))
        loguru_logger.opt(depth=1).warning(message, **kwargs)
        await loguru_logger.complete()

# Global logger instance
app_logger = AppLogger()

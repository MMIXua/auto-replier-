
from __future__ import annotations
from loguru import logger as _logger
import loguru
import sys

from config import LOGS_PATH, LOG_LEVEL


log: loguru.Logger | None = None


if log is None:
    LOGS_PATH = LOGS_PATH.format(module="base")
    fmt = "<g>{time}</> | <lvl>{level}</> | <c>{extra[classname]}:{function}:{line}</> - {message}"
    _logger.remove()
    _logger.configure(extra={"classname": "None"})
    _logger.add(LOGS_PATH, backtrace=True, diagnose=True, level="DEBUG", format=fmt, rotation="1 day")
    _logger.add(sys.stdout, backtrace=True, diagnose=True, level=LOG_LEVEL, format=fmt)
    _logger.info("Started logging successfully")
    log = _logger

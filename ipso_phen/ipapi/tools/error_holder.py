import os
from typing import Any, Union
from datetime import datetime as dt
import logging


ERR_LVL_EXCEPTION = 35

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))


def error_level_to_str(error_level: int) -> str:
    if error_level == logging.INFO:
        return "INFO"
    elif error_level == logging.WARNING:
        return "WARNING"
    elif error_level == ERR_LVL_EXCEPTION:
        return "EXCEPTION"
    elif error_level == logging.ERROR:
        return "ERROR"
    elif error_level == logging.CRITICAL:
        return "CRITICAL"
    else:
        return "UNKNOWN"


def error_level_to_logger(error_level: int, target_logger):
    if error_level == logging.INFO:
        return target_logger.info
    elif error_level == logging.INFO:
        return target_logger.info
    elif error_level == logging.WARNING:
        return target_logger.warning
    elif error_level == ERR_LVL_EXCEPTION:
        return target_logger.exception
    elif error_level == logging.ERROR:
        return target_logger.error
    elif error_level == logging.CRITICAL:
        return target_logger.critical
    else:
        return target_logger.info


def log_data(log_msg: str, log_level: int, target_logger) -> int:
    """Logs msg at desired level with target logger and retruns level

    Args:
        log_msg (str): Message to be logged
        log_level (Union[int, str]): log level
        target_logger (function): logger to be used

    Returns:
        int: Log level as understood by logging unit
    """
    error_level_to_logger(error_level=log_level, target_logger=target_logger)(log_msg)
    return log_level


class ErrorHolder(object):
    def __init__(self, owner: Any, errors: tuple = (), **kwargs):
        for err_dict in errors:
            new_error_text = err_dict.get("text", "")
            if new_error_text:
                error_level_to_logger(
                    error_level=err_dict.get("level", logging.INFO),
                    target_logger=err_dict.get("logger", logger),
                )(new_error_text)

    def __str__(self):
        logger.warning("ErrorHolder - Deprecated class - called method: __str__")
        return "This class is now an empty shell, please use logger instead"

    def __repr__(self):
        logger.warning("ErrorHolder - Deprecated class - called method: __repr__")
        return "This class is now an empty shell, please use logger instead"

    def add_error(
        self,
        new_error_text: str,
        new_error_level: int = logging.INFO,
        new_error_kind: str = "",
        target_logger=logger,
    ):
        """Log error with optional level & kind
        :param new_error_text:
        :param new_error_level:
        :param new_error_kind:
        :param target_logger:
        """
        if new_error_text:
            error_level_to_logger(
                error_level=new_error_level,
                target_logger=target_logger,
            )(new_error_text)

    def clear(self):
        logger.warning("ErrorHolder - Deprecated class - called method: clear")

    def is_kind_present(self, kind: str):
        logger.warning("ErrorHolder - Deprecated class - called method: is_kind_present")
        return False

    def get_count_by_level(self, level: int) -> int:
        logger.warning(
            "ErrorHolder - Deprecated class - called method: get_count_by_level"
        )
        return 0

    def is_error_over_or(self, level):
        logger.warning("ErrorHolder - Deprecated class - called method: is_error_over_or")
        return False

    def is_error_under_or(self, level):
        logger.warning(
            "ErrorHolder - Deprecated class - called method: is_error_under_or"
        )
        return False

    @property
    def error_level(self) -> str:
        logger.warning("ErrorHolder - Deprecated class - called method: error_level")
        return -1

    @property
    def error_count(self):
        logger.warning("ErrorHolder - Deprecated class - called method: error_count")
        return 0

    @property
    def has_errors(self):
        logger.warning("ErrorHolder - Deprecated class - called method: has_errors")
        return False

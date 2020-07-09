from typing import Any, Union
from datetime import datetime as dt


ERR_LVL_UNK = -1
ERR_LVL_OK = 0
ERR_LVL_HINT = 1
ERR_LVL_WARNING = 2
ERR_LVL_EXCEPTION = 3
ERR_LVL_ERROR = 4
ERR_LVL_CRITICAL = 5

import logging

logger = logging.getLogger(__name__)


def error_level_to_str(error_level: int) -> str:
    if error_level == ERR_LVL_OK:
        return "OK"
    elif error_level == ERR_LVL_HINT:
        return "HINT"
    elif error_level == ERR_LVL_WARNING:
        return "WARNING"
    elif error_level == ERR_LVL_EXCEPTION:
        return "EXCEPTION"
    elif error_level == ERR_LVL_ERROR:
        return "ERROR"
    elif error_level == ERR_LVL_CRITICAL:
        return "CRITICAL"
    else:
        return "UNKNOWN"


def error_level_from_str(error_level: str) -> int:
    if error_level == "OK":
        return ERR_LVL_OK
    elif error_level == "HINT":
        return ERR_LVL_HINT
    elif error_level == "WARNING":
        return ERR_LVL_WARNING
    elif error_level == "EXCEPTION":
        return ERR_LVL_EXCEPTION
    elif error_level == "ERROR":
        return ERR_LVL_ERROR
    elif error_level == "CRITICAL":
        return ERR_LVL_CRITICAL
    else:
        return -1


def error_level_to_logger(error_level: int, target_logger):
    if error_level == ERR_LVL_OK:
        return target_logger.info
    elif error_level == ERR_LVL_HINT:
        return target_logger.info
    elif error_level == ERR_LVL_WARNING:
        return target_logger.warning
    elif error_level == ERR_LVL_EXCEPTION:
        return target_logger.exception
    elif error_level == ERR_LVL_ERROR:
        return target_logger.error
    elif error_level == ERR_LVL_CRITICAL:
        return target_logger.critical
    else:
        return target_logger.info


class SingleError(object):
    __slots__ = ["text", "timestamp", "level", "kind", "repeat_count"]

    def __init__(self, **kwargs):
        self.text = kwargs.get("text")
        self.timestamp = kwargs.get("time_stamp", dt.now())
        self.level = kwargs.get("level", -1)
        self.kind = kwargs.get("kind", "")
        self.repeat_count = kwargs.get("repeat_count", 0)
        error_level_to_logger(
            error_level=self.level, target_logger=kwargs.get("logger", logger)
        )(self.text)

    def __str__(self):
        level_str = error_level_to_str(self.level)
        if self.kind:
            kind_str = self.kind
        else:
            kind_str = "unk"
        if self.repeat_count > 0:
            repeat_str = f" (repeated {self.repeat_count} times)"
        else:
            repeat_str = ""
        return f'[{self.timestamp.strftime("%Y/%b/%d - %H:%M:%S")}] {level_str}-|-{kind_str}: {self.text}{repeat_str}'


class ErrorHolder(object):
    def __init__(self, owner: Any, errors: tuple = (), **kwargs):
        self.error_list = []
        self.owner = owner
        for err_dict in errors:
            self.add_error(
                new_error_text=err_dict.get("text", ""),
                new_error_level=err_dict.get("level", -1),
                new_error_kind=err_dict.get("kind", ""),
                target_logger=err_dict.get("logger", logger),
            )

    def __str__(self):
        if self.error_count == 0:
            return f"{str(self.owner)}: No error detected"
        else:
            return f"{str(self.owner)}:\n\t" + "\n\t".join(
                str(error_item) for error_item in self.error_list
            )

    def __repr__(self):
        return f"{repr(self.owner)} {repr(self.error_list)}"

    def to_html(self):
        owner_str = str(self.owner).replace("\n", "<br>")
        if self.error_count == 0:
            return f"{owner_str}: No error detected"
        else:
            return (
                f"{owner_str}:<ul>"
                + "".join(f"<li>{str(error_item)}</li>" for error_item in self.error_list)
                + "</ul>"
            )

    def list_errors(self):
        return [str(error_item) for error_item in self.error_list]

    def append(self, error_holder):
        if isinstance(error_holder, ErrorHolder) and error_holder.error_count > 0:
            for error in error_holder.error_list:
                self.error_list.append(
                    SingleError(
                        text=error.text,
                        timestamp=error.timestamp,
                        level=error.level,
                        kind=error.kind,
                        repeat_count=error.repeat_count,
                    )
                )
            self.error_list.sort(key=lambda x: x.timestamp)

    def add_error(
        self,
        new_error_text: str,
        new_error_level: Union[int, str] = -1,
        new_error_kind: str = "",
        target_logger=logger,
    ):
        """Add error with optional level & kind
        :param new_error_text:
        :param new_error_level:
        :param new_error_kind:
        :param target_logger:
        """
        if (self.error_count > 0) and (self.error_list[-1].text == new_error_text):
            self.error_list[-1].repeat_count += 1
        else:
            self.error_list.append(
                SingleError(
                    text=new_error_text,
                    level=new_error_level
                    if isinstance(new_error_level, int)
                    else error_level_from_str(new_error_level),
                    kind=new_error_kind,
                    logger=target_logger,
                )
            )

    def last_error(self, prefix_with_owner: bool = True, prepend_timestamp: bool = True):
        """Returns last error with prefix or not

        :param prefix_with_owner:
        :return:
        """
        if self.error_list:
            err_: SingleError = self.error_list[-1]
            if prepend_timestamp:
                error_str = str(err_)
            else:
                error_str = f"[{error_level_to_str(err_.level)}|{err_.kind}]-{err_.text}"
        else:
            error_str = ""
        if self.error_count > 1:
            error_str = f"{error_str}, ({self.error_count - 1} more)"
        if error_str and prefix_with_owner:
            return f"{str(self.owner)}: {error_str}"
        else:
            return error_str

    def clear(self):
        self.error_list = []

    def is_kind_present(self, kind: str):
        for error in self.error_list:
            if error.kind == kind:
                return True
        return False

    def get_count_by_level(self, level: int) -> int:
        ret = 0
        for error in self.error_list:
            if error.level == level:
                ret += 1
        return ret

    def is_error_over_or(self, level):
        if self.error_count == 0:
            return False
        else:
            for error in self.error_list:
                if error.level >= level:
                    return True
            else:
                return False

    def is_error_under_or(self, level):
        if self.error_count == 0:
            return True
        else:
            for error in self.error_list:
                if error.level > level:
                    return False
            else:
                return True

    @property
    def error_level(self) -> str:
        lvl = -1
        for error in self.error_list:
            if error.level > lvl:
                lvl = error.level
        return lvl

    @property
    def error_count(self):
        return len(self.error_list)

    @property
    def has_errors(self):
        return self.error_count > 0


# a_list = [i for i in range(10)]
# err_hld = ErrorHolder(a_list)
# print(err_hld.last_error())
# print(err_hld)
#
# err_hld.add_error('this is the first error')
# print(err_hld.last_error(False))
# print(err_hld)
#
# err_hld.add_error('this is the first error')
# print(err_hld.last_error(False))
# print(err_hld)
#
# err_hld.add_error('this is the second error')
# print(err_hld.last_error())
# print(err_hld)

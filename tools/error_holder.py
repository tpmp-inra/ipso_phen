from typing import Any
from datetime import datetime as dt


class SingleError(object):
    __slots__ = ['text', 'timestamp', 'level', 'kind', 'repeat_count']

    def __init__(self, text: str, level: str = '', kind: str = '', repeat_count: int = 0):
        self.text = text
        self.timestamp = dt.now()
        self.level = level
        self.kind = kind
        self.repeat_count = repeat_count

    def __str__(self):
        if self.level:
            level_str = f',{self.level} '
        else:
            level_str = 'unk'
        if self.kind:
            kind_str = f',{self.kind} '
        else:
            kind_str = 'unk'
        if self.repeat_count > 0:
            repeat_str = f' (repeated {self.repeat_count} times)'
        else:
            repeat_str = ''
        return f'[{self.timestamp.strftime("%Y/%b/%d - %H:%M:%S")}]{kind_str}-{level_str}: {self.text}{repeat_str}'


class ErrorHolder(object):

    def __init__(self, owner: Any, errors: tuple = (), **kwargs):
        self.error_list = []
        self.owner = owner
        for err_dict in errors:
            self.add_error(
                new_error_text=err_dict.get('text', ''),
                new_error_level=err_dict.get('level', ''),
                new_error_kind=err_dict.get('kind', '')
            )

    def __str__(self):
        if self.error_count == 0:
            return f'{str(self.owner)}: No error detected'
        else:
            return f"{str(self.owner)}:\n\t" + '\n\t'.join(str(error_item) for error_item in self.error_list)

    def __repr__(self):
        return f'{repr(self.owner)} {repr(self.error_list)}'

    def to_html(self):
        if self.error_count == 0:
            return f'{str(self.owner)}: No error detected'
        else:
            return f'{str(self.owner)}:<ul>' + ''.join(
                f'<li>{str(error_item)}</li>' for error_item in self.error_list
            ) + '</ul>'

    def list_errors(self):
        return [str(error_item) for error_item in self.error_list]

    def add_error(self, new_error_text: str, new_error_level: str = '', new_error_kind: str = ''):
        """Add error with optional level & kind
        :param new_error_text:
        :param new_error_level:
        :param new_error_kind:
        """
        if (self.error_count > 0) and (self.error_list[-1].text == new_error_text):
            self.error_list[-1].repeat_count += 1
        else:
            self.error_list.append(SingleError(new_error_text, new_error_level, new_error_kind))

    def last_error(self, prefix_with_owner: bool = True):
        """Returns last error with prefix or not

        :param prefix_with_owner:
        :return:
        """
        error_str = str(self.error_list[-1]) if self.error_list else ''
        if self.error_count > 1:
            error_str = f'{error_str}, ({self.error_count - 1} more)'
        if error_str and prefix_with_owner:
            return f'{str(self.owner)}: {error_str}'
        else:
            return error_str

    def clear(self):
        self.error_list = []

    def is_kind_present(self, kind: str):
        for error in self.error_list:
            if error.kind == kind:
                return True
        return False

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

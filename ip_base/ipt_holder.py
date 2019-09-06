import sys
import inspect
import pkgutil

from tools.common_functions import get_module_classes
from ip_base.ipt_abstract import IptBase
import ip_tools


class IptHolder(object):

    def __init__(self, **kwargs):
        self._ipt_list = []
        self._use_cases = []
        self._allow_pcv = kwargs.get('allow_pcv', False) is True

    def _init_holders(self):
        """Build list containing a single instance of all available tools
        """
        # Build unique class list
        ipt_classes_list = get_module_classes(
            package=ip_tools,
            class_inherits_from=IptBase,
            remove_abstract=True,
            exclude_if_contains=() if self._allow_pcv else ('pcv',)
        )

        # Create objects
        for cls in ipt_classes_list:
            try:
                op = cls()
                self._ipt_list.append(op)
                self._use_cases.extend(op.use_case)
            except Exception as e:
                print(f'Failed to add "{cls.__name__}" because "{repr(e)}"')
            else:
                pass
            finally:
                pass
            self._use_cases = sorted(list(set(self._use_cases)))
            self._ipt_list.sort(key=lambda x: (x.order, x.name))

    def list_by_use_case(self, use_case: str = ''):
        return [op for op in self.ipt_list if not use_case or (use_case in op.use_case)]

    @property
    def ipt_list(self):
        if not self._ipt_list:
            self._init_holders()
        return self._ipt_list

    @property
    def use_cases(self):
        if not self._use_cases:
            self._init_holders()
        return self._use_cases

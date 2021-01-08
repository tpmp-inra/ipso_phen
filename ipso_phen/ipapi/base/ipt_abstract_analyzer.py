from abc import ABC, abstractproperty

from ipso_phen.ipapi.base.ipt_abstract import IptBase


class IptBaseAnalyzer(IptBase, ABC):
    def __init__(self, wrapper=None, **kwargs):
        super().__init__(wrapper, **kwargs)
        self.data_dict = {}

    def add_value(self, key, value, force_add: bool = False):
        if force_add or (self.get_value_of(key=key) == 1):
            self.data_dict[key] = value

    @abstractproperty
    def name(self):
        return "Abstract image analyzer processing tool"

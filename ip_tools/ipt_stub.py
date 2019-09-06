from ip_base.ipt_abstract import IptBase
from ip_base.ip_common import TOOL_GROUP_DEMO_STR
from abc import ABC, abstractproperty


class IptStub(IptBase, ABC):

    def build_params(self):
        self.add_checkbox(
            name='enabled',
            desc='Activate tool',
            default_value=1,
            hint='Toggle whether or not tool is active'
        )

    def process_wrapper(self, **kwargs):
        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return False

        res = False
        try:
            img = wrapper.current_image
            if self.get_value_of('enabled') == 1:
                pass
            else:
                self.result = img
                wrapper.store_image(self.result, 'source')
            res = True

        except Exception as e:
            wrapper.error_holder.add_error(f'Failed : "{repr(e)}"')
            res = False
        else:
            pass
        finally:
            return res

    @abstractproperty
    def name(self):
        return 'Stub'

    @property
    def real_time(self):
        return True

    @property
    def result_name(self):
        return 'none'

    @property
    def output_kind(self):
        return 'none'

    @property
    def use_case(self):
        return []

    @property
    def description(self):
        return 'This is a stub script, it does nothing'

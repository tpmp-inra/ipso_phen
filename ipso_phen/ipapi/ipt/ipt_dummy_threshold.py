import logging
import os

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))
from ipso_phen.ipapi.base.ipt_abstract import IptBase


class IptDummyThreshold(IptBase):
    def build_params(self):
        self.add_enabled_checkbox()

    def process_wrapper(self, **kwargs):
        """
        Dummy threshold:

                Pass through threshold, expects binary mask as entry
        Real time: True

        Keyword Arguments (in parentheses, argument name):
            * Activate tool (enabled): Toggle whether or not tool is active
        """

        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return False

        res = False
        try:
            if self.get_value_of("enabled") == 1:
                img = wrapper.current_image
                if len(img.shape) == 2 or (len(img.shape) == 3 and img.shape[2] == 1):
                    self.result = img
                else:
                    self.result = wrapper.get_channel(src_img=img)

                res = True
                wrapper.store_image(img, "dummy_mask")
            else:
                wrapper.store_image(wrapper.current_image, "current_image")
                res = True
        except Exception as e:
            res = False
            logger.error(f'Failed to process {self. name}: "{repr(e)}"')
        else:
            pass
        finally:
            return res

    @property
    def name(self):
        return "Dummy threshold"

    @property
    def is_wip(self):
        return True

    @property
    def package(self):
        return "TPMP"

    @property
    def real_time(self):
        return True

    @property
    def result_name(self):
        return "mask"

    @property
    def output_kind(self):
        return "mask"

    @property
    def use_case(self):
        return ["Threshold"]

    @property
    def description(self):
        return """Dummy threshold.
        Pass through threshold, expects binary mask as entry"""

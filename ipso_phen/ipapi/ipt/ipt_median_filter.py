import cv2

from ipso_phen.ipapi.base.ipt_abstract import IptBase
from ipso_phen.ipapi.base.ip_common import ToolFamily, ensure_odd


import logging
import os

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))


class IptMedianFilter(IptBase):
    def build_params(self):
        self.add_enabled_checkbox()

        self.add_slider(
            name="median_filter_size",
            desc="Median filter size (odd values only)",
            default_value=3,
            minimum=3,
            maximum=101,
        )

    def process_wrapper(self, **kwargs):
        """
        Median Filter:
        'Apply median filter
        Real time: True

        Keyword Arguments (in parentheses, argument name):
            * Activate tool (enabled): Toggle whether or not tool is active
            * Median filter size (odd values only) (median_filter_size):
        """

        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return False

        res = False
        try:
            if self.get_value_of("enabled") == 1:
                median_filter_size = self.get_value_of("median_filter_size")

                self.result = cv2.medianBlur(
                    wrapper.current_image,
                    ensure_odd(median_filter_size),
                )

                wrapper.store_image(self.result, "current_image")
                res = True
            else:
                wrapper.store_image(wrapper.current_image, "current_image")
                res = True
        except Exception as e:
            res = False
            logger.error(f"Median Fileter FAILED, exception: {repr(e)}")
        else:
            pass
        finally:
            return res

    @property
    def name(self):
        return "Median Filter"

    @property
    def package(self):
        return "TPMP"

    @property
    def real_time(self):
        return True

    @property
    def result_name(self):
        return "image"

    @property
    def output_kind(self):
        return "image"

    @property
    def use_case(self):
        return [ToolFamily.EXPOSURE_FIXING, ToolFamily.PRE_PROCESSING]

    @property
    def description(self):
        return """'Apply median filter"""

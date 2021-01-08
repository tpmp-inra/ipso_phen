import cv2

import logging
import os

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))

from ipso_phen.ipapi.base.ipt_abstract import IptBase
from ipso_phen.ipapi.base.ip_common import (
    ToolFamily,
    C_FUCHSIA,
    C_ORANGE,
)


class IptSimpleWhiteBalance(IptBase):
    def build_params(self):
        self.add_enabled_checkbox()
        self.add_color_space(default_value="RGB")
        self.add_spin_box(
            name="median_filter_size",
            desc="Median filter size (odd values only)",
            default_value=0,
            minimum=0,
            maximum=51,
        )
        self.add_spin_box(
            name="min", desc="Threshold min %", default_value=2, minimum=0, maximum=100
        )
        self.add_spin_box(
            name="max", desc="Threshold max %", default_value=2, minimum=0, maximum=100
        )
        self.add_text_overlay(0)
        self.add_exposure_viewer_switch()

    def process_wrapper(self, **kwargs):
        """
        Simple white balance: Performs a simple white balance

        Real time : No

        Keyword Arguments (in parentheses, argument name):
            * Color space (color_space): Convert source to color space
            * Median filter size (median_filter_size): Apply median filter if >0
            * Threshold min % (min): Lower cut percentage
            * Threshold max % (max): Upper cut percentage
            * Overlay text on top of images (text_overlay): Draw description text on top of images
        """
        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return False

        res = False
        try:
            if self.get_value_of("enabled") == 1:
                min_ = self.get_value_of("min")
                max_ = self.get_value_of("max")
                color_space = self.get_value_of("color_space")

                res = self.wrapper.current_image

                if color_space == "HSV":
                    res = cv2.cvtColor(res, cv2.COLOR_BGR2HSV)
                elif color_space == "LAB":
                    res = cv2.cvtColor(res, cv2.COLOR_BGR2LAB)

                res = wrapper.simplest_cb(res, (min_, max_))

                if color_space == "HSV":
                    res = cv2.cvtColor(res, cv2.COLOR_HSV2BGR)
                elif color_space == "LAB":
                    res = cv2.cvtColor(res, cv2.COLOR_LAB2BGR)

                self.result = res

                if self.get_value_of("show_over_under") == 1:
                    mask_over = cv2.inRange(self.result, (255, 255, 255), (255, 255, 255))
                    mask_under = cv2.inRange(self.result, (0, 0, 0), (0, 0, 0))
                    self.result[mask_over > 0] = C_FUCHSIA
                    self.result[mask_under > 0] = C_ORANGE

                wrapper.store_image(
                    res,
                    f"simple_cb_{self.input_params_as_str()}",
                    text_overlay=self.get_value_of("text_overlay") == 1,
                )
            else:
                wrapper.store_image(wrapper.current_image, "current_image")
                res = True

        except Exception as e:
            res = False
            wrapper.error_holder.add_error(
                new_error_text=f'Failed to process {self. name}: "{repr(e)}"',
                new_error_level=35,
                target_logger=logger,
            )
        else:
            res = True
        finally:
            return res

    @property
    def name(self):
        return "Simple white balance"

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
        return [
            ToolFamily.PRE_PROCESSING,
            ToolFamily.WHITE_BALANCE,
            ToolFamily.EXPOSURE_FIXING,
        ]

    @property
    def description(self):
        return "Simple white balance: Performs a simple white balance.\nhttps://www.ipol.im/pub/art/2011/llmps-scb/article.pdf"

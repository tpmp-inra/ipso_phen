import os
import logging
import glob

import cv2

from ipso_phen.ipapi.base.ipt_abstract import IptBase
from ipso_phen.ipapi.tools.common_functions import make_safe_name
from ipso_phen.ipapi.base.ip_common import scale_image, TEST_IMG_IN_MSK_OUT

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))


class IptLoadMask(IptBase):
    def build_params(self):
        self.add_enabled_checkbox()
        self.add_file_naming()
        self.add_checkbox(
            name="invert_mask",
            desc="Invert mask",
            default_value=0,
        )
        self.add_combobox(
            name="scale_direction",
            desc="Scaling direction",
            values={
                "none": "No scaling",
                "up": "Up",
                "down": "Down",
            },
            default_value="none",
        )
        self.add_spin_box(
            name="scale_factor",
            desc="Scale factor",
            default_value=1,
            minimum=1,
            maximum=100,
        )

    def process_wrapper(self, **kwargs):
        """
        Load mask:
        'Load a mask from a file
        Real time: True

        Keyword Arguments (in parentheses, argument name):
            * Activate tool (enabled): Toggle whether or not tool is active
            * Path to masks folder (source_folder):
            * Prefix (prefix): Use text as prefix
            * Suffix (suffix): Use text as suffix
            * Mask file extension (extension):
            * Use fuzzy match (fuzzy_match):
            * Match name with safe name (safe_check):
            * Invert mask (invert_mask):
            * Scaling direction (scale_direction):
            * Scale factor (scale_factor):"""

        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return False

        res = False
        try:
            if self.get_value_of("enabled") == 1:

                # Get variables
                mask_path = self.build_path()
                scale_direction = self.get_value_of("scale_direction")
                scale_factor = self.get_value_of("scale_factor")

                if os.path.isfile(mask_path):
                    mask = cv2.imread(filename=mask_path)
                    mask[mask != 0] = 255
                    if scale_direction != "none" and scale_factor != 1:
                        mask = scale_image(
                            src_img=mask,
                            scale_factor=scale_factor
                            if self.get_value_of("scale_direction") == "up"
                            else 1 / scale_factor,
                        )
                    if len(mask.shape) == 3 and mask.shape[2] == 3:
                        h, s, mask = cv2.split(cv2.cvtColor(mask, cv2.COLOR_BGR2HSV))

                    if self.get_value_of("invert_mask"):
                        mask = 255 - mask

                    self.result = mask
                    res = True
                else:
                    logger.error(f"Missing mask: {mask_path}")
                    self.result = None
                    return

                img = wrapper.current_image

                # Write your code here
                wrapper.store_image(img, "current_image")
                res = True
            else:
                wrapper.store_image(wrapper.current_image, "current_image")
                res = True
        except Exception as e:
            res = False
            logger.error(f"Load mask FAILED, exception: {repr(e)}")
        else:
            pass
        finally:
            return res

    @property
    def skip_tests(self):
        return [TEST_IMG_IN_MSK_OUT]

    @property
    def name(self):
        return "Load mask"

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
        return """'Load a mask from a file"""

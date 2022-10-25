import cv2

import logging
import os

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))

from ipso_phen.ipapi.base.ipt_abstract import IptBase
from ipso_phen.ipapi.base.ip_common import ToolFamily


class IptPyramidMeanShift(IptBase):
    def build_params(self):
        self.add_slider(
            name="sp",
            desc="Spatial window radius",
            default_value=4,
            minimum=2,
            maximum=100,
        )
        self.add_slider(
            name="sr",
            desc="Color window radius",
            default_value=10,
            minimum=0,
            maximum=100,
        )

    def process_wrapper(self, **kwargs):
        """
        Pyramid mean shift: A kind of posterization

        Real time : No

        Keyword Arguments (in parentheses, argument name):
            * Spatial window radius (sp): -
            * Color window radius (sr): -
        """
        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return False

        sr = self.get_value_of("sp")
        sp = self.get_value_of("sr")

        res = False
        try:
            img = wrapper.current_image
            self.result = cv2.pyrMeanShiftFiltering(img, sp=sp, sr=sr)
            wrapper.store_image(
                self.result, f"shifted_{self.input_params_as_str()}", text_overlay=True
            )
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
        return "Pyramid mean shift"

    @property
    def real_time(self):
        return False

    @property
    def result_name(self):
        return "image"

    @property
    def output_kind(self):
        return "image"

    @property
    def use_case(self):
        return [ToolFamily.PRE_PROCESSING]

    @property
    def description(self):
        return "Pyramid mean shift: A kind of posterization"

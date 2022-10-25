import cv2
import numpy as np
import os

import logging

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))

from ipso_phen.ipapi.base.ipt_abstract import IptBase
from ipso_phen.ipapi.base.ip_common import ToolFamily


class IptCalculateChlorophyll(IptBase):
    def build_params(self):
        self.add_checkbox(name="normalize", desc="Normalize channel", default_value=0)
        self.add_color_map_selector(name="color_map", default_value="c_2")
        self.add_text_overlay(1)

    def process_wrapper(self, **kwargs):
        """
        Calculates an approximation of plant chlorophyll based on formula:

        Real time : No

        Keyword Arguments (in parentheses, argument name):
            * Normalize (normalize): if true displayed image will be normalized
            * Source (source): select image source among various options
            * Pseudo color map (color_map): Select color map to display chlorophyll levels
        """
        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return False

        color_map = self.get_value_of("color_map")
        text_overlay = self.get_value_of("text_overlay") == 1
        _, color_map = color_map.split("_")
        color_map = int(color_map)

        res = True
        try:
            src_img = wrapper.current_image
            if src_img is None:
                logger.error("Unable to fetch source target image")
                res = False

            mask = self.get_mask()

            b, g, r = cv2.split(src_img)
            self.result = np.exp(
                (-0.0280 * r * 1.04938271604938)
                + (0.0190 * g * 1.04938271604938)
                + (-0.0030 * b * 1.04115226337449)
                + 5.780
            )
            calc_img = (
                (self.result - self.result.min())
                / (self.result.max() - self.result.min())
                * 255
            ).astype(np.uint8)
            pseudo = wrapper.draw_image(
                src_image=src_img,
                channel=calc_img,
                mask=mask,
                background="source",
                foreground="false_colour",
                color_map=color_map,
            )
            wrapper.store_image(
                calc_img,
                f"Chloro_{self.input_params_as_str(exclude_defaults=True)}",
                text_overlay=text_overlay,
            )
            wrapper.store_image(
                pseudo,
                f"POnChloro_{self.input_params_as_str(exclude_defaults=True)}",
                text_overlay=text_overlay,
            )
            self.demo_image = pseudo
            self.result = calc_img
        except Exception as e:
            res = False
            logger.error(f'Failed to process {self. name}: "{repr(e)}"')
        else:
            res = True
        finally:
            return res

    @property
    def name(self):
        return "Calculate chlorophyll"

    @property
    def real_time(self):
        return False

    @property
    def result_name(self):
        return "raw_chlorophyll_image"

    @property
    def output_kind(self):
        return "image"

    @property
    def use_case(self):
        return [ToolFamily.VISUALIZATION]

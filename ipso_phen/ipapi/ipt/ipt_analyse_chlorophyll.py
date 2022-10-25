import os
import cv2
import numpy as np

import logging

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))

from ipso_phen.ipapi.base.ipt_abstract_analyzer import IptBaseAnalyzer
from ipso_phen.ipapi.base.ip_common import ToolFamily


class IptAnalyzeChlorophyll(IptBaseAnalyzer):
    def build_params(self):
        self.add_checkbox(
            name="chlorophyll_mean", desc="chlorophyll_mean", default_value=1
        )
        self.add_checkbox(
            name="chlorophyll_std_dev", desc="chlorophyll_std_dev", default_value=1
        )
        self.add_separator(name="sep_1")
        self.add_color_map_selector()
        self.add_combobox(
            name="background",
            desc="Debug image background",
            default_value="bw",
            values=dict(
                source="Source image",
                black="Black",
                white="White",
                silver="Silver",
                bw="Black and white",
            ),
        )

    def process_wrapper(self, **kwargs):
        """
        Analyze chlorophyll:
        Analyses chlorophyll data and returns mean and standard deviation
        Real time : False

        Keyword Arguments (in parentheses, argument name):
            * chlorophyll_mean (chlorophyll_mean):
            * chlorophyll_std_dev (chlorophyll_std_dev):
            * Select pseudo color map (color_map):
            * Debug image background (background):
        """
        wrapper = super().init_wrapper(**kwargs)
        if wrapper is None:
            return False

        res = False
        try:
            if not self.has_key_matching("chlorophyll"):
                return

            self.data_dict = {}

            img = wrapper.current_image
            mask = self.get_mask()
            if mask is None:
                logger.error(f"FAIL {self.name}: mask must be initialized")
                return

            b, g, r = cv2.split(cv2.bitwise_and(img, img, mask=mask))
            c = np.exp(
                (-0.0280 * r * 1.04938271604938)
                + (0.0190 * g * 1.04938271604938)
                + (-0.0030 * b * 1.04115226337449)
                + 5.780
            )
            calc_img = self.to_uint8(cv2.bitwise_and(c, c, mask=mask), normalize=True)
            self.demo_image = wrapper.draw_image(
                src_image=img,
                channel=calc_img,
                background=self.get_value_of("background"),
                foreground="false_colour",
                color_map=self.get_value_of("color_map"),
            )
            wrapper.store_image(calc_img, "chlorophyll_calculated")
            wrapper.store_image(self.demo_image, "pseudo_chlorophyll_on_img")
            tmp_tuple = cv2.meanStdDev(
                c.reshape(c.shape[1] * c.shape[0]),
                mask=mask.reshape(mask.shape[1] * mask.shape[0]),
            )
            self.add_value(key="chlorophyll_mean", value=tmp_tuple[0][0][0])
            self.add_value(key="chlorophyll_std_dev", value=tmp_tuple[1][0][0])
        except Exception as e:
            logger.error(f'Failed to process {self. name}: "{repr(e)}"')
            res = False
        else:
            res = True
        finally:
            self.result = len(self.data_dict) > 0
            return res

    @property
    def name(self):
        return "Analyze chlorophyll"

    @property
    def real_time(self):
        return False

    @property
    def result_name(self):
        return "dictionary"

    @property
    def output_kind(self):
        return "dictionnary"

    @property
    def use_case(self):
        return [ToolFamily.FEATURE_EXTRACTION]

    @property
    def description(self):
        return "Analyses chlorophyll data and returns mean and standard deviation "

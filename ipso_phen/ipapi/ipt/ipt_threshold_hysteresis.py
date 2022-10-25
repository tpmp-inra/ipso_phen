import cv2
import numpy as np
from skimage.filters import apply_hysteresis_threshold, sobel

import logging
import os

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))

from ipso_phen.ipapi.base.ipt_abstract import IptBase
from ipso_phen.ipapi.base.ip_common import ToolFamily


class IptHysteresis(IptBase):
    def build_params(self):
        self.add_checkbox(name="edge_only", desc="Edge detection only", default_value=0)
        self.add_slider(
            name="low_threshold",
            desc="Low threshold",
            default_value=10,
            minimum=0,
            maximum=100,
        )
        self.add_slider(
            name="high_threshold",
            desc="High threshold",
            default_value=35,
            minimum=0,
            maximum=100,
        )

    def process_wrapper(self, **kwargs):
        """
        Hysteresis threshold:
        From scikit-image: Apply hysteresis thresholding to image.
                    This algorithm finds regions where image is greater than high OR image is
                    greater than low and that region is connected to a region greater than high.
                    In other words, a pixel is accepted if its value is greater than the upper threshold,
                    or its value is higher than the lower threshold and one of has already been accepted.
        Real time: False

        Keyword Arguments (in parentheses, argument name):
            * Edge detection only (edge_only):
            * Low threshold (low_threshold):
            * High threshold (high_threshold):
        """

        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return False

        low_threshold = self.get_value_of("low_threshold") / 100
        high_threshold = self.get_value_of("high_threshold") / 100
        res = False
        try:
            edges = sobel(wrapper.current_image)
            self.result = self.to_uint8(
                img=apply_hysteresis_threshold(edges, low_threshold, high_threshold),
                normalize=True,
            )

            self.demo_image = wrapper.auto_mosaic(
                images=[
                    wrapper.current_image,
                    self.to_uint8(img=edges, normalize=True),
                    self.to_uint8(img=edges > low_threshold, normalize=True),
                    self.to_uint8(img=edges > high_threshold, normalize=True),
                    self.result,
                ]
            )

            wrapper.store_image(self.result, f"hysteresis_threshold")

        except Exception as e:
            res = False
            logger.error(f'Failed to process {self. name}: "{repr(e)}"')
        else:
            res = True
        finally:
            return res

    @property
    def name(self):
        return "Hysteresis threshold"

    @property
    def is_wip(self):
        return False

    @property
    def real_time(self):
        return self.get_value_of("edge_only") == 1

    @property
    def result_name(self):
        return "mask"

    @property
    def output_kind(self):
        return "mask"

    @property
    def use_case(self):
        return [ToolFamily.PRE_PROCESSING]

    @property
    def description(self):
        return """From scikit-image: Apply hysteresis thresholding to image.
            This algorithm finds regions where image is greater than high OR image is 
            greater than low and that region is connected to a region greater than high.
            In other words, a pixel is accepted if its value is greater than the upper threshold, 
            or its value is higher than the lower threshold and one of has already been accepted.  """

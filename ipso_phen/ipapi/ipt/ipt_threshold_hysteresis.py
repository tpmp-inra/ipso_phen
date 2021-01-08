import cv2
import numpy as np
from skimage.filters import apply_hysteresis_threshold

import logging
import os

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))

from ipso_phen.ipapi.base.ipt_abstract import IptBase
from ipso_phen.ipapi.ipt.ipt_edge_detector import IptEdgeDetector
from ipso_phen.ipapi.base.ip_common import ToolFamily


class IptHysteresis(IptBase):
    def build_params(self):
        self.add_checkbox(name="edge_only", desc="Edge detection only", default_value=0)
        self.add_edge_detector()
        self.add_separator(name="sep_1")
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
        self.add_color_map_selector(default_value="c_2")

    def process_wrapper(self, **kwargs):
        """
        Hysteresis threshold:
        From scikit-image: Apply hysteresis thresholding to image.
        This algorithm finds regions where image is greater than high OR image is
        greater than low and that region is connected to a region greater than high.
        In other words, a pixel is accepted if its value is greater than the upper threshold,
        or its value is higher than the lower threshold and one of has already been accepted.

        Real time : False

        Keyword Arguments (in parentheses, argument name):
            * Edge detection only (edge_only):
            * Select edge detection operator (operator):
            * Canny's sigma (canny_sigma): Sigma.
            * Canny's first Threshold (canny_first): First threshold for the hysteresis procedure.
            * Canny's second Threshold (canny_second): Second threshold for the hysteresis procedure.
            * Kernel size (kernel_size):
            * Threshold (threshold): Threshold for kernel based operators
            * Low threshold (low_threshold):
            * High threshold (high_threshold):
            * Select pseudo color map (color_map):
        """
        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return False

        low_threshold = self.get_value_of("low_threshold") / 100
        high_threshold = self.get_value_of("high_threshold") / 100
        color_map = self.get_value_of("color_map")
        _, color_map = color_map.split("_")
        color_map = int(color_map)
        res = False
        try:
            # Get the edge
            with IptEdgeDetector(wrapper=wrapper, **self.params_to_dict()) as (res, ed):
                if not res:
                    return
                edges = ed.result
                if self.get_value_of("edge_only") == 1:
                    self.result = ed.result
                    return True

            edges = self.to_fuzzy(edges)

            high_t = (edges > high_threshold).astype(int)
            hyst = apply_hysteresis_threshold(
                edges, low_threshold, high_threshold
            ).astype(np.uint8)
            hyst = hyst + high_t
            hyst = ((hyst - hyst.min()) / (hyst.max() - hyst.min()) * 255).astype(
                np.uint8
            )
            hyst = cv2.applyColorMap(hyst, color_map)

            self.result = hyst.astype(np.uint8)
            wrapper.store_image(
                self.result,
                f"hysteresis_{self.input_params_as_str()}",
                text_overlay=True,
            )

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
        return True

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
        return [ToolFamily.THRESHOLD]

    @property
    def description(self):
        return """From scikit-image: Apply hysteresis thresholding to image.
            This algorithm finds regions where image is greater than high OR image is 
            greater than low and that region is connected to a region greater than high.
            In other words, a pixel is accepted if its value is greater than the upper threshold, 
            or its value is higher than the lower threshold and one of has already been accepted.  """

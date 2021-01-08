import cv2
import numpy as np
from skimage.segmentation import quickshift
from skimage.util import img_as_float

import logging
import os

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))

from ipso_phen.ipapi.base.ip_common import DEFAULT_COLOR_MAP, ToolFamily
from ipso_phen.ipapi.base.ipt_abstract_merger import IptBaseMerger
from ipso_phen.ipapi.base.ip_common import ToolFamily


class IptQuickShift(IptBaseMerger):
    def build_params(self):
        self.add_color_space(default_value="HSV")
        self.add_slider(
            name="kernel_size",
            desc="Width of Gaussian kernel",
            default_value=3,
            minimum=1,
            maximum=51,
        )
        self.add_slider(
            name="max_dist",
            desc="Max distance",
            default_value=6,
            minimum=0,
            maximum=100,
            hint="Cut-off point for data distances.\nHigher means fewer clusters",
        )
        self.add_slider(
            name="ratio",
            desc="Ratio",
            default_value=50,
            minimum=0,
            maximum=100,
            hint="Balances color-space proximity and image-space proximity. \n"
            "Higher values give more weight to color-space.",
        )

    def process_wrapper(self, **kwargs):
        """
        From scikit-image: Quick shift segments image using quickshift clustering in Color-(x,y) space.

        Real time : No

        Keyword Arguments (in parentheses, argument name):
            * Color space (color_space): Selected color space, default: RGB
            * Width of Gaussian kernel (kernel_size): Width of Gaussian kernel used in smoothing the sample density. Higher means fewer clusters.
            * Max distance (max_dist): Cut-off point for data distances. Higher means fewer clusters
            * Ratio (ratio): Balances color-space proximity and image-space proximity. Higher values give more weight to color-space.
        """
        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return False

        color_space = self.get_value_of("color_space")
        kernel_size = self.get_value_of("kernel_size")
        max_dist = self.get_value_of("max_dist")
        ratio = self.get_value_of("ratio") / 100

        res = False
        try:
            img = self.wrapper.current_image

            if color_space.upper() == "HSV":
                img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            elif color_space.upper() == "LAB":
                img = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)

            if kernel_size == 1:
                kernel_size = 0
            elif kernel_size % 2 == 0:
                kernel_size += 1

            img = img_as_float(img)
            labels = quickshift(
                img, kernel_size=kernel_size, max_dist=max_dist, ratio=ratio
            )
            self.result = labels.copy()

            labels[labels == -1] = 0
            labels = (
                (labels - labels.min()) / (labels.max() - labels.min()) * 255
            ).astype(np.uint8)
            water_img = cv2.applyColorMap(255 - labels, DEFAULT_COLOR_MAP)

            _, lbl_on_src = self.print_segmentation_labels(
                water_img.copy(), labels, dbg_suffix="quick_shift"
            )

            wrapper.store_image(water_img, "quick_shift_vis", text_overlay=True)

            self.demo_image = lbl_on_src

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
        return "Quick shift"

    @property
    def real_time(self):
        return False

    @property
    def result_name(self):
        return "labels"

    @property
    def output_kind(self):
        return "labels"

    @property
    def use_case(self):
        return [ToolFamily.CLUSTERING, ToolFamily.VISUALIZATION]

    @property
    def description(self):
        return "From scikit-image: Quick shift segments image using quickshift clustering in Color-(x,y) space."

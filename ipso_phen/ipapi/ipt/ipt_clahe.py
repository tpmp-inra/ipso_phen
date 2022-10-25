import cv2

import logging
import os

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))

from ipso_phen.ipapi.base.ipt_abstract import IptBase
from ipso_phen.ipapi.base.ip_common import ToolFamily, ensure_odd


class IptClahe(IptBase):
    def build_params(self):
        self.add_color_space(default_value="HSV")
        self.add_slider(
            name="median_filter_size",
            desc="Median filter size (odd values only)",
            default_value=0,
            minimum=0,
            maximum=51,
        )
        self.add_slider(
            name="clip_limit",
            desc="Clip limit",
            default_value=2,
            minimum=2,
            maximum=100,
        )
        self.add_slider(
            name="tile_grid_size",
            desc="Tile grid size",
            default_value=8,
            minimum=2,
            maximum=100,
        )
        self.add_text_overlay()

    def process_wrapper(self, **kwargs):
        """
        Contrast Limited Adaptive Histogram Equalization (CLAHE)
        Equalizes image using multiple histograms

        Real time : Yes

        Keyword Arguments (in parentheses, argument name):
            * Color space (color_space): Selected color space, default: RGB
            * Median filter size (median_filter_size): if >0 a median filter will be applied before, odd values only
            * Clip limit (clip_limit): Local histogram clipping limit
            * Tile grid size (tile_grid_size): Image partition size
            * Overlay text on top of images (text_overlay): Draw description text on top of images
        """
        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return False

        clip_limit = self.get_value_of("clip_limit")
        tile_grid_size = self.get_value_of("tile_grid_size")
        color_space = self.get_value_of("color_space")
        median_filter_size = self.get_value_of("median_filter_size")
        text_overlay = self.get_value_of("text_overlay") == 1

        res = False
        try:

            median_filter_size = (
                0 if median_filter_size == 1 else ensure_odd(median_filter_size)
            )
            if median_filter_size > 0:
                src_img = cv2.medianBlur(wrapper.current_image, median_filter_size)
            else:
                src_img = wrapper.current_image

            self.result = wrapper.apply_CLAHE(
                src_img,
                color_space=color_space,
                clip_limit=(clip_limit, clip_limit, clip_limit),
                tile_grid_size=(tile_grid_size, tile_grid_size),
            )

            wrapper.store_image(
                self.result,
                f"CLAHE_{self.input_params_as_str()}",
                text_overlay=text_overlay,
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
        return "CLAHE"

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
        return [ToolFamily.PRE_PROCESSING, ToolFamily.WHITE_BALANCE]

    @property
    def description(self):
        return "Contrast Limited Adaptive Histogram Equalization (CLAHE).\nEqualizes image using multiple histograms"

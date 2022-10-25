import cv2
import numpy as np
from skimage.morphology import skeletonize, skeletonize_3d, medial_axis, thin

import logging
import os

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))

from ipso_phen.ipapi.base.ipt_abstract import IptBase
from ipso_phen.ipapi.base.ip_common import ToolFamily


class IptSkeletonize(IptBase):
    def build_params(self):
        self.add_combobox(
            name="mode",
            desc="Skeletonize mode",
            default_value="skeletonize",
            values=dict(
                skeletonize="Skeletonize",
                skeletonize_3d="Skeletonize 3D",
                medial_axis="Medial axis skeletonization",
                morphological_thinning="Morphological thinning",
            ),
            hint="Select skeletonize method among 4 available",
        )
        self.add_color_map_selector(
            default_value="k_10", desc="Color map for medial axis skeletonization"
        )
        self.add_checkbox(
            name="build_mosaic",
            desc="Build mosaic",
            default_value=0,
            hint="If true source and result will be displayed side by side",
        )
        self.add_text_overlay(1)

    def process_wrapper(self, **kwargs):
        """
        Skeletonize: Thins the input mask to one pixel width lines


        Real time : False

        Keyword Arguments (in parentheses, argument name):
            * Skeletonize mode (mode): Select skeletonize method among 4 available
            * Color map for medial axis skeletonization (color_map): -
            * Overlay text on top of images (text_overlay): Draw description text on top of images
        """
        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return False

        mode = self.get_value_of("mode")
        text_overlay = self.get_value_of("text_overlay") == 1
        build_mosaic = self.get_value_of("build_mosaic") == 1
        color_map = self.get_value_of("color_map")
        _, color_map = color_map.split("_")
        color_map = int(color_map)

        try:
            # Build mask
            mask = self.get_mask()
            if mask is None:
                logger.error(f"FAIL {self.name}: mask must be initialized")
                return

            res = True

            if mode == "skeletonize":
                mask[mask != 0] = 1
                skeleton = skeletonize(mask).astype(np.uint8)
                skeleton[skeleton != 0] = 255
            elif mode == "skeletonize_3d":
                skeleton = skeletonize_3d(mask)
            elif mode == "medial_axis":
                skel, distance = medial_axis(mask, return_distance=True)
                skeleton = skel * distance
                skeleton = (
                    (skeleton - skeleton.min()) / (skeleton.max() - skeleton.min()) * 255
                ).astype(np.uint8)
                skeleton = cv2.applyColorMap(skeleton, color_map)
            elif mode == "morphological_thinning":
                skeleton = thin(mask).astype(np.uint8)
                skeleton[skeleton != 0] = 255
            else:
                res = False
                skeleton = None

            if res:
                wrapper.store_image(
                    skeleton,
                    f"skeletonize_{self.input_params_as_str()}",
                    text_overlay=text_overlay,
                )
            else:
                logger.error(f"Unknown skeletonize mode {mode}")

            self.result = skeleton

            if build_mosaic:
                wrapper.store_image(self.to_uint8(mask), "source_mask")
                canvas = wrapper.build_mosaic(
                    image_names=np.array(
                        ["source_mask", f"skeletonize_{self.input_params_as_str()}"]
                    )
                )
                wrapper.store_image(canvas, "mosaic")
        except Exception as e:
            logger.error(f'Failed to process {self. name}: "{repr(e)}"')
            return False
        else:
            return res

    @property
    def name(self):
        return "Skeletonize"

    @property
    def real_time(self):
        return False

    @property
    def result_name(self):
        return "mask"

    @property
    def output_kind(self):
        return "channel"

    @property
    def use_case(self):
        return [ToolFamily.MASK_CLEANUP]

    @property
    def description(self):
        return "Skeletonize: Thins the input mask to one pixel width lines.\nInput needs to be a binary mask."

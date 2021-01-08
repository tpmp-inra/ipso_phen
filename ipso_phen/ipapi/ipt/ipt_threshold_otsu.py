import cv2
import numpy as np

import logging
import os

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))

from ipso_phen.ipapi.base.ipt_abstract import IptBase
from ipso_phen.ipapi.base.ip_common import ToolFamily, ensure_odd


class IptOtsu(IptBase):
    def build_params(self):
        self.add_source_selector(default_value="source")
        self.add_channel_selector(default_value="h")
        self.add_checkbox(
            name="invert_mask",
            desc="Invert mask",
            default_value=0,
            hint="Invert result",
        )
        self.add_checkbox(
            name="build_mosaic",
            desc="Build mosaic",
            default_value=0,
            hint="If true source and result will be displayed side by side",
        )
        self.add_slider(
            name="median_filter_size",
            desc="Median filter size (odd values only)",
            default_value=0,
            minimum=0,
            maximum=51,
        )
        self.add_morphology_operator()
        self.add_text_overlay()

    def process_wrapper(self, **kwargs):
        """
        Otsu binarization:

        Real time : No

        Keyword Arguments (in parentheses, argument name):
            * Channel (channel): Selected channel
            * Invert mask (invert_mask): Invert result
            * Median filter size (odd values only) (median_filter_size):  Size of median filter to be applied
            * Morphology operator (morphology_op):  Morphology operator to be applied afterwards
            * Morphology kernel size (kernel_size): -
            * Overlay text on top of images (text_overlay): Draw description text on top of images
        """
        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return False

        median_filter_size = self.get_value_of("median_filter_size")
        invert_mask = self.get_value_of("invert_mask") == 1
        channel = self.get_value_of("channel")
        text_overlay = self.get_value_of("text_overlay") == 1
        build_mosaic = self.get_value_of("build_mosaic") == 1

        res = False
        try:
            src_img = self.wrapper.current_image

            median_filter_size = (
                0 if median_filter_size == 1 else ensure_odd(median_filter_size)
            )

            c = wrapper.get_channel(
                src_img, channel, median_filter_size=median_filter_size
            )
            if c is None:
                self.do_channel_failure(channel)
                return
            # Crop if channel is msp
            if (c.shape != src_img.shape) and (
                self.get_value_of("source_file", "source") == "cropped_source"
            ):
                c = wrapper.crop_to_keep_roi(c)

            _, mask = cv2.threshold(c, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            if invert_mask:
                mask = 255 - mask

            self.result = self.apply_morphology_from_params(mask)
            wrapper.store_image(
                self.result,
                f"otsu_binarization_{self.input_params_as_str()}",
                text_overlay=text_overlay,
            )

            if build_mosaic:
                wrapper.store_image(c, "source_channel")
                canvas = wrapper.build_mosaic(
                    image_names=np.array(
                        [
                            "source_channel",
                            f"otsu_binarization_{self.input_params_as_str()}",
                        ]
                    )
                )
                wrapper.store_image(canvas, "mosaic")

            res = True

        except Exception as e:
            res = False
            logger.error(f'Failed to process {self. name}: "{repr(e)}"')
        else:
            pass
        finally:
            return res

    @property
    def name(self):
        return "Otsu"

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
        return [ToolFamily.THRESHOLD]

    @property
    def description(self):
        return "Thresholds image using Otsu binarization"

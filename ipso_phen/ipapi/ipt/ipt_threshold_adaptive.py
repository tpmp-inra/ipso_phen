import cv2
import numpy as np

import logging
import os

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))

from ipso_phen.ipapi.base.ipt_abstract import IptBase
from ipso_phen.ipapi.base.ip_common import ToolFamily, ensure_odd


class IptThresholdAdaptive(IptBase):
    def build_params(self):
        self.add_checkbox(
            name="enabled",
            desc="Activate tool",
            default_value=1,
            hint="Toggle whether or not tool is active",
        )
        self.add_source_selector(default_value="source")
        self.add_channel_selector(default_value="h")
        self.add_checkbox(
            name="invert_mask",
            desc="Invert mask",
            default_value=0,
            hint="Invert result",
        )
        self.add_slider(
            name="max_value",
            desc="Max value",
            default_value=255,
            minimum=1,
            maximum=255,
            hint="Non-zero value assigned to the pixels for which the condition is satisfied",
        )
        self.add_combobox(
            name="method",
            desc="Adaptive method",
            default_value="gauss",
            values=dict(mean="Mean", gauss="Gaussian"),
            hint="Adaptive thresholding algorithm to use, see cv::AdaptiveThresholdTypes",
        )
        self.add_slider(
            name="block_size",
            desc="Block size",
            default_value=3,
            minimum=1,
            maximum=101,
            hint="""Size of a pixel neighborhood that is used to calculate a threshold value
            for the pixel: 3, 5, 7, and so on.""",
        )
        self.add_slider(
            name="C",
            desc="C",
            default_value=2,
            minimum=-20,
            maximum=20,
            hint="""Constant subtracted from the mean or weighted mean (see the details below).
            Normally, it is positive but may be zero or negative as well.""",
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
        Adaptive threshold:


        Real time : True

        Keyword Arguments (in parentheses, argument name):
            * Activate tool (enabled): Toggle whether or not tool is active
            * Select source file type (source_file): no clue
            * Channel (channel):
            * Invert mask (invert_mask): Invert result
            * Max value (max_value): Non-zero value assigned to the pixels for which the condition
                is satisfied
            * Adaptive method (method): Adaptive thresholding algorithm to use,
                see cv::AdaptiveThresholdTypes
            * Block size (block_size): Size of a pixel neighborhood that is used to calculate a
                threshold value for the pixel: 3, 5, 7, and so on.
            * C (C): Constant subtracted from the mean or weighted mean (see the details below).
                Normally, it is positive but may be zero or negative as well.
            * Build mosaic (build_mosaic): If true source and result will be displayed side by side
            * Median filter size (odd values only) (median_filter_size):
            * Morphology operator (morph_op):
            * Kernel size (kernel_size):
            * Kernel shape (kernel_shape):
            * Iterations (proc_times):
            * Overlay text on top of images (text_overlay): Draw description text on top of images
        """

        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return False

        res = False
        try:
            src_img = self.wrapper.current_image
            wrapper.store_image(src_img, "source")
            if self.get_value_of("enabled") == 1:
                median_filter_size = self.get_value_of("median_filter_size")
                median_filter_size = (
                    0 if median_filter_size == 1 else ensure_odd(median_filter_size)
                )
                if self.get_value_of("invert_mask") == 1:
                    invert = cv2.THRESH_BINARY_INV
                else:
                    invert = cv2.THRESH_BINARY
                max_value = self.get_value_of("max_value")
                method = self.get_value_of("method")
                if method == "gauss":
                    method = cv2.ADAPTIVE_THRESH_GAUSSIAN_C
                elif method == "mean":
                    method = cv2.ADAPTIVE_THRESH_MEAN_C
                else:
                    logger.error(f"Unknown method {method}")
                    return False
                block_size = self.get_value_of("block_size")
                if block_size % 2 == 0:
                    block_size += 1
                c_value = self.get_value_of("C")
                channel = self.get_value_of("channel")
                text_overlay = self.get_value_of("text_overlay") == 1
                build_mosaic = self.get_value_of("build_mosaic") == 1

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

                mask = cv2.adaptiveThreshold(
                    src=c,
                    maxValue=max_value,
                    adaptiveMethod=method,
                    thresholdType=invert,
                    blockSize=block_size,
                    C=c_value,
                )

                self.result = self.apply_morphology_from_params(mask)
                wrapper.store_image(
                    self.result,
                    f"adaptive_threshold_{self.input_params_as_str()}",
                    text_overlay=text_overlay,
                )

                if build_mosaic:
                    wrapper.store_image(c, "source_channel")
                    canvas = wrapper.build_mosaic(
                        image_names=np.array(
                            [
                                "source_channel",
                                f"adaptive_threshold_{self.input_params_as_str()}",
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
        return "Adaptive threshold"

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
        return "Perform a adaptive threshold.\nMorphology operation can be performed afterwards"

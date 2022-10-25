import numpy as np
import os

import logging

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))

from ipso_phen.ipapi.base.ipt_abstract import IptBase
from ipso_phen.ipapi.base.ip_common import ToolFamily, ensure_odd


class IptChannelSubtraction(IptBase):
    def build_params(self):
        self.add_channel_selector("rd", name="channel_1", desc="Channel 1")
        self.add_slider(
            name="alpha",
            desc="Weight of the first channel",
            default_value=100,
            minimum=0,
            maximum=100,
        )
        self.add_channel_selector("bl", name="channel_2", desc="Channel 2")
        self.add_slider(
            name="beta",
            desc="Weight of the second channel",
            default_value=100,
            minimum=0,
            maximum=100,
        )
        self.add_combobox(
            name="post_processing",
            desc="On result image do",
            default_value="normalize",
            values=dict(
                normalize="Normalize values between 0-255",
                cut_negative="Cut negative values",
                cut_negative_and_normalize="Cut negative values and normalize",
                rescale="Move values so min becomes 0",
            ),
            hint="Action to perform after subtraction to return an image",
        )
        self.add_slider(
            name="min",
            desc="Threshold min value",
            default_value=0,
            minimum=0,
            maximum=255,
        )
        self.add_slider(
            name="max",
            desc="Threshold max value",
            default_value=255,
            minimum=0,
            maximum=255,
        )
        self.add_slider(
            name="median_filter_size",
            desc="Median filter size (odd values only)",
            default_value=0,
            minimum=0,
            maximum=51,
        )
        self.add_morphology_operator()

    def process_wrapper(self, **kwargs):
        """
        Performs channel subtraction while ensure 8bit range, each channel can have a weight.
        If threshold min or max are set a threshold operation will be performed.

        Real time : Yes

        Keyword Arguments (in parentheses, argument name):
            * Channel 1 (channel_1): First channel
            * Weight of the first channel (alpha): Weight of the first channel
            * Channel 2 (channel_2): Second channel
            * Weight of the second channel (beta): Weight of the second channel
            * Threshold min value (min): Lower threshold bound, if >0 threshold will be applied
            * Threshold max value (max): Upper threshold bound, if <255 threshold will be applied
            * Median filter size (median_filter_size): odd values only, if not 1 will be added
            * Morphology operator (morphology_op): Can be none
            * Morphology kernel size (kernel_size): Kernel is elliptical
        """
        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return False

        channel_1 = self.get_value_of("channel_1")
        alpha = self.get_value_of("alpha") / 100
        channel_2 = self.get_value_of("channel_2")
        beta = self.get_value_of("beta") / 100
        post_processing = self.get_value_of("post_processing")

        min_ = self.get_value_of("min")
        max_ = self.get_value_of("max")
        median_filter_size = self.get_value_of("median_filter_size")
        median_filter_size = (
            0 if median_filter_size == 1 else ensure_odd(median_filter_size)
        )

        res = False
        try:
            img = self.wrapper.current_image
            c1 = wrapper.get_channel(img, channel_1)
            c2 = wrapper.get_channel(img, channel_2)
            if c1 is None:
                self.do_channel_failure(channel_1)
                return
            if c2 is None:
                self.do_channel_failure(channel_2)
                return
            wrapper.store_image(c1, f"Channel 1: {channel_1}")
            wrapper.store_image(c2, f"Channel 1: {channel_2}")

            tmp = (c1 * alpha) - (c2 * beta)

            if post_processing == "normalize":
                tmp = ((tmp - tmp.min()) / (tmp.max() - tmp.min()) * 255).astype(np.uint8)
            elif post_processing == "cut_negative":
                tmp[tmp < 0] = 0
                tmp = tmp.astype(np.uint8)
            elif post_processing == "cut_negative_and_normalize":
                tmp[tmp < 0] = 0
                tmp = ((tmp - tmp.min()) / (tmp.max() - tmp.min()) * 255).astype(np.uint8)
            elif post_processing == "rescale":
                tmp = (tmp - tmp.min()).astype(np.uint8)
            else:
                logger.error(f"Unknown postprocessing {post_processing}")
                res = False
                return

            wrapper.store_image(
                tmp,
                f"Subtraction_{self.input_params_as_str(exclude_defaults=True)}",
                text_overlay=True,
            )

            if (min_ > 0) or (max_ < 255):
                mask, _ = wrapper.get_mask(
                    tmp, "", min_, max_, median_filter_size=median_filter_size
                )
                mask = self.apply_morphology_from_params(mask)
                wrapper.store_image(
                    mask,
                    f"sub_threshold_{self.input_params_as_str(exclude_defaults=True)}",
                    text_overlay=True,
                )
                self.result = mask.copy()
            else:
                self.result = tmp.copy()

        except Exception as e:
            res = False
            logger.error(f'Failed to process {self. name}: "{repr(e)}"')
        else:
            res = True
        finally:
            return res

    @property
    def name(self):
        return "Channel subtraction"

    @property
    def real_time(self):
        return True

    @property
    def result_name(self):
        return "result, threshold"

    @property
    def output_kind(self):
        return "image"

    @property
    def use_case(self):
        return [ToolFamily.PRE_PROCESSING]

    @property
    def description(self):
        return "Creates a new channel by subtracting one channel to another."

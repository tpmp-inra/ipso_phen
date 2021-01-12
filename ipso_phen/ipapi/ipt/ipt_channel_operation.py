import numpy as np
import cv2
import os

import logging

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))

from ipso_phen.ipapi.base.ipt_abstract import IptBase
from ipso_phen.ipapi.base.ip_common import ToolFamily


class IptChannelOperation(IptBase):
    def build_params(self):
        self.add_channel_selector(
            "bl", name="channel_1", desc="Channel 1", enable_none=True
        )
        self.add_slider(
            name="alpha",
            desc="Weight of the first channel",
            default_value=100,
            minimum=0,
            maximum=100,
        )
        self.add_arithmetic_operator(name="op1")
        self.add_channel_selector(
            "rd", name="channel_2", desc="Channel 2", enable_none=True
        )
        self.add_slider(
            name="beta",
            desc="Weight of the second channel",
            default_value=100,
            minimum=0,
            maximum=100,
        )
        self.add_arithmetic_operator(name="op2")
        self.add_channel_selector(
            "gr", name="channel_3", desc="Channel 3", enable_none=True
        )
        self.add_slider(
            name="gamma",
            desc="Weight of the third channel",
            default_value=100,
            minimum=0,
            maximum=100,
        )
        self.add_separator(name="sep_1")
        self.add_checkbox(
            name="cut_negative_values", desc="Set negative values to 0", default_value=0
        )
        self.add_color_map_selector(name="color_map", default_value="c_2")
        self.add_checkbox(
            name="use_palette",
            desc="use color palette",
            default_value=0,
            hint="Use color palette in postprocessing",
        )
        self.add_combobox(
            name="build_mosaic",
            desc="Build mosaic",
            default_value="no",
            values=dict(no="None", steps="Steps", sbs="Source and result side by side"),
            hint="Choose mosaic type to display",
        )
        self.add_text_overlay(0)

    def process_wrapper(self, **kwargs):
        """
        Channel operation:
        Performs arithmetic operation between up to 3 channels
        Real time : True

        Keyword Arguments (in parentheses, argument name):
            * Channel 1 (channel_1):
            * Weight of the first channel (alpha):
            * Arithmetic operator (op1): Operator to use with operands
            * Channel 2 (channel_2):
            * Weight of the second channel (beta):
            * Arithmetic operator (op2): Operator to use with operands
            * Channel 3 (channel_3):
            * Weight of the third channel (gamma):
            * Set negative values to 0 (cut_negative_values):
            * Select pseudo color map (color_map):
            * use color palette (use_palette): Use color palette in postprocessing
            * Build mosaic (build_mosaic): Choose mosaic type to display
            * Overlay text on top of images (text_overlay): Draw description text on top of images
        """

        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return False

        res = False
        try:
            channel_1 = self.get_value_of("channel_1")
            alpha = self.get_value_of("alpha") / 100
            channel_2 = self.get_value_of("channel_2")
            beta = self.get_value_of("beta") / 100
            channel_3 = self.get_value_of("channel_3")
            gamma = self.get_value_of("gamma") / 100

            op1 = self.get_value_of("op1")
            op2 = self.get_value_of("op2")

            post_processing = self.get_value_of("post_processing")
            text_overlay = self.get_value_of("text_overlay") == 1
            build_mosaic = self.get_value_of("build_mosaic")
            color_map = self.get_value_of("color_map")
            _, color_map = color_map.split("_")

            img = wrapper.current_image

            c1 = wrapper.get_channel(img, channel_1)
            c2 = wrapper.get_channel(img, channel_2)
            c3 = wrapper.get_channel(img, channel_3)

            if c1 is not None:
                c1 = c1 * alpha
            if c2 is not None:
                c2 = c2 * beta
            if c3 is not None:
                c3 = c3 * gamma

            c12 = None
            if c1 is not None:
                if c2 is not None:
                    if op1 == "plus":
                        c12 = np.add(c1, c2)
                    elif op1 == "minus":
                        c12 = np.subtract(c1, c2)
                    elif op1 == "mult":
                        c12 = np.multiply(c1, c2)
                    elif op1 == "div":
                        np.seterr(divide="ignore")
                        try:
                            c12 = np.divide(c1, c2)
                            c12[c12 == np.inf] = 0
                            c12[np.isnan(c12)] = 0
                        finally:
                            np.seterr(divide="warn")
                    elif op1 == "power":
                        c12 = np.power(c1, c2)
                    else:
                        logger.error(f"Unknown operator {op1}")
                else:
                    c12 = c1
            elif c2 is not None:
                c12 = c2

            if c12 is not None:
                if c3 is not None:
                    if op2 == "plus":
                        tmp = np.add(c12, c3)
                    elif op2 == "minus":
                        tmp = np.subtract(c12, c3)
                    elif op2 == "mult":
                        tmp = np.multiply(c12, c3)
                    elif op2 == "div":
                        np.seterr(divide="ignore")
                        try:
                            tmp = np.divide(c12, c3)
                        finally:
                            np.seterr(divide="warn")
                    elif op2 == "power":
                        tmp = np.power(c12, c3)
                    else:
                        tmp = None
                        logger.error(f"Unknown operator {op2}")
                else:
                    tmp = c12
            elif c3 is not None:
                tmp = c3
            else:
                tmp = None

            c1_str = f"Channel 1: {channel_1}"
            c2_str = f"Channel 3: {channel_2}"
            c3_str = f"Channel 3: {channel_3}"
            if c1 is not None:
                wrapper.store_image(self.to_uint8(img=c1, normalize=True), c1_str)
            if c2 is not None:
                wrapper.store_image(self.to_uint8(img=c2, normalize=True), c2_str)
            if c3 is not None:
                wrapper.store_image(self.to_uint8(img=c3, normalize=True), c3_str)
            if c12 is not None:
                wrapper.store_image(self.to_uint8(img=c12, normalize=True), "step_1")

            if tmp is not None:
                if self.get_value_of("cut_negative_values") == 1:
                    tmp[tmp < 0] = 0
                tmp = ((tmp - tmp.min()) / (tmp.max() - tmp.min()) * 255).astype(np.uint8)
                res = True
            else:
                res = False
                return

            if not res:
                return

            if self.get_value_of("use_palette") == 1:
                tmp = cv2.applyColorMap(tmp, int(color_map))

            self.result = tmp
            wrapper.store_image(tmp, "arithmetic_result")

            if build_mosaic == "steps":
                canvas = wrapper.build_mosaic(
                    shape=(tmp.shape[0] * 2, tmp.shape[1] * 3, 3),
                    image_names=np.array(
                        [
                            [c1_str, c2_str, c3_str],
                            ["source", "step_1", "arithmetic_result"],
                        ]
                    ),
                )
                main_result_name = "arithmetic_result_mosaic_steps"
            elif build_mosaic == "sbs":
                canvas = wrapper.build_mosaic(
                    image_names=np.array(["source", "arithmetic_result"])
                )
                main_result_name = "arithmetic_result_mosaic_side_by_side"
            else:
                canvas = tmp
                main_result_name = "arithmetic_result"

            if text_overlay:
                wrapper.store_image(
                    canvas,
                    main_result_name,
                    text_overlay=self.input_params_as_str(
                        exclude_defaults=False, excluded_params=("progress_callback",)
                    ).replace(", ", "\n"),
                )
            else:
                wrapper.store_image(canvas, main_result_name)
        except Exception as e:
            res = False
            self.result = None
            logger.error(f'Failed to process {self. name}: "{repr(e)}"')
        else:
            if not res:
                self.result = None
        finally:
            return res

    @property
    def name(self):
        return "Channel operation"

    @property
    def real_time(self):
        return True

    @property
    def result_name(self):
        return "channel"

    @property
    def output_kind(self):
        return "image"

    @property
    def use_case(self):
        return [ToolFamily.PRE_PROCESSING]

    @property
    def description(self):
        return "Performs arithmetic operation between up to 3 channels"

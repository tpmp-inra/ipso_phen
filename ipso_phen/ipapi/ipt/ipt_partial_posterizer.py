from ipso_phen.ipapi.base.ipt_abstract import IptBase
import cv2
import numpy as np

import logging
import os

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))
from ipso_phen.ipapi.base.ip_common import all_colors_dict
from ipso_phen.ipapi.base.ip_common import ToolFamily


class IptPartialPosterizer(IptBase):
    def build_params(self):
        self.add_checkbox(
            name="enabled",
            desc="Activate tool",
            default_value=1,
            hint="Toggle whether or not tool is active",
        )
        self.add_separator(name="sep_0")
        self.add_color_selector(
            name="blue_color",
            desc="Color to use to replace blue dominant pixels",
            default_value="none",
            enable_none=True,
            hint="Replace value of pixels where blue is dominant and represents more than % value by selected color",
        )
        self.add_spin_box(
            name="post_blue_value",
            desc="Blue channel threshold value",
            default_value=34,
            minimum=0,
            maximum=100,
            hint="Blue pixel value threshold (as percentage)",
        )
        self.add_color_selector(
            name="green_color",
            desc="Color to use to replace green dominant pixels",
            default_value="none",
            enable_none=True,
            hint="Replace value of pixels where green is dominant and represents more than % value by selected color",
        )
        self.add_spin_box(
            name="post_green_value",
            desc="Green channel threshold value",
            default_value=34,
            minimum=0,
            maximum=100,
            hint="Green pixel value threshold (as percentage)",
        )
        self.add_color_selector(
            name="red_color",
            desc="Color to use to replace red dominant pixels",
            default_value="none",
            enable_none=True,
            hint="Replace value of pixels where red is dominant and represents more than % value by selected color",
        )
        self.add_spin_box(
            name="post_red_value",
            desc="Red channel threshold value",
            default_value=34,
            minimum=0,
            maximum=100,
            hint="Red pixel value threshold (as percentage)",
        )
        self.add_separator(name="sep_1")
        self.add_combobox(
            name="build_mosaic",
            desc="Build mosaic",
            default_value="no",
            values=dict(
                no="None",
                channels="Channels dominance and result in bottom right",
                sbs="Source and result side by side",
            ),
            hint="Choose mosaic type to display",
        )
        self.add_text_overlay(0)

    def process_wrapper(self, **kwargs):
        """
        Partial posterizer:
        Replaces dominant colors by other colors
        Real time : True

        Keyword Arguments (in parentheses, argument name):
            * Activate tool (enabled): Toggle whether or not tool is active
            * Color to use to replace blue dominant pixels (blue_color): Replace value of pixels where blue is dominant and represents more than % value by selected color
            * Blue channel threshold value (post_blue_value): Blue pixel value threshold (as percentage)
            * Color to use to replace green dominant pixels (green_color): Replace value of pixels where green is dominant and represents more than % value by selected color
            * Green channel threshold value (post_green_value): Green pixel value threshold (as percentage)
            * Color to use to replace red dominant pixels (red_color): Replace value of pixels where red is dominant and represents more than % value by selected color
            * Red channel threshold value (post_red_value): Red pixel value threshold (as percentage)
            * Build mosaic (build_mosaic): Choose mosaic type to display
            * Overlay text on top of images (text_overlay): Draw description text on top of images
        """
        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return False

        res = False
        try:
            img = self.wrapper.current_image
            if self.get_value_of("enabled") == 1:
                blue_color = self.get_value_of(key="blue_color")
                blue_percent = self.get_value_of("post_blue_value") / 100
                green_color = self.get_value_of(key="green_color")
                green_percent = self.get_value_of("post_green_value") / 100
                red_color = self.get_value_of(key="red_color")
                red_percent = self.get_value_of("post_red_value") / 100

                text_overlay = self.get_value_of("text_overlay") == 1
                build_mosaic = self.get_value_of("build_mosaic")

                b, g, r = cv2.split(img)
                if blue_color != "none":
                    np.seterr(divide="ignore")
                    try:
                        where_more = cv2.bitwise_and(
                            (b > r).astype(np.uint8), (b > r).astype(np.uint8)
                        )
                        where_percent = np.divide(
                            b.astype(np.float),
                            b.astype(np.float) + g.astype(np.float) + r.astype(np.float),
                        )
                        where_percent[
                            (where_percent == np.inf) | np.isnan(where_percent)
                        ] = 0
                        wrapper.store_image(
                            self.to_uint8(where_percent, normalize=True), "bdm"
                        )
                        where_percent = (where_percent > blue_percent).astype(np.uint8)
                        blue_mask = cv2.bitwise_and(where_more, where_percent)
                    finally:
                        np.seterr(divide="warn")
                    img[blue_mask > 0] = all_colors_dict[blue_color]

                if green_color != "none":
                    np.seterr(divide="ignore")
                    try:
                        where_more = cv2.bitwise_and(
                            (g > r).astype(np.uint8), (g > b).astype(np.uint8)
                        )
                        where_percent = np.divide(
                            g.astype(np.float),
                            b.astype(np.float) + g.astype(np.float) + r.astype(np.float),
                        )
                        where_percent[
                            (where_percent == np.inf) | np.isnan(where_percent)
                        ] = 0
                        wrapper.store_image(
                            self.to_uint8(where_percent, normalize=True), "gdm"
                        )
                        where_percent = (where_percent > green_percent).astype(np.uint8)
                        green_mask = cv2.bitwise_and(where_more, where_percent)
                    finally:
                        np.seterr(divide="warn")
                    img[green_mask > 0] = all_colors_dict[green_color]

                if red_color != "none":
                    np.seterr(divide="ignore")
                    try:
                        where_more = cv2.bitwise_and(
                            (r > b).astype(np.uint8), (r > g).astype(np.uint8)
                        )
                        where_percent = np.divide(
                            b.astype(np.float),
                            r.astype(np.float) + g.astype(np.float) + r.astype(np.float),
                        )
                        where_percent[
                            (where_percent == np.inf) | np.isnan(where_percent)
                        ] = 0
                        wrapper.store_image(
                            self.to_uint8(where_percent, normalize=True), "rdm"
                        )
                        where_percent = (where_percent > red_percent).astype(np.uint8)
                        red_mask = cv2.bitwise_and(where_more, where_percent)
                    finally:
                        np.seterr(divide="warn")
                    img[red_mask > 0] = all_colors_dict[red_color]

                if text_overlay:
                    text_overlay = self.input_params_as_str(
                        exclude_defaults=False, excluded_params=("progress_callback",)
                    ).replace(", ", "\n")

                self.result = img
                wrapper.store_image(
                    self.result, "partial_poster", text_overlay=text_overlay
                )
                if build_mosaic == "channels":
                    wrapper.store_image(
                        self.result, "threshold_by_average", text_overlay=False
                    )
                    canvas = wrapper.build_mosaic(
                        shape=(img.shape[0], img.shape[1], 3),
                        image_names=np.array(
                            [["bdm", "gdm"], ["rdm", "threshold_by_average"]]
                        ),
                    )
                    wrapper.store_image(canvas, "mosaic", text_overlay=text_overlay)
                elif build_mosaic == "sbs":
                    canvas = wrapper.build_mosaic(
                        image_names=np.array(["source", "partial_poster"])
                    )
                    wrapper.store_image(canvas, "mosaic")
            else:
                self.result = img
                wrapper.store_image(self.result, "partial_poster")
            res = True

        except Exception as e:
            wrapper.error_holder.add_error(
                new_error_text=f'Failed to process {self. name}: "{repr(e)}"',
                new_error_level=35,
                target_logger=logger,
            )
            res = False
        else:
            pass
        finally:
            return res

    @property
    def name(self):
        return "Partial posterizer"

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
        return [ToolFamily.PRE_PROCESSING]

    @property
    def description(self):
        return "Replaces dominant colors by other colors"

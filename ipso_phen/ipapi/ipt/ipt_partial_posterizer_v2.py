import cv2
import numpy as np

import logging
import os

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))

from ipso_phen.ipapi.base.ipt_abstract import IptBase
import ipso_phen.ipapi.base.ip_common as ipc


class IptPartialPosterizerV2(IptBase):
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
            default_value=100,
            minimum=0,
            maximum=200,
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
            default_value=100,
            minimum=0,
            maximum=200,
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
            default_value=100,
            minimum=0,
            maximum=200,
            hint="Red pixel value threshold (as percentage)",
        )

    def process_wrapper(self, **kwargs):
        """
        Partial posterizer v2:
        Replaces dominant colors by other colors. Different algorithm from V1
        Real time: True

        Keyword Arguments (in parentheses, argument name):
            * Activate tool (enabled): Toggle whether or not tool is active
            * Color to use to replace blue dominant pixels (blue_color): Replace value of pixels where blue is dominant and represents more than % value by selected color
            * Blue channel threshold value (post_blue_value): Blue pixel value threshold (as percentage)
            * Color to use to replace green dominant pixels (green_color): Replace value of pixels where green is dominant and represents more than % value by selected color
            * Green channel threshold value (post_green_value): Green pixel value threshold (as percentage)
            * Color to use to replace red dominant pixels (red_color): Replace value of pixels where red is dominant and represents more than % value by selected color
            * Red channel threshold value (post_red_value): Red pixel value threshold (as percentage)
        """

        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return False

        res = False
        try:
            if self.get_value_of("enabled") == 1:
                img = wrapper.current_image

                blue_color = self.get_value_of(key="blue_color")
                blue_percent = self.get_value_of("post_blue_value") / 100
                green_color = self.get_value_of(key="green_color")
                green_percent = self.get_value_of("post_green_value") / 100
                red_color = self.get_value_of(key="red_color")
                red_percent = self.get_value_of("post_red_value") / 100

                b, g, r = cv2.split(img)
                b = (b.astype(np.float) * blue_percent).astype(np.uint8)
                g = (g.astype(np.float) * green_percent).astype(np.uint8)
                r = (r.astype(np.float) * red_percent).astype(np.uint8)
                if blue_color != "none":
                    img[(b > g) & (b > r)] = ipc.all_colors_dict[blue_color]
                if green_color != "none":
                    img[(g > b) & (g > r)] = ipc.all_colors_dict[green_color]
                if red_color != "none":
                    img[(r > g) & (r > b)] = ipc.all_colors_dict[red_color]

                self.result = img
                wrapper.store_image(self.result, self.name)
                res = True
            else:
                wrapper.store_image(wrapper.current_image, "current_image")
                res = True
        except Exception as e:
            res = False
            wrapper.error_holder.add_error(
                f"Partial posterizer v2 FAILED, exception: {repr(e)}",
                new_error_level=35,
                target_logger=logger,
            )
        else:
            pass
        finally:
            return res

    @property
    def name(self):
        return "Partial posterizer v2"

    @property
    def package(self):
        return "TPMP"

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
        return ["Pre processing"]

    @property
    def description(self):
        return "Replaces dominant colors by other colors. Different algorithm from V1"

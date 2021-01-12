import cv2
import numpy as np
import os

import logging

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))

from ipso_phen.ipapi.base.ipt_abstract import IptBase
from ipso_phen.ipapi.base.ip_common import ToolFamily


class IptChannelMixer(IptBase):
    def build_params(self):
        self.add_color_space(default_value="HSV")
        self.add_separator("sep_1")
        self.add_slider(
            name="channel_1_weight",
            desc="Weight of channel 1",
            default_value=100,
            minimum=0,
            maximum=100,
            hint="Factor used to multiply channel 1 values",
        )
        self.add_slider(
            name="channel_2_weight",
            desc="Weight of channel 2",
            default_value=100,
            minimum=0,
            maximum=100,
            hint="Factor used to multiply channel 2 values",
        )
        self.add_slider(
            name="channel_3_weight",
            desc="Weight of channel 3",
            default_value=100,
            minimum=0,
            maximum=100,
            hint="Factor used to multiply channel 3 values",
        )
        self.add_separator("sep_4")
        self.add_combobox(
            name="post_process",
            desc="Output mode:",
            default_value="rgb",
            values=dict(
                rgb="RGB image",
                grey_avg="Grey scale, average of values",
                grey_std="Gery scale, standard",
            ),
        )
        self.add_color_map_selector(
            default_value="c_2",
            desc="Grey scale palette:",
            hint="Grey scale palette (grey scale output only)",
        )
        self.add_checkbox(name="build_mosaic", desc="Build mosaic", default_value=0)

    def process_wrapper(self, **kwargs):
        """
        Channel mixer:


        Real time : True

        Keyword Arguments (in parentheses, argument name):
            * Select source file type (source_file): no clue
            * Color space (color_space): no clue
            * Weight of channel 1 (channel_1_weight): Factor used to multiply channel 1 values
            * Weight of channel 2 (channel_2_weight): Factor used to multiply channel 2 values
            * Weight of channel 3 (channel_3_weight): Factor used to multiply channel 3 values
            * Output mode: (post_process):
            * Grey scale palette: (color_map): Grey scale palette (grey scale output only)
            * Build mosaic (build_mosaic):
        """

        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return False

        res = False
        try:
            img = wrapper.current_image

            channels = []
            for i in range(0, 3):
                m = self.get_value_of(f"channel_{i+1}_weight") / 100
                c = img[:, :, i].astype(np.float)
                c *= m
                c = c.astype(np.uint8)
                channels.append(c)
                wrapper.store_image(c, f"c{i+1}")

            img = np.dstack(channels)
            color_space = self.get_value_of("color_space")
            if color_space == "HSV":
                img = cv2.cvtColor(img, cv2.COLOR_HSV2BGR)
            elif color_space == "LAB":
                img = cv2.cvtColor(img, cv2.COLOR_LAB2BGR)
            post_process = self.get_value_of("post_process")
            if post_process != "rgb":
                color_map = self.get_value_of("color_map")
                _, color_map = color_map.split("_")
                if post_process == "grey_std":
                    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                    img = cv2.applyColorMap(img, int(color_map))
                elif post_process == "grey_avg":
                    img = ((img[:, :, 0] + img[:, :, 1] + img[:, :, 2]) / 3).astype(
                        np.uint8
                    )
                    img = cv2.applyColorMap(img, int(color_map))

            wrapper.store_image(img, "channel_mixer")
            self.result = img

            res = True

            if self.get_value_of("build_mosaic") == 1:
                canvas = wrapper.build_mosaic(
                    shape=(img.shape[0], img.shape[1], 3),
                    image_names=np.array([["c1", "c2"], ["c3", "channel_mixer"]]),
                )
                wrapper.store_image(canvas, "mosaic")

        except Exception as e:
            logger.error(f'Failed to process {self. name}: "{repr(e)}"')
            res = False
        else:
            pass
        finally:
            return res

    @property
    def name(self):
        return "Channel mixer"

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
        return "Creates an new image by combining 3 channels from of the color spaces available."

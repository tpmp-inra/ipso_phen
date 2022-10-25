import cv2
import numpy as np

import logging
import os

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))

from scipy.special import expit

from ipso_phen.ipapi.base.ipt_abstract import IptBase
from ipso_phen.ipapi.base.ip_common import ToolFamily


class IptCustomChannel(IptBase):
    def build_params(self):
        self.add_checkbox(
            name="enabled",
            desc="Activate tool",
            default_value=1,
            hint="Toggle whether or not tool is active",
        )
        self.add_source_selector(default_value="source")
        self.add_separator("sep_1")
        self.add_channel_selector(
            name="channel_1",
            desc="Channel 1:",
            default_value="bl",
        )
        self.add_checkbox(
            name="invert_channel_1",
            desc="Invert channel 1",
            default_value=0,
        )
        self.add_combobox(
            name="transformation_channel_1",
            desc="Transformation applied to channel 1",
            default_value="none",
            values=dict(none="None", sigmoid="Sigmoid", normalize="Normalize"),
        )
        self.add_separator("sep_2")
        self.add_channel_selector(
            name="channel_2",
            desc="Channel 2:",
            default_value="gr",
        )
        self.add_checkbox(
            name="invert_channel_2",
            desc="Invert channel 2",
            default_value=0,
        )
        self.add_combobox(
            name="transformation_channel_2",
            desc="Transformation applied to channel 2",
            default_value="none",
            values=dict(none="None", sigmoid="Sigmoid", normalize="Normalize"),
        )
        self.add_separator("sep_3")
        self.add_channel_selector(
            name="channel_3",
            desc="Channel 3:",
            default_value="rd",
        )
        self.add_checkbox(
            name="invert_channel_3",
            desc="Invert channel 3",
            default_value=0,
        )
        self.add_combobox(
            name="transformation_channel_3",
            desc="Transformation applied to channel 3",
            default_value="none",
            values=dict(none="None", sigmoid="Sigmoid", normalize="Normalize"),
        )
        self.add_separator("sep_4")
        self.add_combobox(
            name="post_process",
            desc="Output mode:",
            default_value="rgb",
            values=dict(
                rgb="RGB image",
                hsv="HSV image",
                lab="LAB image",
                grey_avg="Grey scale, average of values",
                grey_std="Gery scale, standard",
            ),
        )
        self.add_color_map_selector(
            default_value="c_2",
            desc="Grey scale palette:",
            hint="Grey scale palette (grey scale output only)",
        )
        self.add_combobox(
            name="build_mosaic",
            desc="Build mosaic",
            default_value="no",
            values=dict(
                no="None",
                channels="Channels and result in bottom right",
                sbs="Source and result side by side",
            ),
            hint="Choose mosaic type to display",
        )
        self.add_text_overlay(0)

    def process_wrapper(self, **kwargs):
        """
        Custom channels:


        Real time : True

        Keyword Arguments (in parentheses, argument name):
            * Activate tool (enabled): Toggle whether or not tool is active
            * Select source file type (source_file): no clue
            * Channel 1: (channel_1):
            * Invert channel 1 (invert_channel_1):
            * Transformation applied to channel 1 (transformation_channel_1):
            * Channel 2: (channel_2):
            * Invert channel 2 (invert_channel_2):
            * Transformation applied to channel 2 (transformation_channel_2):
            * Channel 3: (channel_3):
            * Invert channel 3 (invert_channel_3):
            * Transformation applied to channel 3 (transformation_channel_3):
            * Output mode: (post_process):
            * Grey scale palette: (color_map): Grey scale palette (grey scale output only)
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
                channels = []
                channel_names = []
                for i in ["1", "2", "3"]:
                    channel = self.get_value_of(f"channel_{i}")
                    ct = self.get_value_of(f"transformation_channel_{i}")
                    if ct == "sigmoid":
                        c = wrapper.get_channel(src_img=img, channel=channel)
                        c = np.interp(c, (c.min(), c.max()), (-5, 5))
                        c = expit(c)
                        c = np.interp(c, (c.min(), c.max()), (0, 255)).astype(np.uint8)
                    elif ct == "normalize":
                        c = wrapper.get_channel(
                            src_img=img, channel=channel, normalize=True
                        )
                    else:
                        c = wrapper.get_channel(src_img=img, channel=channel)
                    if self.get_value_of(f"invert_channel_{i}") == 1:
                        c = 255 - c
                    channels.append(c)
                    channel_names.append(f"c{i}_{channel}")
                    wrapper.store_image(c, f"c{i}_{channel}")

                img = np.dstack(channels)
                post_process = self.get_value_of("post_process")
                color_map = self.get_value_of("color_map")
                _, color_map = color_map.split("_")
                if post_process == "rgb":
                    pass
                elif post_process == "hsv":
                    img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
                elif post_process == "lab":
                    img = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
                elif post_process == "grey_std":
                    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                    img = cv2.applyColorMap(img, int(color_map))
                elif post_process == "grey_avg":
                    img = ((img[:, :, 0] + img[:, :, 1] + img[:, :, 2]) / 3).astype(
                        np.uint8
                    )
                    img = cv2.applyColorMap(img, int(color_map))

                if self.get_value_of("text_overlay") == 1:
                    text_overlay = self.input_params_as_str(
                        exclude_defaults=True, excluded_params=("progress_callback",)
                    ).replace(", ", "\n")
                else:
                    text_overlay = False
                self.result = self.to_uint8(img, normalize=False)

                wrapper.store_image(
                    self.result, "threshold_by_average", text_overlay=text_overlay
                )
                build_mosaic = self.get_value_of("build_mosaic")
                if (build_mosaic == "channels") and self.result is not None:
                    wrapper.store_image(
                        self.result, "threshold_by_average", text_overlay=False
                    )
                    canvas = wrapper.build_mosaic(
                        shape=(img.shape[0], img.shape[1], 3),
                        image_names=np.array(
                            [
                                [channel_names[0], channel_names[1]],
                                [channel_names[2], "threshold_by_average"],
                            ]
                        ),
                    )
                    wrapper.store_image(canvas, "mosaic", text_overlay=text_overlay)
                elif build_mosaic == "sbs":
                    canvas = wrapper.build_mosaic(
                        image_names=np.array(["source", "threshold_by_average"])
                    )
                    wrapper.store_image(canvas, "mosaic")

                res = True
            else:
                wrapper.store_image(image=img, text="source")
                res = True

        except Exception as e:
            logger.error(f'Failed to process {self. name}: "{repr(e)}"')
            res = False
        else:
            pass
        finally:
            return res

    @property
    def name(self):
        return "Custom channels"

    @property
    def real_time(self):
        return True

    @property
    def result_name(self):
        return "image"

    @property
    def output_kind(self):
        return "mask"

    @property
    def use_case(self):
        return [ToolFamily.PRE_PROCESSING]

    @property
    def description(self):
        return "Builds a mask or a channel by comparing pixels to the average value."

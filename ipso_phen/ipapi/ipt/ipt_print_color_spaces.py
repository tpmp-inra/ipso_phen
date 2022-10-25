import numpy as np
import cv2

import logging
import os

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))

from ipso_phen.ipapi.base import ip_common as ipc
from ipso_phen.ipapi.base.ipt_abstract import IptBase


class IptPrintColorSpaces(IptBase):
    def build_params(self):
        self.add_enabled_checkbox()
        self.add_separator(name="sp_0")
        self.add_checkbox(
            name="rgb",
            desc="RGB",
            default_value=1,
        )
        self.add_checkbox(
            name="lab",
            desc="LAB",
            default_value=1,
        )
        self.add_checkbox(
            name="hsv",
            desc="HSV",
            default_value=1,
        )
        self.add_checkbox(
            name="msp",
            desc="MSP",
            default_value=1,
            hint="Only for multispectral images",
        )
        self.add_checkbox(
            name="normalize",
            desc="Normalize channels",
            default_value=0,
        )
        self.add_checkbox(
            name="tag_images",
            desc="Add text to images",
            default_value=0,
        )
        self.add_separator(name="sp_1")
        self.add_checkbox(
            name="single",
            desc="Output data as single images",
            default_value=0,
        )
        self.add_checkbox(
            name="mosaics",
            desc="Output data as mosaics",
            default_value=1,
        )

    def store_image(self, wrapper, channel, idx, text):
        text = text if self.get_value_of("tag_images") else False
        if self.get_value_of("normalize") == 1:
            channel = cv2.equalizeHist(channel)
        wrapper.store_image(
            image=channel,
            text=idx,
            text_overlay=text,
            force_store=True,
            font_color=ipc.C_CYAN,
        )

    def process_wrapper(self, **kwargs):
        """
        Print color spaces:
        Print color spaces as individual channels or mosaics.
        Real time: False

        Keyword Arguments (in parentheses, argument name):
            * Activate tool (enabled): Toggle whether or not tool is active
            * RGB (rgb):
            * LAB (lab):
            * HSV (hsv):
            * MSP (msp): Only for multispectral images
            * Normalize channels (normalize):
            * Add text to images (tag_images):
            * Output data as single images (single):
            * Output data as mosaics (mosaics):
        """
        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return False

        res = False
        try:
            if self.get_value_of("enabled") == 1:
                img = wrapper.current_image

                rgb_channels = []
                lab_channels = []
                hsv_channels = []
                msp_channels = []

                if self.get_value_of("rgb") == 1:
                    b, g, r = cv2.split(img)
                    for c, t in zip((b, g, r), ("blue", "green", "red")):
                        self.store_image(
                            wrapper=wrapper, channel=c, idx=f"RGB_{t}", text=f"RGB {t}"
                        )
                        rgb_channels.append(f"RGB_{t}")

                if self.get_value_of("lab") == 1:
                    l, a, b = cv2.split(cv2.cvtColor(img, cv2.COLOR_BGR2LAB))
                    for c, t in zip((l, a, b), ("luminance", "red green", "yellow blue")):
                        self.store_image(
                            wrapper=wrapper, channel=c, idx=f"LAB_{t}", text=f"LAB {t}"
                        )
                        lab_channels.append(f"LAB_{t}")

                if self.get_value_of("hsv") == 1:
                    h, s, v = cv2.split(cv2.cvtColor(img, cv2.COLOR_BGR2HSV))
                    for c, t in zip((h, s, v), ("hue", "saturation", "value")):
                        self.store_image(
                            wrapper=wrapper, channel=c, idx=f"HSV_{t}", text=f"HSV {t}"
                        )
                        hsv_channels.append(f"HSV_{t}")

                if self.get_value_of("msp") == 1 and wrapper.is_msp:
                    for c, channel_name in ipc.CHANNELS_BY_SPACE["msp"].items():
                        self.store_image(
                            wrapper=wrapper,
                            channel=wrapper.get_channel(channel=c),
                            idx=f"MSP {c}",
                            text=f"MSP {channel_name}",
                        )
                        msp_channels.append(f"MSP {c}")

                if self.get_value_of("mosaics") == 1:
                    if wrapper.is_msp:
                        while len(msp_channels) < 8:
                            msp_channels.append("")
                        mosaic_data = np.array(
                            [
                                msp_channels[0:3],
                                [msp_channels[3], "current_image", msp_channels[4]],
                                msp_channels[5:8],
                            ]
                        )
                        wrapper.store_image(
                            image=wrapper.build_mosaic(image_names=mosaic_data),
                            text="msp_mosaic",
                            force_store=True,
                        )
                    mosaic_data = None
                    for cs in [rgb_channels, hsv_channels, lab_channels]:
                        if not cs:
                            continue
                        if mosaic_data is None:
                            mosaic_data = np.array(cs)
                        else:
                            mosaic_data = np.vstack((mosaic_data, cs))
                    if mosaic_data is not None:
                        wrapper.store_image(
                            image=wrapper.build_mosaic(image_names=mosaic_data),
                            text="vis_mosaic",
                            force_store=True,
                        )

                # Write your code here
                res = True
            else:
                wrapper.store_image(wrapper.current_image, "current_image")
                res = True
        except Exception as e:
            res = False
            wrapper.error_holder.add_error(
                new_error_text=f'Failed to process {self. name}: "{repr(e)}"',
                new_error_level=35,
                target_logger=logger,
            )
        else:
            pass
        finally:
            return res

    @property
    def name(self):
        return "Print color spaces"

    @property
    def package(self):
        return "Me"

    @property
    def real_time(self):
        return False

    @property
    def result_name(self):
        return "image"

    @property
    def output_kind(self):
        return "image"

    @property
    def use_case(self):
        return ["Visualization"]

    @property
    def description(self):
        return """Print color spaces as individual channels or mosaics."""

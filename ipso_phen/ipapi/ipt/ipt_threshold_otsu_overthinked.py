import cv2
import numpy as np

import logging
import os

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))

from ipso_phen.ipapi.base.ip_common import (
    create_channel_generator,
    get_hr_channel_name,
    CHANNELS_FLAT,
)
from ipso_phen.ipapi.base.ipt_abstract import IptBase
from ipso_phen.ipapi.base.ip_common import ToolFamily


class IptOtsuOverthinked(IptBase):
    def build_params(self):
        self.add_combobox(
            name="merge_method",
            desc="Merge method:",
            default_value="l_and",
            values=dict(l_and="Logical AND", l_or="Logical OR"),
            hint="Selected merge method",
        )
        self.add_label(name="lbl_channel", desc="Channels:")
        choices_dict = dict(disabled="disabled", active="active", inverted="inverted")
        for color_space, channel, channel_name in create_channel_generator(
            ("h", "s", "l", "a", "b", "rd", "gr", "bl")
        ):
            self.add_combobox(
                name=f"{channel}",
                desc=f"Channel {channel_name} behavior:",
                default_value="active",
                values=choices_dict,
                hint=f"Select channel {get_hr_channel_name(channel)} behavior",
            )
        self.add_checkbox(name="normalize", desc="Normalize channel", default_value=0)
        self.add_separator(name="sep1")
        self.add_morphology_operator()
        self.add_separator(name="sep2")
        self.add_combobox(
            name="build_mosaic",
            desc="Build mosaic",
            default_value="no",
            values=dict(
                no="None",
                channels="Channels and result in the middle",
                sbs="Source and result side by side",
            ),
            hint="Choose mosaic type to display",
        )

    def process_wrapper(self, **kwargs):
        """
        Otsu overthinked:
        Based on Otsu's binarization, uses a costum set of channels.
        Real time: True

        Keyword Arguments (in parentheses, argument name):
            * Merge method: (merge_method): Selected merge method
            * Channel hue behavior: (h): Select channel hsv: hue behavior
            * Channel saturation behavior: (s): Select channel hsv: saturation behavior
            * Channel lightness behavior: (l): Select channel lab: lightness behavior
            * Channel a_green-red behavior: (a): Select channel lab: a_green-red behavior
            * Channel b_blue-yellow behavior: (b): Select channel lab: b_blue-yellow behavior
            * Channel red behavior: (rd): Select channel rgb: red behavior
            * Channel green behavior: (gr): Select channel rgb: green behavior
            * Channel blue behavior: (bl): Select channel rgb: blue behavior
            * Normalize channel (normalize):
            * Morphology operator (morph_op):
            * Kernel size (kernel_size):
            * Kernel shape (kernel_shape):
            * Iterations (proc_times):
            * Build mosaic (build_mosaic): Choose mosaic type to display
        """
        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return False

        res = False
        try:
            normalize = self.get_value_of("normalize") == 1
            build_mosaic = self.get_value_of("build_mosaic")
            merge_method = self.get_value_of("merge_method")
            masks = []
            power_ = 0

            wrapper.store_image(wrapper.current_image, "current_image")

            mask = None
            for p in self.gizmos:
                if (p.name not in CHANNELS_FLAT) or (p.value == "disabled"):
                    continue
                _, mask = cv2.threshold(
                    wrapper.get_channel(channel=p.name, normalize=normalize),
                    0,
                    255,
                    cv2.THRESH_BINARY + cv2.THRESH_OTSU,
                )
                if p.value == "inverted":
                    mask = 255 - mask
                wrapper.store_image(mask, f"Otsu_{get_hr_channel_name(p.name)}")
                power_ += 1
                masks.append(mask)

            if masks:
                if merge_method == "l_and":
                    mask = wrapper.multi_and(masks)
                elif merge_method == "l_or":
                    mask = wrapper.multi_or(masks)
                else:
                    logger.error("Unknown merge method")
                    return

                self.result = self.apply_morphology_from_params(mask)
                wrapper.store_image(self.result, "otsu_overthinked")
            else:
                img = wrapper.current_image
                self.result = None

            if (build_mosaic == "channels") and mask is not None:
                canvas = wrapper.build_mosaic(
                    shape=(mask.shape[0] * 3, mask.shape[1] * 3, 3),
                    image_names=np.array(
                        [
                            [f"OTSU_{get_hr_channel_name(c)}" for c in ["h", "s", "l"]],
                            [
                                f'OTSU_{get_hr_channel_name("a")}',
                                "otsu_overthinked",
                                f'OTSU_{get_hr_channel_name("b")}',
                            ],
                            [
                                f"OTSU_{get_hr_channel_name(c)}"
                                for c in ["rd", "gr", "bl"]
                            ],
                        ]
                    ),
                )
                wrapper.store_image(canvas, "mosaic")
            elif build_mosaic == "sbs":
                canvas = wrapper.build_mosaic(
                    image_names=np.array(
                        [
                            "source",
                            "otsu_overthinked",
                        ]
                    )
                )
                wrapper.store_image(canvas, "mosaic")

            res = True

        except Exception as e:
            logger.error(f'Failed to process {self. name}: "{repr(e)}"')
            res = False
        else:
            pass
        finally:
            return res

    def apply_test_values_overrides(self, use_cases: tuple = ()):
        if ToolFamily.THRESHOLD in use_cases:
            self.set_value_of("merge_method", "l_or")

    @property
    def name(self):
        return "Otsu overthinked"

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
        return "Based on Otsu's binarization, uses a costum set of channels."

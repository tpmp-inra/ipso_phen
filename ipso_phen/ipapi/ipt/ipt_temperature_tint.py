import numpy as np
import cv2

import logging
import os

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))

from ipso_phen.ipapi.base.ipt_abstract import IptBase
from ipso_phen.ipapi.base.ip_common import (
    ToolFamily,
    C_FUCHSIA,
    C_ORANGE,
)


class IptTemperatureTint(IptBase):
    def build_params(self):
        self.add_checkbox(
            name="enabled",
            desc="Activate tool",
            default_value=1,
            hint="Toggle whether or not tool is active",
        )
        self.add_combobox(
            name="clip_method",
            desc="Clip method",
            default_value="clip",
            values=dict(
                clip="Set to 0 if lower 255 if upper",
                rescale="Allow overflow and the rescale",
            ),
        )
        self.add_spin_box(
            name="temperature_adjustment",
            desc="Temperature adjustment",
            default_value=0,
            minimum=-100,
            maximum=100,
            hint="Adjust image temperature",
        )
        self.add_spin_box(
            name="tint_adjustment",
            desc="Tint adjustment",
            default_value=0,
            minimum=-100,
            maximum=100,
            hint="Adjust image tint",
        )
        self.add_exposure_viewer_switch()

    def process_wrapper(self, **kwargs):
        """
        Temperature and tint:
        Simple method to alter an image temperature and tint
        http://www.tannerhelland.com/5675/simple-algorithms-adjusting-image-temperature-tint/
        Real time: True

        Keyword Arguments (in parentheses, argument name):
            * Activate tool (enabled): Toggle whether or not tool is active
            * Clip method (clip_method):
            * Temperature adjustment (temperature_adjustment): Adjust image temperature
            * Tint adjustment (tint_adjustment): Adjust image tint
            * Build mosaic (build_mosaic):
        """
        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return False

        res = False
        try:
            img = wrapper.current_image
            if self.get_value_of("enabled") == 1:
                b, g, r = cv2.split(img)

                temperature_adjustment = self.get_value_of("temperature_adjustment")
                tint_adjustment = self.get_value_of("tint_adjustment")

                b = b.astype(np.float) - temperature_adjustment
                g = g.astype(np.float) + tint_adjustment
                r = r.astype(np.float) + temperature_adjustment

                clip_method = self.get_value_of("clip_method")

                if clip_method == "clip":
                    b[b < 0] = 0
                    g[g < 0] = 0
                    r[r < 0] = 0
                    b[b > 255] = 255
                    g[g > 255] = 255
                    r[r > 255] = 255
                    self.result = cv2.merge(
                        [b.astype(np.uint8), g.astype(np.uint8), r.astype(np.uint8)]
                    )
                elif clip_method == "rescale":
                    self.result = self.to_uint8(cv2.merge([b, g, r]))
                else:
                    logger.error(f'Failed : unknown clip_method "{clip_method}"')
                    return

                if self.get_value_of("show_over_under") == 1:
                    mask_over = cv2.inRange(self.result, (255, 255, 255), (255, 255, 255))
                    mask_under = cv2.inRange(self.result, (0, 0, 0), (0, 0, 0))
                    self.result[mask_over > 0] = C_FUCHSIA
                    self.result[mask_under > 0] = C_ORANGE

                wrapper.store_image(self.result, "temp_tint")

                res = True
            else:
                self.result = img
                wrapper.store_image(self.result, "source")
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
        return "Temperature and tint"

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
        return [ToolFamily.EXPOSURE_FIXING, ToolFamily.PRE_PROCESSING]

    @property
    def description(self):
        return "Simple method to alter an image temperature and tint\nhttp://www.tannerhelland.com/5675/simple-algorithms-adjusting-image-temperature-tint/"

from ipso_phen.ipapi.base.ipt_abstract import IptBase


import os
import logging

import numpy as np
import cv2

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))


class IptAutowbgwa(IptBase):
    def build_params(self):
        self.add_enabled_checkbox()
        self.add_spin_box(
            name="shift_gr",
            desc="Green/Red shift",
            default_value=0,
            minimum=-128,
            maximum=128,
            hint="Red/blue shift",
        )
        self.add_spin_box(
            name="shift_yb",
            desc="Yellow/Blue shift",
            default_value=0,
            minimum=-128,
            maximum=128,
            hint="Red/blue shift",
        )

    def process_wrapper(self, **kwargs):
        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return False

        res = False
        try:
            if self.get_value_of("enabled") == 1:
                img = wrapper.current_image
                shift_gr = self.get_value_of("shift_gr", 0)
                shift_yb = self.get_value_of("shift_yb", 0)
                result = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
                avg_a = np.average(result[:, :, 1])
                avg_b = np.average(result[:, :, 2])
                result[:, :, 1] = result[:, :, 1] - (
                    (avg_a - 128 + shift_gr) * (result[:, :, 0] / 255.0) * 1.1
                )
                result[:, :, 2] = result[:, :, 2] - (
                    (avg_b - 128 + shift_yb) * (result[:, :, 0] / 255.0) * 1.1
                )
                self.result = cv2.cvtColor(result, cv2.COLOR_LAB2BGR)

                # Write your code here
                wrapper.store_image(img, "current_image")
                res = True
            else:
                wrapper.store_image(wrapper.current_image, "current_image")
                res = True
        except Exception as e:
            res = False
            logger.error(f"AutoWBGWA FAILED, exception: {repr(e)}")
        else:
            pass
        finally:
            return res

    @property
    def name(self):
        return "Auto WB Grey World Assumption"

    @property
    def package(self):
        return "TPMP"

    @property
    def is_wip(self):
        return True

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
        return ["Exposure fixing", "Pre processing", "White balance"]

    @property
    def description(self):
        return """'Automatic White Balancing with Gray world assumption"""

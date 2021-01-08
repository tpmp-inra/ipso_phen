import cv2

import logging
import os

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))

from ipso_phen.ipapi.base.ipt_abstract import IptBase


class IptConvertImageToMask(IptBase):
    def build_params(self):
        self.add_enabled_checkbox()
        self.add_spin_box(
            name="threshold",
            desc="Threshold",
            default_value=128,
            minimum=0,
            maximum=255,
            hint="All value > threshold will be set to 255, others to 0",
        )

    def process_wrapper(self, **kwargs):
        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return False

        res = False
        try:
            if self.get_value_of("enabled") == 1:
                img = wrapper.current_image

                if len(img.shape) > 2 and img.shape[2] >= 1:
                    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

                t = self.get_value_of("threshold")
                img[img > t] = 255
                img[img <= t] = 0

                wrapper.store_image(img, "current_image")
                self.result = img
                res = True
            else:
                wrapper.store_image(wrapper.current_image, "image_2_mask")
                res = True
        except Exception as e:
            res = False
            logger.error(f"Convert image to mask FAILED, exception: {repr(e)}")
        else:
            pass
        finally:
            return res

    @property
    def name(self):
        return "Convert image to mask"

    @property
    def is_wip(self):
        return True

    @property
    def package(self):
        return "TPMP"

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
        return ["Threshold"]

    @property
    def description(self):
        return """
        Convert an image to a mask using a threshold.
        If source image is multi channel, default conversion will be applied.
        """

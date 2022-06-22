import cv2

from ipso_phen.ipapi.base.ipt_abstract import IptBase
from ipso_phen.ipapi.base.ip_common import ToolFamily, ensure_odd
from ipso_phen.ipapi.base.ipt_abstract import IptBase
from ipso_phen.ipapi.base import ip_common as ipc


import os
import logging

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))


class IptGaussianFiltering(IptBase):
    def build_params(self):
        self.add_enabled_checkbox()

        self.add_combobox(
            name="source",
            desc="Source",
            default_value="current_image",
            values={"current_image": "Current image", "mask": "Current mask"},
        )

        self.add_spin_box(
            name="kernel_size",
            desc="Gaussian filter size (odd values only)",
            default_value=3,
            minimum=3,
            maximum=101,
        )
        self.add_roi_selector()

    def process_wrapper(self, **kwargs):
        """
        Gaussian filtering:
        'Apply Gaussian filter
        Real time: True

        Keyword Arguments (in parentheses, argument name):
            * Activate tool (enabled): Toggle whether or not tool is active
            * Source (source):
            * Gaussian filter size (odd values only) (kernel_size):"""

        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return False

        res = False
        try:
            if self.get_value_of("enabled") == 1:
                kernel_size = ensure_odd(self.get_value_of("kernel_size"))
                img = wrapper.current_image
                if self.output_type == ipc.IO_MASK:
                    mask = self.get_mask()
                    if mask is None:
                        logger.error(
                            "Failure Match image and mask resolution: mask must be initialized"
                        )
                        return
                else:
                    mask = None

                self.result = cv2.GaussianBlur(
                    src=img if self.output_type == ipc.IO_IMAGE else mask,
                    ksize=(kernel_size, kernel_size),
                    sigmaX=(kernel_size - 1) / 6,
                    sigmaY=(kernel_size - 1) / 6,
                )
                if self.output_type == ipc.IO_MASK:
                    self.result[self.result != 0] = 255

                self.result = self.compose_image_with_rois(
                    fgd_img=self.result,
                    bkg_img=self.wrapper.current_image,
                )

                wrapper.store_image(self.result, "current_image")
                res = True
            else:
                wrapper.store_image(wrapper.current_image, "current_image")
                res = True
        except Exception as e:
            res = False
            logger.error(f"Median Fileter FAILED, exception: {repr(e)}")
        else:
            pass
        finally:
            return res

    @property
    def output_type(self):
        return ipc.IO_MASK if self.get_value_of("source") == "mask" else ipc.IO_IMAGE

    @property
    def name(self):
        return "Gaussian filtering"

    @property
    def package(self):
        return "TPMP"

    @property
    def is_wip(self):
        return False

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
        return ["Mask cleanup", "Pre processing"]

    @property
    def description(self):
        return """'Apply Gaussian filter"""

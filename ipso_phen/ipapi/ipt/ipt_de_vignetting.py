from ipso_phen.ipapi.base.ipt_abstract import IptBase

import os
import logging

import cv2
import numpy as np

import ipso_phen.ipapi.base.ip_common as ipc

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))


class IptDeVignetting(IptBase):
    def build_params(self):
        self.add_enabled_checkbox()
        self.add_spin_box(
            name="dilate_kernel_size",
            desc="Dillate's kernel size",
            default_value=7,
            minimum=3,
        )
        self.add_spin_box(
            name="median_filter_kernel_size",
            desc="Dillate's kernel size",
            default_value=7,
            minimum=3,
        )
        self.add_checkbox(
            name="normalize",
            desc="Nprmalize output?",
            default_value=0,
        )

    def process_wrapper(self, **kwargs):
        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return False

        res = False
        try:
            if self.get_value_of("enabled") == 1:
                h, s, v = cv2.split(
                    cv2.cvtColor(
                        wrapper.current_image,
                        cv2.COLOR_BGR2HSV,
                    )
                )
                dilate_kernel_size = ipc.ensure_odd(
                    self.get_value_of("dilate_kernel_size")
                )
                median_filter_kernel_size = ipc.ensure_odd(
                    self.get_value_of("median_filter_kernel_size")
                )

                v_dilated = cv2.dilate(
                    v,
                    np.ones(
                        (dilate_kernel_size, dilate_kernel_size),
                        np.uint8,
                    ),
                )
                v_bg_img = cv2.medianBlur(v_dilated, median_filter_kernel_size)
                wrapper.store_image(v_bg_img, "v_bg_img")

                diff_img = 255 - cv2.absdiff(v, v_bg_img)
                wrapper.store_image(diff_img, "diff_img")

                if self.get_value_of("normalize") == 0:
                    self.result = cv2.merge((h, s, diff_img))
                else:
                    self.result = cv2.merge(
                        (
                            h,
                            s,
                            cv2.normalize(
                                diff_img,
                                None,
                                alpha=0,
                                beta=255,
                                norm_type=cv2.NORM_MINMAX,
                                dtype=cv2.CV_8UC1,
                            ),
                        )
                    )
                self.result = diff_img  # cv2.cvtColor(self.result, cv2.COLOR_HSV2RGB)
                wrapper.store_image(self.result, "devignetting")
                res = True
            else:
                wrapper.store_image(wrapper.current_image, "current_image")
                res = True
        except Exception as e:
            res = False
            logger.error(f"De vignetting FAILED, exception: {repr(e)}")
        else:
            pass
        finally:
            return res

    @property
    def name(self):
        return "De vignetting"

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
        return ["Exposure fixing", "Pre processing"]

    @property
    def description(self):
        return """'Removes vignetting from image"""

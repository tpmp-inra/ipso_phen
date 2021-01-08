import numpy as np
import cv2

import logging
import os

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))

from ipso_phen.ipapi.base.ipt_abstract import IptBase
from ipso_phen.ipapi.tools.regions import RectangleRegion
import ipso_phen.ipapi.base.ip_common as ipc


class IptFixWhiteBalanceWithRoi(IptBase):
    def build_params(self):
        self.add_enabled_checkbox()
        self.add_label(
            name="lbl_roi_hint_1", desc='ROIs should be of type "keep" or "delete"'
        )
        self.add_label(name="lbl_roi_hint_2", desc="Only static ROIs are allowed")
        self.add_roi_selector()

    def process_wrapper(self, **kwargs):
        """
        Fix white balance with ROI:

        Fixes image white balance from ROI that is supposed to be white.
        ROI must be present in pipeline.
        ROIs will be used as keep ROIs.
        Only static ROIs are allowed.

        Real time: True

        Keyword Arguments (in parentheses, argument name):
            * Activate tool (enabled): Toggle whether or not tool is active
            * Name of ROI to be used (roi_names): Operation will only be applied inside of ROI
            * ROI selection mode (roi_selection_mode):
        """
        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return False

        res = False
        try:
            if self.get_value_of("enabled") == 1:
                img = wrapper.current_image

                # Apply ROIs
                rois = self.get_ipt_roi(
                    wrapper=wrapper,
                    roi_names=self.get_value_of("roi_names").replace(" ", "").split(","),
                    selection_mode=self.get_value_of("roi_selection_mode"),
                )
                if not rois:
                    logger.error("Warning Fix white balance with ROI, missing ROI")
                    rois = [RectangleRegion(width=wrapper.width, height=wrapper.height)]

                patch = wrapper.keep_rois(src_mask=img, tags=rois)
                b, g, r = cv2.split(patch)
                b_avg = np.average(b[b != 0])
                g_avg = np.average(g[g != 0])
                r_avg = np.average(r[r != 0])
                lum = b_avg * 0.0722 + g_avg * 0.7152 + r_avg * 0.2126

                b, g, r = cv2.split(img)
                b = b.astype(np.float) * lum / b_avg
                g = g.astype(np.float) * lum / g_avg
                r = r.astype(np.float) * lum / r_avg

                self.result = self.to_uint8(cv2.merge([b, g, r]))

                wrapper.store_image(self.result, "fix_wb_roi")
                res = True
            else:
                wrapper.store_image(wrapper.current_image, "current_image")
                res = True
        except Exception as e:
            res = False
            logger.error(f'Failed to process {self. name}: "{repr(e)}"')
        else:
            pass
        finally:
            return res

    @property
    def name(self):
        return "Fix white balance with ROI"

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
        return [ipc.ToolFamily.WHITE_BALANCE]

    @property
    def description(self):
        return """ Fixes image white balance from ROI that is supposed to be white.
        ROI must be present in pipeline.
        ROIs must be of type 'keep' or 'delete'.
        Only static ROIs are allowed."""

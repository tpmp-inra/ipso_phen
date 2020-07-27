from ipapi.base.ipt_abstract import IptBase
import numpy as np
import cv2

import logging

logger = logging.getLogger(__name__)

from ipapi.base import ip_common as ipc


class IptFilterContourBySize(IptBase):
    def build_params(self):
        self.add_enabled_checkbox()
        self.add_spin_box(
            name="min_threshold",
            desc="Lower bound limit",
            default_value=0,
            minimum=0,
            maximum=100000000,
            hint="Only contours bigger than lower limit bound will be kept",
        )
        self.add_spin_box(
            name="max_threshold",
            desc="Upper bound limit",
            default_value=100000000,
            minimum=0,
            maximum=100000000,
            hint="Only contours smaller than lower limit bound will be kept",
        )
        self.add_roi_selector()

    def process_wrapper(self, **kwargs):
        """
        Filter contour by size:
        'Keep or descard contours according to their size
        Real time: False

        Keyword Arguments (in parentheses, argument name):
            * Activate tool (enabled): Toggle whether or not tool is active
            * Lower bound limit (min_threshold): Only contours bigger than lower limit bound will be kept
            * Upper bound limit (max_threshold): Only contours smaller than lower limit bound will be kept
            * Name of ROI to be used (roi_names): Operation will only be applied inside of ROI
            * ROI selection mode (roi_selection_mode):
        """
        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return False

        res = False
        try:
            if self.get_value_of("enabled") == 1:
                mask = self.get_mask()
                if mask is None:
                    wrapper.error_holder.add_error(
                        f"FAIL {self.name}: mask must be initialized", target_logger=logger
                    )
                    return

                lt, ut = self.get_value_of("min_threshold"), self.get_value_of("max_threshold")

                # Get ROIs as mask
                rois = self.get_ipt_roi(
                    wrapper=wrapper,
                    roi_names=self.get_value_of("roi_names").replace(" ", "").split(","),
                    selection_mode=self.get_value_of("roi_selection_mode"),
                )
                if rois:
                    rois_mask = np.zeros_like(mask)
                    for roi in rois:
                        rois_mask = roi.draw_to(dst_img=rois_mask, line_width=-1, color=255)
                    mask = np.bitwise_and(mask, rois_mask)
                wrapper.store_image(mask, "mask_after_roi")

                # Get source contours
                contours = ipc.get_contours(
                    mask=mask, retrieve_mode=cv2.RETR_LIST, method=cv2.CHAIN_APPROX_SIMPLE
                )
                dbg_mask = np.dstack(
                    (np.zeros_like(mask), np.zeros_like(mask), np.zeros_like(mask))
                )
                colors = ipc.build_color_steps(ipc.C_BLUE, ipc.C_YELLOW, len(contours))
                for clr, cnt in zip(colors, reversed(contours[:-1])):
                    cv2.drawContours(dbg_mask, [cnt], 0, clr, -1)
                fnt = (cv2.FONT_HERSHEY_SIMPLEX, 0.6)

                for cnt in reversed(contours[:-1]):
                    area_ = cv2.contourArea(cnt)
                    x, y, w, h = cv2.boundingRect(cnt)
                    x += w // 2 - 10
                    y += h // 2
                    if area_ > 0:
                        cv2.putText(
                            dbg_mask, f"{area_}", (x, y), fnt[0], fnt[1], (255, 255, 255), 2
                        )
                wrapper.store_image(image=dbg_mask, text="all_contours")

                dbg_mask = np.dstack(
                    (np.zeros_like(mask), np.zeros_like(mask), np.zeros_like(mask))
                )
                out_mask = np.zeros_like(mask)
                fnt = (cv2.FONT_HERSHEY_SIMPLEX, 0.6)
                for cnt in contours:
                    area_ = cv2.contourArea(cnt)
                    if lt < area_ < ut:
                        cv2.drawContours(out_mask, [cnt], 0, 255, -1)
                        cv2.drawContours(dbg_mask, [cnt], 0, ipc.C_GREEN, -1)
                        clr = ipc.C_LIME
                    else:
                        clr = ipc.C_RED
                    x, y, w, h = cv2.boundingRect(cnt)
                    x += w // 2 - 10
                    y += h // 2
                    cv2.putText(
                        dbg_mask, f"{area_}", (x, y), fnt[0], fnt[1], clr, thickness=2,
                    )

                wrapper.store_image(image=out_mask, text="filtered_contours")
                wrapper.store_image(image=dbg_mask, text="tagged_contours")
                self.result = out_mask
                if rois:
                    for roi in rois:
                        dbg_mask = roi.draw_to(dst_img=dbg_mask, line_width=8, color=255)
                self.demo_image = dbg_mask
                res = True
            else:
                wrapper.store_image(wrapper.current_image, "current_image")
                res = True
        except Exception as e:
            res = False
            logger.exception(f"Filter contour by size FAILED, exception: {repr(e)}")
        else:
            pass
        finally:
            return res

    @property
    def name(self):
        return "Filter contour by size"

    @property
    def package(self):
        return "TPMP"

    @property
    def real_time(self):
        return False

    @property
    def result_name(self):
        return "mask"

    @property
    def output_kind(self):
        return "mask"

    @property
    def use_case(self):
        return [ipc.ToolFamily.MASK_CLEANUP]

    @property
    def description(self):
        return """'Keep or descard contours according to their size"""

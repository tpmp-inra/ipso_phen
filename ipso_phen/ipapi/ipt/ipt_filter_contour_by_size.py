from ipso_phen.ipapi.base.ipt_abstract import IptBase
from ipso_phen.ipapi.tools import regions
import numpy as np
import cv2

import logging
import os

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))

from ipso_phen.ipapi.base import ip_common as ipc


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
                    logger.error(f"FAIL {self.name}: mask must be initialized")
                    return

                lt, ut = self.get_value_of("min_threshold"), self.get_value_of(
                    "max_threshold"
                )

                # Get source contours
                contours = [
                    c
                    for c in ipc.get_contours(
                        mask=mask,
                        retrieve_mode=cv2.RETR_LIST,
                        method=cv2.CHAIN_APPROX_SIMPLE,
                    )
                    if cv2.contourArea(c, True) < 0
                ]
                contours.sort(key=lambda x: cv2.contourArea(x), reverse=True)
                colors = ipc.build_color_steps(step_count=len(contours))

                dbg_img = np.dstack(
                    (np.zeros_like(mask), np.zeros_like(mask), np.zeros_like(mask))
                )
                for clr, cnt in zip(colors, contours):
                    cv2.drawContours(dbg_img, [cnt], 0, clr, -1)
                dbg_img = np.dstack(
                    (
                        cv2.bitwise_and(dbg_img[:, :, 0], mask),
                        cv2.bitwise_and(dbg_img[:, :, 1], mask),
                        cv2.bitwise_and(dbg_img[:, :, 2], mask),
                    )
                )
                wrapper.store_image(
                    image=dbg_img,
                    text="all_contours",
                )

                fnt = (cv2.FONT_HERSHEY_SIMPLEX, 0.6)
                for cnt in contours:
                    area_ = cv2.contourArea(cnt)
                    x, y, w, h = cv2.boundingRect(cnt)
                    x += w // 2 - 10
                    y += h // 2
                    if area_ > 0:
                        cv2.putText(
                            dbg_img,
                            f"{area_}",
                            (x, y),
                            fnt[0],
                            fnt[1],
                            (255, 255, 255),
                            2,
                        )
                wrapper.store_image(
                    image=dbg_img,
                    text="all_contours_with_sizes",
                )

                dbg_img = np.dstack(
                    (np.zeros_like(mask), np.zeros_like(mask), np.zeros_like(mask))
                )
                out_mask = np.zeros_like(mask)

                # Discarded contours
                size_cnts = np.dstack(
                    (np.zeros_like(mask), np.zeros_like(mask), np.zeros_like(mask))
                )
                for cnt in contours:
                    area_ = cv2.contourArea(cnt)
                    if area_ < lt:
                        cv2.drawContours(size_cnts, [cnt], 0, ipc.C_RED, -1)
                    elif area_ > ut:
                        cv2.drawContours(size_cnts, [cnt], 0, ipc.C_BLUE, -1)
                    else:
                        cv2.drawContours(size_cnts, [cnt], 0, ipc.C_WHITE, -1)
                wrapper.store_image(image=size_cnts, text="cnts_by_size")

                # Discarded contours
                size_cnts = np.dstack(
                    (np.zeros_like(mask), np.zeros_like(mask), np.zeros_like(mask))
                )
                for cnt in sorted(
                    contours, key=lambda x: cv2.contourArea(x), reverse=True
                ):
                    area_ = cv2.contourArea(cnt)
                    if area_ < lt:
                        cv2.drawContours(size_cnts, [cnt], 0, ipc.C_RED, -1)
                    elif area_ > ut:
                        cv2.drawContours(size_cnts, [cnt], 0, ipc.C_BLUE, -1)
                    else:
                        cv2.drawContours(size_cnts, [cnt], 0, ipc.C_WHITE, -1)
                wrapper.store_image(image=size_cnts, text="cnts_by_size_reversed")

                for cnt in contours:
                    area_ = cv2.contourArea(cnt)
                    if not (lt < area_ < ut):
                        cv2.drawContours(dbg_img, [cnt], 0, ipc.C_RED, -1)
                # Discarded contours borders
                for cnt in contours:
                    area_ = cv2.contourArea(cnt)
                    if not (lt < area_ < ut):
                        cv2.drawContours(dbg_img, [cnt], 0, ipc.C_MAROON, 4)
                # Kept contours
                for cnt in contours:
                    area_ = cv2.contourArea(cnt)
                    if lt < area_ < ut:
                        cv2.drawContours(out_mask, [cnt], 0, 255, -1)
                        cv2.drawContours(dbg_img, [cnt], 0, ipc.C_GREEN, -1)
                    else:
                        cv2.drawContours(out_mask, [cnt], 0, 0, -1)
                        cv2.drawContours(dbg_img, [cnt], 0, ipc.C_RED, -1)
                dbg_img = np.dstack(
                    (
                        cv2.bitwise_and(dbg_img[:, :, 0], mask),
                        cv2.bitwise_and(dbg_img[:, :, 1], mask),
                        cv2.bitwise_and(dbg_img[:, :, 2], mask),
                    )
                )
                # Discarded sizes
                for cnt in contours:
                    area_ = cv2.contourArea(cnt)
                    if not (lt < area_ < ut):
                        x, y, w, h = cv2.boundingRect(cnt)
                        x += w // 2 - 10
                        y += h // 2
                        cv2.putText(
                            dbg_img,
                            f"{area_}",
                            (x, y),
                            fnt[0],
                            fnt[1],
                            ipc.C_RED,
                            thickness=2,
                        )
                # Kept sizes
                for cnt in contours:
                    area_ = cv2.contourArea(cnt)
                    if lt < area_ < ut:
                        x, y, w, h = cv2.boundingRect(cnt)
                        x += w // 2 - 10
                        y += h // 2
                        cv2.putText(
                            dbg_img,
                            f"{area_}",
                            (x, y),
                            fnt[0],
                            fnt[1],
                            ipc.C_LIME,
                            thickness=2,
                        )

                out_mask = cv2.bitwise_and(
                    out_mask,
                    mask,
                )

                # Apply ROIs if needed
                rois = self.get_ipt_roi(
                    wrapper=wrapper,
                    roi_names=self.get_value_of("roi_names").replace(" ", "").split(","),
                    selection_mode=self.get_value_of("roi_selection_mode"),
                )
                if rois:
                    untouched_mask = regions.delete_rois(rois=rois, image=self.get_mask())
                    self.result = cv2.bitwise_or(
                        untouched_mask, regions.keep_rois(rois=rois, image=out_mask)
                    )
                    self.demo_image = cv2.bitwise_or(
                        dbg_img,
                        np.dstack((untouched_mask, untouched_mask, untouched_mask)),
                    )
                else:
                    self.result = out_mask
                    self.demo_image = dbg_img

                wrapper.store_image(image=self.result, text="filtered_contours")
                wrapper.store_image(image=self.demo_image, text="tagged_contours")

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

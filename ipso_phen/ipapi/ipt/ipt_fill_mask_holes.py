import numpy as np
import cv2

import logging
import os

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))

from ipso_phen.ipapi.base.ipt_abstract_analyzer import IptBaseAnalyzer
import ipso_phen.ipapi.base.ip_common as ipc


class IptFillMaskHoles(IptBaseAnalyzer):
    def build_params(self):
        self.add_enabled_checkbox()
        self.add_roi_selector()
        self.add_label(desc="Apply morphology operator before filling")
        self.add_morphology_operator(default_operator="none")
        self.add_checkbox(
            name="invert",
            desc="Invert mask before filling",
            default_value=0,
            hint="Mask will be inverted once again at the end",
        )
        self.add_checkbox(
            name="count_holes",
            desc="Count filled holes",
            default_value=False,
            hint="Display number of holes filled and return value",
        )

    def process_wrapper(self, **kwargs):
        """
        Fill mask holes:
        Fills holes in mask
        Real time: False

        Keyword Arguments (in parentheses, argument name):
            * Activate tool (enabled): Toggle whether or not tool is active
            * Name of ROI to be used (roi_names): Operation will only be applied inside of ROI
            * ROI selection mode (roi_selection_mode):
            * Morphology operator (morph_op):
            * Kernel size (kernel_size):
            * Kernel shape (kernel_shape):
            * Iterations (proc_times):
            * Invert mask before filling (invert): Mask will be inverted once again at the end
        """
        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return False

        res = False
        try:
            if self.get_value_of("enabled") == 1:
                img = wrapper.current_image
                mask = self.get_mask()
                if mask is None:
                    logger.error(f"FAIL {self.name}: mask must be initialized")
                    return

                rois = self.get_ipt_roi(
                    wrapper=wrapper,
                    roi_names=self.get_value_of("roi_names").replace(" ", "").split(","),
                )
                if len(rois) > 0:
                    mask = wrapper.keep_rois(mask, rois)
                    merge_at_end = True
                else:
                    merge_at_end = False

                mask = self.apply_morphology_from_params(mask, store_result=True)

                cnt, hierarchy = cv2.findContours(
                    image=mask, mode=cv2.RETR_TREE, method=cv2.CHAIN_APPROX_SIMPLE
                )

                if cnt is None or not cnt or hierarchy is None:
                    self.result = wrapper.mask
                else:
                    dbg_img = np.dstack(
                        (
                            np.zeros_like(mask),
                            np.zeros_like(mask),
                            np.zeros_like(mask),
                        )
                    )
                    fnt = (cv2.FONT_HERSHEY_SIMPLEX, 0.6)
                    colors = ipc.build_color_steps(step_count=len(cnt))
                    i = 0
                    for c, h in zip(cnt, hierarchy[0]):
                        if self.get_value_of("count_holes") == 1:
                            if h[3] != -1:
                                i += 1
                                cv2.drawContours(
                                    image=dbg_img,
                                    contours=[c],
                                    contourIdx=-1,
                                    color=colors[i],
                                    thickness=-1,
                                )
                                x, y, w, height = cv2.boundingRect(c)
                                x += w // 2 - 10
                                y += height // 2
                                cv2.putText(
                                    dbg_img,
                                    f"{i}",
                                    (x, y),
                                    fnt[0],
                                    fnt[1],
                                    ipc.C_WHITE,
                                    2,
                                )
                        else:
                            if h[3] == -1:
                                color = ipc.C_BLUE
                            elif h[3] == 0:
                                color = ipc.C_CYAN
                            elif h[3] == 1:
                                color = ipc.C_YELLOW
                            elif h[3] == 2:
                                color = ipc.C_GREEN
                            elif h[3] == 3:
                                color = ipc.C_ORANGE
                            elif h[3] == 4:
                                color = ipc.C_MAROON
                            else:
                                color = ipc.C_FUCHSIA
                            cv2.drawContours(
                                image=dbg_img,
                                contours=[c],
                                contourIdx=-1,
                                color=color,
                                thickness=-1,
                            )
                        if h[3] != -1:
                            cv2.drawContours(
                                image=mask,
                                contours=[c],
                                contourIdx=-1,
                                color=255,
                                thickness=-1,
                            )

                    wrapper.store_image(dbg_img, "tagged_contours")

                    if merge_at_end:
                        self.result = cv2.bitwise_or(mask, wrapper.mask)
                    else:
                        self.result = mask

                    self.demo_image = dbg_img

                # Write your code here
                wrapper.store_image(self.result, "filled_mask")
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
        return "Fill mask holes"

    @property
    def package(self):
        return "IPSO Phen"

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
        return [ipc.ToolFamily.MASK_CLEANUP, ipc.ToolFamily.FEATURE_EXTRACTION]

    @property
    def description(self):
        return "Fills holes in mask"

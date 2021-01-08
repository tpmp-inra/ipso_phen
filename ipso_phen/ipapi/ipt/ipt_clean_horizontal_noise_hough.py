import numpy as np
import cv2

import logging
import os

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))

from ipso_phen.ipapi.base.ipt_abstract import IptBase
from ipso_phen.ipapi.base import ip_common as ipc


class IptCleanHorizontalNoiseHough(IptBase):
    def build_params(self):
        self.add_enabled_checkbox()
        self.add_slider(
            name="votes_threshold",
            desc="Votes threshold",
            default_value=100,
            minimum=0,
            maximum=1000,
            hint="Threshold to allow a line",
        )

    def process_wrapper(self, **kwargs):
        """
        Clean horizontal noise (Hough method):
        Removes noise in the form of horizontal lines from masks using Hough transformation.
        Used with light barriers
        Real time: False

        Keyword Arguments (in parentheses, argument name):
            * Activate tool (enabled): Toggle whether or not tool is active
            * Votes threshold (votes_threshold): Threshold to allow a line
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
                votes_threshold = self.get_value_of("votes_threshold", 100)

                stable_ = False
                iter_count_ = 0
                min_angle, max_angle = (
                    np.pi / 2 - (np.pi / 2 * 0.01),
                    np.pi / 2 + (np.pi / 2 * 0.01),
                )
                all_lines_img = np.dstack((mask, mask, mask))
                lines_removed_ = []
                nz_pixels = np.count_nonzero(mask)
                while not stable_ and (iter_count_ < 100):
                    stable_ = True
                    iter_count_ += 1
                    edges = cv2.Canny(mask, 0, 255)
                    wrapper.store_image(edges, f"edges iter {iter_count_}")
                    lines = cv2.HoughLines(
                        edges, rho=1, theta=np.pi / 180, threshold=votes_threshold
                    )
                    if lines is not None:
                        erosion_mask = np.zeros_like(mask)
                        kernel = np.ones((5, 1))
                        lines_img = np.dstack((mask, mask, mask))
                        l, r = 0, mask.shape[1]
                        for l_cpt, line in enumerate(lines):
                            for rho, theta in line:
                                a = np.cos(theta)
                                b = np.sin(theta)
                                x0 = a * rho
                                y0 = b * rho
                                x1 = int(x0 + 1000 * (-b))
                                y1 = int(y0 + 1000 * a)
                                x2 = int(x0 - 1000 * (-b))
                                y2 = int(y0 - 1000 * a)
                                x1, y1 = wrapper.constraint_to_image(x1, y1, mask)
                                x2, y2 = wrapper.constraint_to_image(x2, y2, mask)
                                if not (min_angle < abs(theta) < max_angle):
                                    cv2.line(lines_img, (x1, y1), (x2, y2), ipc.C_RED, 2)
                                    continue
                                stable_ = False
                                if max(y1, y2) < mask.shape[0] - 10:
                                    lines_removed_.append(y1)
                                cv2.line(lines_img, (x1, y1), (x2, y2), ipc.C_BLUE, 2)
                                cv2.line(all_lines_img, (x1, y1), (x2, y2), ipc.C_BLUE, 1)
                                if min(y1, y2) <= 4:
                                    mask[min(y1, y2) : max(y1, y2) + 1, l:r] = 0
                                else:
                                    t, b = min(y1, y2) - 2, max(y1, y2) + 2
                                    erosion_mask[t:b, l:r] = mask[t:b, l:r]
                        c_minus = wrapper.multi_and((255 - erosion_mask, mask))
                        wrapper.store_image(
                            lines_img, f"horizontal_lines iter {iter_count_}"
                        )
                        wrapper.store_image(
                            erosion_mask,
                            f"horizontal_erosion_target iter {iter_count_}",
                        )
                        wrapper.store_image(
                            c_minus, f"horizontal_mask_minus_erosion iter {iter_count_}"
                        )
                        erosion_mask = cv2.morphologyEx(
                            erosion_mask, cv2.MORPH_OPEN, kernel
                        )
                        wrapper.store_image(
                            erosion_mask,
                            f"horizontal_erosion_result iter {iter_count_}",
                        )
                        mask = wrapper.multi_or((c_minus, erosion_mask))
                        wrapper.store_image(mask, f"horizontal_mask iter {iter_count_}")
                    else:
                        break
                if lines_removed_:
                    if "hor_lines_removed" in wrapper.data_output:
                        wrapper.data_output["hor_lines_removed"].append(lines_removed_)
                    else:
                        wrapper.data_output["hor_lines_removed"] = lines_removed_
                wrapper.data_output["hor_pixels_removed"] = nz_pixels - np.count_nonzero(
                    mask
                )
                wrapper.data_output["hor_lines_removed_hit_plant"] = 0
                wrapper.store_image(all_lines_img, "horizontal_all_eroded_lines")

                self.result = mask

                wrapper.store_image(mask, "hough_line_cleaned_mask")
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
        return "Clean horizontal noise (Hough method)"

    @property
    def package(self):
        return "Heliasen"

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
        return "Removes noise in the form of horizontal lines from masks using Hough transformation.\nUsed with light barriers"

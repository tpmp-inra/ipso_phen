import numpy as np
import cv2

import logging
import os

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))

from ipso_phen.ipapi.base.ipt_abstract import IptBase
from ipso_phen.ipapi.base import ip_common as ipc


class IptCleanHorizontalNoise(IptBase):
    def build_params(self):
        self.add_enabled_checkbox()
        self.add_spin_box(
            name="min_line_size",
            desc="Minimal size for a line to be considered for removal",
            default_value=11,
            minimum=2,
            maximum=4000,
        )
        self.add_spin_box(
            name="max_iter",
            desc="Maximum number of iterations to perform",
            default_value=100,
            minimum=1,
            maximum=1000,
        )
        self.add_checkbox(
            name="fully_isolated", desc="Remove blocks of lines", default_value=1
        )

    def process_wrapper(self, **kwargs):
        """
        Clean horizontal noise:
        Removes noise in the form of horizontal lines from masks.
        Used with light barriers
        Real time: False

        Keyword Arguments (in parentheses, argument name):
            * Activate tool (enabled): Toggle whether or not tool is active
            * Minimal size for a line to be considered for removal (min_line_size):
            * Maximum number of iterations to perform (max_iter):
            * Remove blocks of lines (fully_isolated):
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

                nz_pixels = np.count_nonzero(mask)
                min_line_size = self.get_value_of("min_line_size")
                max_iter = self.get_value_of("max_iter")
                fully_isolated = self.get_value_of("fully_isolated")
                stable_ = False
                iter_ = 0
                all_lines = []

                while not stable_ and (iter_ < max_iter):
                    stable_ = True
                    iter_ += 1
                    msk_data = ipc.MaskData(mask=mask)
                    for l in msk_data.lines_data:
                        if (l.solidity >= 0.99) and (
                            l.nz_span >= msk_data.mask_width - 4
                        ):
                            ld_up, ld_down = msk_data.find_top_bottom_non_full_lines(
                                l.height_pos
                            )
                            l.merge_or(ld_up, ld_down)
                            all_lines.append([(l.height_pos, 0, msk_data.mask_width)])
                            mask[l.height_pos] = 0
                            for i in l.nz_pos:
                                mask[l.height_pos][i] = 255
                        else:
                            lines = msk_data.horizontal_lines_at(
                                l.height_pos, min_line_size, fully_isolated
                            )
                            if not lines:
                                continue
                            all_lines.append(lines)
                            for i, line in enumerate(lines):
                                stable_ = False
                                cv2.line(
                                    mask, (line[1], line[0]), (line[2], line[0]), 0, 1
                                )
                    wrapper.store_image(mask, f"cleaned_image_iter_{iter_}")

                lines_removed_ = list(set([line[0][0] for line in all_lines]))
                if lines_removed_:
                    if "hor_lines_removed" in wrapper.data_output:
                        wrapper.data_output["hor_lines_removed"].extend(lines_removed_)
                    else:
                        wrapper.data_output["hor_lines_removed"] = lines_removed_
                wrapper.data_output["hor_pixels_removed"] = nz_pixels - np.count_nonzero(
                    mask
                )
                wrapper.data_output["hor_lines_removed_hit_plant"] = 0

                self.result = mask

                wrapper.store_image(self.result, "line_cleaned_mask")
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
        return "Clean horizontal noise"

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
        return "Removes noise in the form of horizontal lines from masks.\nUsed with light barriers"

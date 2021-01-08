import math
import numpy as np
import cv2

import logging
import os

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))

import ipso_phen.ipapi.base.ip_common as ipc
from ipso_phen.ipapi.base.ipt_abstract import IptBase


class IptRemovePlantGuide(IptBase):
    def build_params(self):
        self.add_enabled_checkbox()

        self.add_spin_box(
            name="delete_too_narrow",
            desc="If narrower than that assume it's a guide",
            default_value=8,
            minimum=0,
            maximum=10000,
            hint="Normally should be set to the actual width in pixels of the guide",
        )
        self.add_spin_box(
            name="keep_and_stop_too_wide",
            desc="Expected minimal plant width",
            default_value=60,
            minimum=0,
            maximum=10000,
            hint="If it is this wide it must be the plant",
        )
        self.add_spin_box(
            name="investigate_lower_bound",
            desc="Minimal width value to start investigating",
            default_value=16,
            minimum=0,
            maximum=10000,
            hint="If line width is between lower and upper bounds the algorithm will look closely.",
        )
        self.add_spin_box(
            name="investigate_upper_bound",
            desc="Maximal width value to start investigating",
            default_value=16,
            minimum=0,
            maximum=10000,
            hint="If line width is between lower and upper bounds the algorithm will look closely.",
        )

    def clean_vertical_line_noise(
        self,
        src,
        wrapper,
        min_angle: float,
        max_angle: float,
        min_height: int,
        threshold: int = 10,
        min_line_size: int = 30,
        max_line_gap: int = 0,
    ):
        stable_ = False
        iter_count_ = 0
        all_lines_img = np.dstack((src, src, src))
        lines_removed_ = 0
        nz_pixels = np.count_nonzero(src)
        while not stable_ and (iter_count_ < 100):
            stable_ = True
            iter_count_ += 1
            edges = cv2.Canny(src, 0, 255)
            wrapper.store_image(edges, f"vertical_edges iter {iter_count_}")
            lines = cv2.HoughLinesP(
                edges,
                rho=1,
                theta=np.pi / 180,
                threshold=threshold,
                minLineLength=min_line_size,
                maxLineGap=max_line_gap,
            )
            if lines is not None:
                lines_img = np.dstack((src, src, src))
                for line in lines:
                    x1, y1, x2, y2 = line[0]
                    rad = math.atan2(y2 - y1, x2 - x1)
                    if not (min_angle < abs(rad) < max_angle) or (
                        (y2 > min_height) and (y1 > min_height)
                    ):
                        cv2.rectangle(lines_img, (x1, y1), (x2, y2), ipc.C_RED, 2)
                        continue
                    stable_ = False
                    lines_removed_ += 1
                    # Delete the line
                    cv2.rectangle(src, (x1, y1), (x2, y2), ipc.C_BLACK, 2)
                    cv2.rectangle(lines_img, (x1, y1), (x2, y2), ipc.C_BLUE, 2)
                    cv2.rectangle(all_lines_img, (x1, y1), (x2, y2), ipc.C_BLUE, 1)
                wrapper.store_image(lines_img, f"vertical_lines iter {iter_count_}")
                wrapper.store_image(src, f"vertical_mask iter {iter_count_}")
            else:
                break
        wrapper.data_output["vert_lines_removed"] = lines_removed_
        wrapper.data_output["vert_pixels_removed"] = nz_pixels - np.count_nonzero(src)
        wrapper.store_image(all_lines_img, "vertical_all_deleted_lines")
        return src

    def process_wrapper(self, **kwargs):
        """
        Remove plant guide:
        Removes plant guide. Built for Heliasen light barrier
        Real time: False

        Keyword Arguments (in parentheses, argument name):
            * Activate tool (enabled): Toggle whether or not tool is active
            * If narrower than that assume it's a guide (delete_too_narrow):
                Normally should be set to the actual width in pixels of the guide
            * Expected minimal plant width (keep_and_stop_too_wide):
                If it is this wide it must be the plant
            * Minimal width value to start investigating (investigate_lower_bound):
                If line width is between lower and upper bounds the algorithm will look closely.
            * Maximal width value to start investigating (investigate_upper_bound):
                If line width is between lower and upper bounds the algorithm will look closely.
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

                wrapper.store_image(
                    image=mask, text="mask_before_guide_removal", force_store=True
                )

                delete_too_narrow_ = self.get_value_of("delete_too_narrow")
                keep_and_stop_too_wide_ = self.get_value_of("keep_and_stop_too_wide")
                investigate_lower_bound_ = self.get_value_of("investigate_lower_bound")
                investigate_upper_bound_ = self.get_value_of("investigate_upper_bound")

                # Find top of plant and detect guide presence
                stop_checking_ = False
                plant_top_idx = -1
                guide_found_ = False
                for line_number, line in enumerate(mask):
                    # Build line data
                    cur_ln_dt = ipc.MaskLineData(line_number, line, 0)
                    # At some point we have to admit that there is no guide
                    if not guide_found_ and (line_number > 200):
                        wrapper.data_output["expected_plant_top_position"] = False
                        break
                    if cur_ln_dt.nz_span == 0:
                        pass
                    elif (
                        stop_checking_
                        or (
                            (cur_ln_dt.nz_span >= investigate_upper_bound_)
                            and (cur_ln_dt.solidity > 0.7)
                        )
                        or (
                            (cur_ln_dt.nz_span >= keep_and_stop_too_wide_)
                            and (cur_ln_dt.solidity > 0.5)
                        )
                    ):
                        # This thing is wide, we must have reached the plant
                        plant_top_idx = line_number
                        wrapper.data_output["expected_plant_top_position"] = plant_top_idx
                        break
                    elif (
                        investigate_lower_bound_
                        < cur_ln_dt.nz_span
                        < investigate_upper_bound_
                    ):
                        # Look closely into it before deciding
                        guide_found_ = True
                    elif cur_ln_dt.nz_span < delete_too_narrow_:
                        # This is really small, delete it
                        guide_found_ = True
                    else:
                        # Unable to decide, we will take care of this later
                        pass

                # Remove vertical noise
                if guide_found_ and (plant_top_idx > 0):
                    plant_top_img = np.dstack((mask, mask, mask))
                    cv2.line(
                        plant_top_img,
                        (0, plant_top_idx),
                        (mask.shape[1], plant_top_idx),
                        ipc.C_BLUE,
                        2,
                    )
                    wrapper.store_image(plant_top_img, "plant_top")
                    mask = self.clean_vertical_line_noise(
                        src=mask,
                        wrapper=wrapper,
                        min_angle=np.pi / 2 - (np.pi / 2 * 0.05),
                        max_angle=np.pi / 2 + (np.pi / 2 * 0.05),
                        min_height=plant_top_idx,
                        threshold=80,
                        min_line_size=30,
                        max_line_gap=0,
                    )
                    wrapper.store_image(mask, "mask_after_vertical_noise_removal")
                else:
                    wrapper.data_output["vert_lines_removed"] = 0
                    wrapper.data_output["vert_pixels_removed"] = 0

                # Remove vertical noise
                stop_checking_ = False
                guide_found_ = False
                line_data = []
                last_span_ = 0
                for line_number, line in enumerate(mask):
                    # Build line data
                    cur_ln_dt = ipc.MaskLineData(line_number, line, last_span_)
                    last_span_ = cur_ln_dt.nz_span
                    line_data.append(cur_ln_dt)
                    # At some point we have to admit that there is no guide
                    if not guide_found_ and (line_number > 100):
                        stop_checking_ = True
                    if cur_ln_dt.nz_span == 0:
                        # Nothing to do
                        cur_ln_dt.tag = "no_pixels"
                    elif (
                        stop_checking_
                        or (
                            (cur_ln_dt.nz_span >= investigate_upper_bound_)
                            and (cur_ln_dt.solidity > 0.7)
                        )
                        or (cur_ln_dt.nz_span >= keep_and_stop_too_wide_)
                    ):
                        # This thing is wide, we must have reached the plant
                        stop_checking_ = True
                        cur_ln_dt.tag = "stop_checking"
                    elif (
                        investigate_lower_bound_
                        < cur_ln_dt.nz_span
                        < investigate_upper_bound_
                    ):
                        # Look closely into it before deciding
                        guide_found_ = True
                        if (
                            cur_ln_dt.solidity < 0.4
                        ):  # There's probably a plant and a guide here
                            cur_ln_dt.tag = "plant_and_guide"
                        else:  # Check the last nz_span
                            if (cur_ln_dt.last_span == 0) or (
                                cur_ln_dt.nz_span / cur_ln_dt.last_span < 2
                            ):
                                # Probably still a guide
                                cur_ln_dt.tag = "plant_start"
                            else:
                                # May be the start of the plant
                                cur_ln_dt.tag = "plant_start"
                    elif cur_ln_dt.nz_span < delete_too_narrow_:
                        # This is really small, delete it
                        guide_found_ = True
                        cur_ln_dt.tag = "to_small"
                    else:
                        # Unable to decide, we will take care of this later
                        cur_ln_dt.tag = "unknown"

                lines_img = np.dstack((mask, mask, mask))
                vt_fixed = np.zeros_like(mask)
                top_of_plant = None
                for line_number, line in enumerate(line_data):
                    if line.tag == "no_pixels":
                        pass
                    elif line.tag == "stop_checking":
                        for i in line.nz_pos:
                            lines_img[line_number][i] = ipc.C_WHITE
                            vt_fixed[line_number][i] = 255
                        if top_of_plant is None:
                            top_of_plant = line_number
                    elif line.tag == "plant_and_guide":
                        for i in line.nz_pos:
                            lines_img[line_number][i] = ipc.C_GREEN
                            vt_fixed[line_number][i] = 255
                        if top_of_plant is None:
                            top_of_plant = line_number
                    elif line.tag == "guide":
                        for i in line.nz_pos:
                            lines_img[line_number][i] = ipc.C_RED
                    elif line.tag == "to_small":
                        for i in line.nz_pos:
                            lines_img[line_number][i] = ipc.C_MAROON
                    elif line.tag == "plant_start":
                        for i in line.nz_pos:
                            lines_img[line_number][i] = ipc.C_LIME
                            vt_fixed[line_number][i] = 255
                    elif line.tag == "unknown":
                        for i in line.nz_pos:
                            lines_img[line_number][i] = ipc.C_SILVER
                            vt_fixed[line_number][i] = 255
                    else:
                        for i in line.nz_pos:
                            lines_img[line_number][i] = ipc.C_FUCHSIA
                            vt_fixed[line_number][i] = 255
                wrapper.data_output["plant_top_position"] = top_of_plant

                wrapper.store_image(lines_img, "lines_tagged")

                wrapper.store_image(image=vt_fixed, text="cleaned_image")

                self.result = vt_fixed

                res = True
            else:
                wrapper.store_image(wrapper.current_image, "current_image")
                res = True
        except Exception as e:
            res = False
            wrapper.error_holder.add_error(
                new_error_text=f'Failed to process {self. name}: "{repr(e)}"',
                new_error_level=35,
                target_logger=logger,
            )
        else:
            pass
        finally:
            return res

    @property
    def name(self):
        return "Remove plant guide"

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
        return "Removes plant guide. Built for Heliasen light barrier"

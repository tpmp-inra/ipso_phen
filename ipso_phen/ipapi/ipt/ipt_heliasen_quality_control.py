import numpy as np
import cv2

import logging
import os

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))

import ipso_phen.ipapi.base.ip_common as ipc

from ipso_phen.ipapi.base.ipt_abstract_analyzer import IptBaseAnalyzer


class IptHeliasenQualityControl(IptBaseAnalyzer):
    def build_params(self):
        self.add_enabled_checkbox()
        self.add_checkbox(
            name="binary_error",
            desc="Encode final error as binary option",
            default_value=0,
        )

    def process_wrapper(self, **kwargs):
        """
        Heliasen Quality Control:

        Needs vertical and horizontal noise removal before been called.
        Checks light barrier image quality.
        Outputs main error and partial errors.
        Real time: False

        Keyword Arguments (in parentheses, argument name):
            * Activate tool (enabled): Toggle whether or not tool is active
        """

        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return False

        res = False
        try:
            self.data_dict = {}
            if self.get_value_of("enabled") == 1:
                img = wrapper.current_image
                mask = self.get_mask()
                if mask is None:
                    logger.error(f"FAIL {self.name}: mask must be initialized")
                    return

                ept = wrapper.data_output.get("expected_plant_top_position", False)
                pt = int(wrapper.data_output.get("plant_top_position", 0))
                hlr = wrapper.data_output.get("hor_lines_removed", [])
                lrc = len(hlr)
                hlr = list(set(hlr))
                wrapper.data_output["horizontal_lines_hard_to_remove"] = lrc - len(hlr)
                hlr = np.array(hlr)
                hlr = [hlr[i] for i in np.where(hlr <= wrapper.height - 12)][0]
                wrapper.data_output["hor_lines_removed"] = len(hlr)

                report_lines = []
                guide_pixels = 0
                guide_span = 0
                last_span_ = 0

                # Initialise mask data
                msk_dt = ipc.MaskData(mask=mask)

                if msk_dt.height == 0:
                    wrapper.data_output["guide_only_pixels"] = "-"
                    wrapper.data_output["guide_average_width"] = "-"
                    return False

                mask_before_guide_removal, *_ = cv2.split(
                    wrapper.retrieve_stored_image("mask_before_guide_removal")
                )
                msk_height = mask_before_guide_removal.shape[0]
                wrapper.data_output["final_plant_top_position"] = msk_dt.top_index
                wrapper.data_output["guide_average_pixels"] = 0
                wrapper.data_output["guide_average_span"] = 0
                wrapper.data_output["guide_only_pixels"] = 0
                if msk_dt.top_index and not isinstance(ept, bool):
                    line_stop = min(min(msk_dt.top_index, int(ept)), pt)
                    active_line_count = 0
                    for l_n, line in enumerate(mask_before_guide_removal):
                        if l_n >= line_stop:
                            break
                        cur_ln_dt = ipc.MaskLineData(l_n, line, last_span_)
                        guide_pixels += cur_ln_dt.nz_count
                        guide_span += cur_ln_dt.nz_span
                        if cur_ln_dt.nz_span > 0:
                            active_line_count += 1
                    wrapper.data_output["guide_only_pixels"] = guide_pixels
                    if active_line_count > 0:
                        wrapper.data_output["guide_average_pixels"] = g_avg_ap = (
                            guide_pixels / active_line_count
                        )
                        wrapper.data_output["guide_average_span"] = guide_average_span = (
                            guide_span / active_line_count
                        )
                    else:
                        wrapper.data_output["guide_average_pixels"] = g_avg_ap = 0
                        wrapper.data_output["guide_average_span"] = guide_average_span = 0
                    if g_avg_ap > 0:
                        guide_solidity = guide_average_span / g_avg_ap
                    else:
                        guide_solidity = 0
                else:
                    guide_average_span = 0
                    guide_solidity = 0

                err_lst = []

                if msk_dt.bottom_index and (msk_dt.bottom_index < msk_height - 60):
                    plant_bottom_error = 3
                    report_lines.append(
                        f"- Plant starts at {msk_height - msk_dt.bottom_index} from image bottom"
                    )
                else:
                    plant_bottom_error = 0
                wrapper.data_output["plant_bottom_error"] = plant_bottom_error
                err_lst.append(plant_bottom_error)

                leaning_error = 0
                # Leaning plant
                first_active_line = msk_dt.lines_data[0]
                if (first_active_line is not None) and (
                    len(first_active_line.nz_pos) >= 1
                ):
                    if (first_active_line.nz_pos[0] <= 10) and (
                        first_active_line.nz_span < mask.shape[1] / 3
                    ):
                        report_lines.append("- Plant seems to lean to the left")
                        leaning_error += 2
                    elif (first_active_line.nz_pos[-1] >= mask.shape[1] - 10) and (
                        first_active_line.nz_span < mask.shape[0] / 3
                    ):
                        report_lines.append("- Plant seems to lean to the right")
                        leaning_error += 2
                    else:
                        pass
                wrapper.data_output["leaning_error"] = leaning_error
                err_lst.append(leaning_error)

                # Horizontal noise
                hrz_error = 0
                last_active_line = msk_dt.lines_data[-1]
                if first_active_line and last_active_line and (len(hlr) > 0):
                    ttl_hlr = len(hlr)
                    plant_hlr = [
                        hlr[i]
                        for i in np.where(
                            np.logical_and(
                                hlr >= first_active_line.height_pos,
                                hlr <= last_active_line.height_pos,
                            )
                        )
                    ][0]
                    wrapper.data_output["hor_lines_removed_hit_plant"] = len(plant_hlr)
                    if len(plant_hlr) != 0:
                        hlr_plant_hit_ratio = (
                            last_active_line.height_pos - first_active_line.height_pos
                        ) / len(plant_hlr)
                        lpx = f"1 line per ({hlr_plant_hit_ratio})"
                        if hlr_plant_hit_ratio > 100:
                            report_lines.append(
                                f"- Horizontal noise: Some noise detected ({lpx}) pixels, "
                                f"please clean sensor"
                            )
                            hrz_error += 1
                        elif hlr_plant_hit_ratio > 40:
                            report_lines.append(
                                f"- Horizontal noise: Noise level critical ({lpx}), please clean sensor"
                            )
                            hrz_error += 2
                        else:
                            if wrapper.hour in ["06", "07", "08"]:
                                report_lines.append(
                                    f"- Horizontal noise: Noise level extreme ({lpx}), "
                                    f"check sensor, check sun position"
                                )
                                hrz_error += 3
                            else:
                                report_lines.append(
                                    f"- Horizontal noise: Noise level extreme ({lpx}), check sensor"
                                )
                                hrz_error += 3
                        rem_hlr = ttl_hlr - len(plant_hlr)
                        if rem_hlr > 0:
                            hrz_error += 1
                            report_lines.append(
                                f"- Horizontal noise: {rem_hlr} detected outside of plant, "
                                f"please clean sensor"
                            )
                    elif ttl_hlr > 0:
                        report_lines.append(
                            f"- Horizontal noise: {ttl_hlr} removed, none crossed the plant, "
                            f"please clean sensor"
                        )
                        hrz_error += 1
                    else:
                        pass
                else:
                    if len(hlr) == 0:
                        pass
                    elif len(hlr) < 10:
                        report_lines.append(
                            f"- Horizontal noise: Some noise detected ({len(hlr)}), please clean sensor"
                        )
                        hrz_error += 1
                    elif len(hlr) < 50:
                        report_lines.append(
                            f"- Horizontal noise: Noise level critical ({len(hlr)}), please clean sensor"
                        )
                        hrz_error += 2
                    else:
                        if wrapper.hour in ["06", "07", "08"]:
                            report_lines.append(
                                f"- Horizontal noise: Noise level extreme ({len(hlr)}), "
                                f"check sensor, check sun position"
                            )
                            hrz_error += 3
                        else:
                            report_lines.append(
                                f"- Horizontal noise: Noise level extreme ({len(hlr)}), check sensor"
                            )
                            hrz_error += 3
                wrapper.data_output["hrz_error"] = hrz_error
                err_lst.append(hrz_error)

                # Moving guide
                guide_error = 0
                if guide_average_span > 6:
                    report_lines.append(
                        f"- Guide width ({guide_average_span:.2f}): guide may have moved during acquisition"
                    )
                    guide_error += 1
                if guide_solidity > 1.1:
                    report_lines.append(
                        f"- Guide solidity ({guide_solidity:.2f}): guide has moved during acquisition"
                    )
                    guide_error += 1
                wrapper.data_output["guide_error"] = guide_error
                err_lst.append(guide_error)

                # Plant top detection
                plant_top_error = 0
                if not isinstance(ept, bool):
                    ept = int(ept)
                    fpt = int(wrapper.data_output.get("final_plant_top_position", 0))
                    if ept:
                        estimation_first_error = abs(pt - ept)
                        real_estimation_error = abs(ept - fpt)
                        if estimation_first_error > 30:
                            report_lines.append(
                                f"- Plant top estimation guess failed by {estimation_first_error} "
                                f"on first step"
                            )
                            plant_top_error += 2
                        if real_estimation_error > 30:
                            report_lines.append(
                                f"- Plant top estimation guess failed by {real_estimation_error} "
                                f"on final output"
                            )
                            plant_top_error += 2
                wrapper.data_output["plant_top_error"] = plant_top_error
                err_lst.append(plant_top_error)

                err_lst = np.array(err_lst)
                if self.get_value_of("binary_error") == 1:
                    error_level = 0 if np.max(err_lst) == 0 else 1
                else:
                    error_level = np.max(err_lst)
                    if error_level >= 2:
                        error_level += len(np.where(err_lst >= 2)[0]) - 1
                wrapper.data_output["error_level"] = error_level
                if report_lines:
                    wrapper.data_output["report"] = " ".join(report_lines).replace(
                        ",", "->"
                    )
                else:
                    wrapper.data_output["report"] = " "

                # Build debug image
                dbg_img = np.dstack((msk_dt.mask, msk_dt.mask, msk_dt.mask))
                # Tag horizontal lines removed
                x_to = dbg_img.shape[1]
                plant_hlr = np.array(
                    [
                        hlr[i]
                        for i in np.where(
                            np.logical_and(
                                hlr >= first_active_line.height_pos,
                                hlr <= last_active_line.height_pos,
                            )
                        )
                    ]
                )
                for line_height in hlr:
                    if line_height in plant_hlr:
                        line_color = ipc.C_RED
                    else:
                        line_color = ipc.C_ORANGE
                    cv2.line(dbg_img, (0, line_height), (10, line_height), line_color, 1)
                    cv2.line(
                        dbg_img,
                        (x_to - 10, line_height),
                        (x_to, line_height),
                        line_color,
                        1,
                    )
                wrapper.store_image(dbg_img, "quality_control_report")

                for k, v in wrapper.data_output.items():
                    self.add_value(key=k, value=v, force_add=True)

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
        return "Heliasen Quality Control"

    @property
    def is_wip(self):
        return True

    @property
    def package(self):
        return "Heliasen"

    @property
    def real_time(self):
        return False

    @property
    def result_name(self):
        "dictionary"

    @property
    def output_kind(self):
        "dictionary"

    @property
    def use_case(self):
        return ["Feature extraction"]

    @property
    def description(self):
        return """Needs vertical and horizontal noise removal before been called.
        Checks light barrier image quality.
        Outputs main error and partial errors."""

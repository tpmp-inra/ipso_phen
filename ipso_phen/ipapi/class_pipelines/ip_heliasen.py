import math

import cv2
import numpy as np

import ipso_phen.ipapi.base.ip_common as ipc
from ipso_phen.ipapi.base.ip_abstract import BaseImageProcessor
from ipso_phen.ipapi.tools.csv_writer import AbstractCsvWriter


class ImageCsvWriter(AbstractCsvWriter):
    def __init__(self):
        super().__init__()
        self.data_list = dict.fromkeys(
            [
                # Header - text values
                "experiment",
                "plant",
                "plant_code",
                "date_time",
                # Morphology
                "area",
                "hull_area",
                "width_data",
                "shape_height",
                "shape_solidity",
                "shape_extend",
                "rotated_bounding_rectangle",
                "minimum_enclosing_circle",
                "quantile_width_4",
                # Metadata
                "error_level",
            ]
        )


class IpHeliasen(BaseImageProcessor):
    @staticmethod
    def can_process(dict_data: dict) -> bool:
        """
        Checks if the class can process the image
        :param dict_data: Dictionary containing filter data
        :return: True if current class can process data
        """
        return dict_data["robot"] == "FileHandlerHeliasen"

    def init_csv_writer(self):
        return ImageCsvWriter()

    def check_source(self):
        res = super(IpHeliasen, self).check_source()
        return res

    def init_csv_data(self, source_image):
        self.csv_data_holder.update_csv_value(
            "plant_code", f"{self.experiment}{self.plant}"
        )

    def init_rois(self):
        self.add_rect_roi(width=-42, height=-245, name="carter", tag="delete")
        self.add_rect_roi(
            left=40, width=135, top=518, height=88, name="safe_zone", tag="safe"
        )
        self.add_rect_roi(height=-20, name="pot", tag="delete")
        self.add_rect_roi(width=-136, height=-33, name="hose", tag="delete")
        self.add_rect_roi(
            left=40, width=60, top=550, height=60, name="enforcer", tag="enforce"
        )
        # self.add_rect_roi(left=0, width=224, top=0, height=589, name='remove_hat', tag='keep_after')

    def clean_horizontal_line_noise_v2(self, src):
        nz_pixels = np.count_nonzero(src)
        lr_res = self.remove_hor_noise_lines(mask=src, min_line_size=11, max_iter=100)
        lines_removed_ = list(set([line[0][0] for line in lr_res["lines"]]))
        self.data_output["hor_lines_removed"] += np.array(lines_removed_)
        self.data_output["hor_pixels_removed"] = nz_pixels - np.count_nonzero(src)
        self.data_output["hor_lines_removed_hit_plant"] = 0

        return lr_res["mask"]

    def clean_horizontal_line_noise(
        self, src, min_angle: float, max_angle: float, threshold: int = 50
    ):
        stable_ = False
        iter_count_ = 0
        all_lines_img = np.dstack((src, src, src))
        lines_removed_ = []
        nz_pixels = np.count_nonzero(src)
        while not stable_ and (iter_count_ < 100):
            stable_ = True
            iter_count_ += 1
            edges = cv2.Canny(src, 0, 255)
            self.store_image(edges, f"edges iter {iter_count_}")
            lines = cv2.HoughLines(edges, rho=1, theta=np.pi / 180, threshold=threshold)
            if lines is not None:
                erosion_mask = np.zeros_like(src)
                kernel = np.ones((5, 1))
                lines_img = np.dstack((src, src, src))
                l, r = 0, src.shape[1]
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
                        x1, y1 = self.constraint_to_image(x1, y1, src)
                        x2, y2 = self.constraint_to_image(x2, y2, src)
                        if not (min_angle < abs(theta) < max_angle):
                            cv2.line(lines_img, (x1, y1), (x2, y2), ipc.C_RED, 2)
                            continue
                        stable_ = False
                        if max(y1, y2) < src.shape[0] - 10:
                            lines_removed_.append(y1)
                        cv2.line(lines_img, (x1, y1), (x2, y2), ipc.C_BLUE, 2)
                        cv2.line(all_lines_img, (x1, y1), (x2, y2), ipc.C_BLUE, 1)
                        if min(y1, y2) <= 4:
                            src[min(y1, y2) : max(y1, y2) + 1, l:r] = 0
                        else:
                            t, b = min(y1, y2) - 2, max(y1, y2) + 2
                            erosion_mask[t:b, l:r] = src[t:b, l:r]
                c_minus = self.multi_and((255 - erosion_mask, src))
                self.store_image(lines_img, f"horizontal_lines iter {iter_count_}")
                self.store_image(
                    erosion_mask, f"horizontal_erosion_target iter {iter_count_}"
                )
                self.store_image(
                    c_minus, f"horizontal_mask_minus_erosion iter {iter_count_}"
                )
                erosion_mask = cv2.morphologyEx(erosion_mask, cv2.MORPH_OPEN, kernel)
                self.store_image(
                    erosion_mask, f"horizontal_erosion_result iter {iter_count_}"
                )
                src = self.multi_or((c_minus, erosion_mask))
                self.store_image(src, f"horizontal_mask iter {iter_count_}")
            else:
                break
        self.data_output["hor_lines_removed"] += np.array(lines_removed_)
        self.data_output["hor_pixels_removed"] = nz_pixels - np.count_nonzero(src)
        self.data_output["hor_lines_removed_hit_plant"] = 0
        self.store_image(all_lines_img, "horizontal_all_eroded_lines")
        return src

    def clean_vertical_line_noise(
        self,
        src,
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
            self.store_image(edges, f"vertical_edges iter {iter_count_}")
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
                self.store_image(lines_img, f"vertical_lines iter {iter_count_}")
                self.store_image(src, f"vertical_mask iter {iter_count_}")
            else:
                break
        self.data_output["vert_lines_removed"] = lines_removed_
        self.data_output["vert_pixels_removed"] = nz_pixels - np.count_nonzero(src)
        self.store_image(all_lines_img, "vertical_all_deleted_lines")
        return src

    def build_channel_mask(self, source_image, **kwargs):
        try:
            channel = self.get_channel(source_image, "l")
            channel = self.apply_rois(channel)
            self.store_image(channel, "source_carter_removed")

            # Remove horizontal noise
            if kwargs.get("horizontal_cleaning_method", "in_house") == "hough":
                channel = self.clean_horizontal_line_noise(
                    channel,
                    np.pi / 2 - (np.pi / 2 * 0.01),
                    np.pi / 2 + (np.pi / 2 * 0.01),
                    threshold=60,
                )
            else:
                channel = self.clean_horizontal_line_noise_v2(channel)
            self.store_image(
                channel, "mask_after_horizontal_noise_removal", force_store=True
            )

            # Define search parameters
            delete_too_narrow_ = 8
            keep_and_stop_too_wide_ = 60
            investigate_lower_bound_ = 16
            investigate_upper_bound_ = 40

            # Find top of plant and detect guide presence
            stop_checking_ = False
            plant_top_idx = -1
            guide_found_ = False
            for line_number, line in enumerate(channel):
                # Build line data
                cur_ln_dt = ipc.MaskLineData(line_number, line, 0)
                # At some point we have to admit that there is no guide
                if not guide_found_ and (line_number > 200):
                    self.data_output["expected_plant_top_position"] = False
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
                    self.data_output["expected_plant_top_position"] = plant_top_idx
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
                plant_top_img = np.dstack((channel, channel, channel))
                cv2.line(
                    plant_top_img,
                    (0, plant_top_idx),
                    (channel.shape[1], plant_top_idx),
                    ipc.C_BLUE,
                    2,
                )
                self.store_image(plant_top_img, "plant_top")
                channel = self.clean_vertical_line_noise(
                    src=channel,
                    min_angle=np.pi / 2 - (np.pi / 2 * 0.05),
                    max_angle=np.pi / 2 + (np.pi / 2 * 0.05),
                    min_height=plant_top_idx,
                    threshold=80,
                    min_line_size=30,
                    max_line_gap=0,
                )
                self.store_image(channel, "mask_after_vertical_noise_removal")

            # Apply remaining ROIs
            self.add_rect_roi(0, 220, -1, 12, "pot", "delete")
            self.add_rect_roi(144, 40, 606, 26, "tubes", "delete")
            channel = self.apply_rois(channel)

            # Remove vertical noise
            stop_checking_ = False
            guide_found_ = False
            line_data = []
            last_span_ = 0
            for line_number, line in enumerate(channel):
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

            lines_img = np.dstack((channel, channel, channel))
            vt_fixed = np.zeros_like(channel)
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
            self.data_output["plant_top_position"] = top_of_plant

            self.store_image(lines_img, "lines_tagged")

            mask = vt_fixed

        except Exception as e:
            self.error_holder.add_error(
                f'Failed to build channel mask because "{repr(e)}"'
            )
            return False
        else:
            self.mask = mask
            self.store_image(self.mask, "channel_mask")
            if self.mask is None:
                return False
            else:
                return np.count_nonzero(self.mask) > 0

    def clean_mask(self, source_image):
        try:
            if (self.mask is None) or (np.count_nonzero(self.mask) <= 0):
                return False

            self.add_rect_roi(88, 96, -1, 34, "tubes_2", "clean_erode")
            mask = self.keep_linked_contours(
                src_mask=self.erode(
                    self.mask, kernel_size=5, rois=self.get_rois({"clean_erode"})
                ),
                dilation_iter=-1,
                tolerance_distance=2,
                tolerance_area=50,
                root_position="BOTTOM_LEFT",
            )
            # mask = self.keep_roi(mask, 'remove_hat')
            self.store_image(mask, "mask")
        except Exception as e:
            self.error_holder.add_error(f'Failed to clean mask because "{repr(e)}"')
            return False
        else:
            self.store_image(mask, "mask")
            self.mask = mask
            if self.mask is None:
                return False
            else:
                return np.count_nonzero(self.mask) > 0

    def ensure_mask_zone(self):
        mask = self.mask
        mask = self.keep_roi(mask, "enforcer")
        return np.count_nonzero(mask) > 0

    def build_mosaic_data(self, **kwargs):
        if self.store_mosaic.lower() == "debug":
            self._mosaic_data = np.array(
                ["source", "plant_top", "quality_control_report", "mask"]
            )
        else:
            self._mosaic_data = np.array(
                ["source", "img_wth_tagged_cnt", "mask", "shapes"]
            )
        return True

    def finalize_process(self, **kwargs):
        res = False
        try:
            # Init
            mask = self.mask

            ept = self.data_output.get("expected_plant_top_position", False)
            pt = int(self.data_output.get("plant_top_position", 0))
            hlr = self.data_output.get("hor_lines_removed", [])
            hlr = [hlr[i] for i in np.where(hlr <= self.height - 12)][0]
            self.data_output["hor_lines_removed"] = len(hlr)

            report_lines = []
            guide_pixels = 0
            guide_span = 0
            last_span_ = 0

            # Initialise mask data
            msk_dt = ipc.MaskData(mask=mask)

            if msk_dt.height == 0:
                self.data_output["guide_only_pixels"] = "-"
                self.data_output["guide_average_width"] = "-"
                return False

            mask_after_horizontal_noise_removal, *_ = cv2.split(
                self.retrieve_stored_image("mask_after_horizontal_noise_removal")
            )
            msk_height = mask_after_horizontal_noise_removal.shape[0]
            self.data_output["final_plant_top_position"] = msk_dt.top_index
            if msk_dt.top_index and not isinstance(ept, bool):
                line_stop = min(min(msk_dt.top_index, int(ept)), pt)
                active_line_count = 0
                for l_n, line in enumerate(mask_after_horizontal_noise_removal):
                    if l_n >= line_stop:
                        break
                    cur_ln_dt = ipc.MaskLineData(l_n, line, last_span_)
                    guide_pixels += cur_ln_dt.nz_count
                    guide_span += cur_ln_dt.nz_span
                    if cur_ln_dt.nz_span > 0:
                        active_line_count += 1
                self.data_output["guide_only_pixels"] = guide_pixels
                if active_line_count > 0:
                    self.data_output["guide_average_pixels"] = g_avg_ap = (
                        guide_pixels / active_line_count
                    )
                    self.data_output["guide_average_span"] = guide_average_span = (
                        guide_span / active_line_count
                    )
                else:
                    self.data_output["guide_average_pixels"] = g_avg_ap = 0
                    self.data_output["guide_average_span"] = guide_average_span = 0
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
            self.data_output["plant_bottom_error"] = plant_bottom_error
            err_lst.append(plant_bottom_error)

            leaning_error = 0
            # Leaning plant
            first_active_line = msk_dt.lines_data[0]
            if (first_active_line is not None) and (len(first_active_line.nz_pos) >= 1):
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
            self.data_output["leaning_error"] = leaning_error
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
                self.data_output["hor_lines_removed_hit_plant"] = len(plant_hlr)
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
                        if self.hour in ["06", "07", "08"]:
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
                    if self.hour in ["06", "07", "08"]:
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
            self.data_output["hrz_error"] = hrz_error
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
            self.data_output["guide_error"] = guide_error
            err_lst.append(guide_error)

            # Plant top detection
            plant_top_error = 0
            if not isinstance(ept, bool):
                ept = int(ept)
                fpt = int(self.data_output.get("final_plant_top_position", 0))
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
            self.data_output["plant_top_error"] = plant_top_error
            err_lst.append(plant_top_error)

            err_lst = np.array(err_lst)
            error_level = np.max(err_lst)
            if error_level >= 2:
                error_level += len(np.where(err_lst >= 2)[0]) - 1
            self.data_output["error_level"] = error_level
            self.csv_data_holder.update_csv_value("error_level", error_level)
            self.data_output["report"] = "\n".join(report_lines)

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
            self.store_image(dbg_img, "quality_control_report")

        except Exception as e:
            self.data_output["report"] = f'Failed to build report "{str(e)}'
            res = False
        else:
            res = True
        finally:
            return res

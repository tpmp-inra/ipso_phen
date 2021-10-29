import os

import numpy as np
import cv2

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
                "plant_id",
                "date_time",
                "angle",
                "series_id",
                "acquisition_note",
                # Morphology
                "area",
                "hull_area",
                "width_data",
                "shape_height",
                "shape_solidity",
                "shape_extend",
                "rotated_bounding_rectangle",
                "minimum_enclosing_circle",
                # Color descriptors
                "color_std_dev",
                "color_mean",
                # Image properties
                "image_width",
                "image_height",
                "scale_width",
            ]
        )


class Ip013s1801sym(BaseImageProcessor):
    @staticmethod
    def init_csv_writer():
        return ImageCsvWriter()

    @staticmethod
    def can_process(dict_data: dict) -> bool:
        """Checks if the class can process the image

        :param dict_data: Dictionary containing filter data
        :return: True if current class can process data
        """
        return dict_data["experiment"] in ["013s1801_sym"]

    def init_csv_data(self, source_image):
        self.csv_data_holder.update_csv_dimensions(source_image, self.scale_width)

        [_, _, plant_id_] = self.plant.split("_")
        self.csv_data_holder.update_csv_value("plant_id", plant_id_)

        if self.is_between_dates("2018_02_01", "2018_02_02"):
            self.csv_data_holder.update_csv_value("acquisition_note", "checkered")
        elif self.is_between_dates("2018_02_02", "2018_02_06"):
            self.csv_data_holder.update_csv_value("acquisition_note", "wide_angle")
        elif self.is_between_dates("2018_02_06", "2018_02_07"):
            self.csv_data_holder.update_csv_value(
                "acquisition_note", "wide_angle_overexposed"
            )
        elif self.is_between_dates("2018_02_07", "2018_02_28"):
            self.csv_data_holder.update_csv_value("acquisition_note", "bad_white_balance")
        elif self.is_between_dates("2018_02_28", "2018_03_20"):
            self.csv_data_holder.update_csv_value(
                "acquisition_note", "bad_white_balance_cage"
            )
        elif self.is_between_dates("2018_03_20", "2018_03_23"):
            self.csv_data_holder.update_csv_value("acquisition_note", "cage")
        elif self.is_between_dates("2018_03_23", "2018_04_09", include_end=True):
            self.csv_data_holder.update_csv_value(
                "acquisition_note", "blue_background_cage"
            )

        return True

    def _fix_source_image(self):
        if self.is_vis:
            if self.is_blue_background:
                fwb_img = self.simplest_cb(self.current_image, (0, 2))
            elif self.is_blue_guide:
                if self.is_before_date(year="2018", month="03", day="20"):
                    fwb_img = self.simplest_cb(self.current_image, (20, 40))
                else:
                    fwb_img = self.simplest_cb(self.current_image, (5, 20))
            else:
                if self.is_no_wb_fix:
                    fwb_img = self.current_image
                else:
                    fwb_img = self.simplest_cb(self.current_image, [20, 40])
            self.store_image(fwb_img, "fixed_img", self.rois_list)
            return fwb_img
        elif self.is_nir:
            return self.current_image
        elif self.is_fluo:
            return self.current_image
        else:
            return None

    def init_rois(self):
        if self.is_blue_background:
            self.add_rect_roi(28, 1998, 20, 1290, "main_roi", "keep")
            self.add_rect_roi(1688, 338, 20, 290, "roi_cable", "erode")
            self.add_rect_roi(0, 112, 4, 2438, "roi_bar_left", "erode")
            self.add_rect_roi(1941, 80, 4, 2438, "roi_bar_right", "erode")
            self.add_rect_roi(236, 1416, 42, 1222, "safe_left_top", "safe")
            self.add_rect_roi(706, 662, 1278, 64, "pot_top", "erode")
            self.add_rect_roi(1550, 256, 372, 892, "safe_right_middle", "safe")
        elif self.is_blue_guide:
            self.add_rect_roi(28, 1998, 20, 1290, "main_roi", "keep")
            self.add_rect_roi(1688, 338, 20, 290, "roi_cable", "erode")
            self.add_rect_roi(0, 190, 4, 2438, "roi_bar_left", "erode")
            self.add_rect_roi(1839, 190, 4, 2438, "roi_bar_right", "erode")
            self.add_rect_roi(236, 1416, 42, 1222, "safe_left_top", "safe")
            self.add_rect_roi(706, 662, 1278, 64, "pot_top", "erode")
            self.add_rect_roi(1550, 256, 372, 892, "safe_right_middle", "safe")
        else:
            self.init_standard_rois()

    def build_channel_mask(self, source_image, **kwargs):
        try:
            if self.is_blue_background:
                params_dict = [
                    dict(
                        channel="h", min_t=10, max_t=90, morph_op="close", kernel_size=3
                    ),
                    dict(
                        channel="b",
                        min_t=130,
                        max_t=165,
                        morph_op="close",
                        kernel_size=3,
                    ),
                ]
                self.mask = self.build_mask(
                    source_image,
                    **dict(
                        is_store_images=True,
                        merge_action="multi_and",
                        params_list=params_dict,
                    ),
                )
            elif self.is_blue_guide:
                if self.is_before_date(year="2018", month="03", day="20"):
                    params_dict = [
                        dict(
                            channel="h",
                            min_t=10,
                            max_t=60,
                            morph_op="close",
                            kernel_size=3,
                        ),
                        dict(
                            channel="l",
                            min_t=5,
                            max_t=150,
                            morph_op="close",
                            kernel_size=3,
                        ),
                        dict(
                            channel="b",
                            min_t=130,
                            max_t=170,
                            median_filter_size=3,
                            morph_op="close",
                            kernel_size=3,
                        ),
                    ]
                else:
                    params_dict = [
                        dict(channel="h", min_t=5, max_t=65),
                        dict(
                            channel="v",
                            min_t=15,
                            max_t=180,
                            morph_op="close",
                            kernel_size=3,
                        ),
                        dict(channel="l", min_t=10, max_t=165),
                        dict(
                            channel="b",
                            min_t=130,
                            max_t=165,
                            median_filter_size=3,
                            morph_op="close",
                            kernel_size=3,
                        ),
                    ]
                self.mask = self.build_mask(
                    source_image,
                    **dict(
                        is_store_images=True,
                        merge_action="multi_and",
                        params_list=params_dict,
                    ),
                )
            else:
                mask_b, stored_name = self.get_mask(
                    source_image, "b", 135, 255, self.rois_list, False, 7
                )
                self.store_image(mask_b, stored_name, self.rois_list)
                mask_s, stored_name = self.get_mask(
                    source_image, "s", 30, 255, self.rois_list, False, 5
                )
                self.store_image(mask_s, stored_name, self.rois_list)
                self.mask = cv2.bitwise_and(mask_b, mask_s)

            self.store_image(self.mask, "channel_mask", self.rois_list)
        except Exception as e:
            self.error_holder.add_error(
                f'Failed to build channel mask because "{repr(e)}"'
            )
            return False
        else:
            if self.mask is None:
                return False
            else:
                return np.count_nonzero(self.mask) > 0

    def clean_mask(self, source_image):
        try:
            # Apply erosion to selected zones
            mask = self.erode(
                self.mask, 7, cv2.MORPH_ELLIPSE, self.get_rois({"erode"}), "ellipse"
            )
            self.store_image(mask, "mask_eroded", self.rois_list)
            if self.is_blue_background:
                self.store_image(mask, "mask_before_keep")
            elif self.is_blue_guide:
                self.store_image(mask, "mask_before_keep")
            else:
                # Create safe zone mask and apply it to safe zone
                mask_s, stored_name = self.get_mask(
                    source_image, "s", 30, 255, self.rois_list, False, 5
                )
                self.store_image(mask_s, stored_name, self.rois_list)
                mask_s = self.keep_rois(mask_s, ["safe"])
                self.store_image(mask_s, "mask_s_safe_only", self.rois_list)
                mask = self.multi_or([mask, mask_s])
                self.store_image(mask, "mask_before_keep")

            if np.count_nonzero(mask) <= 0:
                return False
            mask = self.keep_linked_contours(
                src_image=source_image,
                src_mask=mask,
                dilation_iter=10,
                tolerance_distance=67,
                tolerance_area=1003,
            )

            self.store_image(mask, "mask")
            self.mask = mask
        except Exception as e:
            self.error_holder.add_error(f'Failed to clean mask because "{repr(e)}"')
            return False
        else:
            if self.mask is None:
                return False
            else:
                return np.count_nonzero(self.mask) > 0

    def build_mosaic_data(self, **kwargs):
        if self.store_mosaic.lower() == "debug":
            self._mosaic_data = np.array(["source", "mask_before_keep", "mask"])
        return True

    @property
    def is_corrupted(self):
        return not os.path.isfile(self.file_path) or self.is_before_date(
            year="2018", month="02", day="02"
        )

import os

import numpy as np

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
                "geno",
                "treatment",
                "substratum",
                "plant_id" "date_time",
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
            ]
        )


class Ip013c2307mar(BaseImageProcessor):
    @staticmethod
    def init_csv_writer():
        return ImageCsvWriter()

    @staticmethod
    def can_process(dict_data: dict) -> bool:
        """
        Checks if the class can process the image
        :param dict_data: Dictionary containing filter data
        :return: True if current class can process data
        """
        return dict_data["experiment"] in ["013c2307mar"]

    def init_csv_data(self, source_image):
        self.csv_data_holder.update_csv_dimensions(source_image, self.scale_width)

        if "stress" in self.plant:
            [
                geno_,
                treatment_1_,
                treatment_2_,
                substratum_,
                plant_id_,
            ] = self.plant.split("_")
            self.csv_data_holder.update_csv_value("geno", geno_)
            self.csv_data_holder.update_csv_value(
                "treatment", f"{treatment_1_}_{treatment_2_}"
            )
            self.csv_data_holder.update_csv_value("substratum", substratum_)
            self.csv_data_holder.update_csv_value("plant_id", plant_id_)
        else:
            [geno_, treatment_, substratum_, plant_id_] = self.plant.split("_")
            self.csv_data_holder.update_csv_value("geno", geno_)
            self.csv_data_holder.update_csv_value("treatment", treatment_)
            self.csv_data_holder.update_csv_value("substratum", substratum_)
            self.csv_data_holder.update_csv_value("plant_id", plant_id_)

        return True

    def init_rois(self):
        if self.is_msp:
            main_roi_radius = 1180 / 2
            x, y = 696, 435
        elif self.is_cf_calc:
            main_roi_radius = 238 / 2
            x, y = 172, 108
        else:
            self.error_holder.add_error("Failed to init ROIs , unknown camera")
            return
        self.add_circle_roi(
            int(x + main_roi_radius),
            int(y + main_roi_radius),
            int(main_roi_radius),
            "main_roi",
            "keep",
        )

    def build_channel_mask(self, source_image, **kwargs):
        try:
            if self.is_msp:
                if "feutre" in self.plant:
                    params_dict = [
                        dict(
                            channel="h",
                            min_t=10,
                            max_t=70,
                            morph_op="open",
                            kernel_size=7,
                            median_filter_size=3,
                        ),
                        dict(
                            channel="s",
                            min_t=30,
                            max_t=165,
                            morph_op="open",
                            kernel_size=5,
                        ),
                        dict(
                            channel="b",
                            min_t=130,
                            max_t=170,
                            morph_op="open",
                            kernel_size=9,
                        ),
                    ]
                elif "papier" in self.plant:
                    params_dict = [
                        dict(
                            channel="h",
                            min_t=10,
                            max_t=80,
                            morph_op="open",
                            kernel_size=5,
                        ),
                        dict(
                            channel="b",
                            min_t=135,
                            max_t=160,
                            morph_op="open",
                            kernel_size=3,
                        ),
                    ]
                elif "sable" in self.plant:
                    params_dict = [
                        dict(
                            channel="h",
                            min_t=5,
                            max_t=100,
                            morph_op="open",
                            kernel_size=7,
                            median_filter_size=3,
                        ),
                        dict(
                            channel="b",
                            min_t=130,
                            max_t=175,
                            morph_op="open",
                            kernel_size=9,
                            median_filter_size=5,
                        ),
                    ]
                else:
                    self.error_holder.add_error(
                        "Failed to build channel mask, unknown substratum"
                    )
                    return False
            elif self.is_cf_calc:
                params_dict = [
                    dict(
                        channel="v",
                        min_t=195,
                        morph_op="open",
                        kernel_size=3,
                        median_filter_size=3,
                    )
                ]
            else:
                self.error_holder.add_error(
                    "Failed to build channel mask, unknown camera"
                )
                return False

            mask = self.build_mask(
                source_image,
                **dict(
                    is_store_images=True,
                    merge_action="multi_and",
                    params_list=params_dict,
                ),
            )

            if self.is_msp and ("papier" in self.plant):
                mask = self.dilate(mask, 3, proc_times=4)

            self.store_image(mask, "channel_mask")
        except Exception as e:
            self.error_holder.add_error(
                f'Failed to build channel mask because "{repr(e)}"'
            )
            return False
        else:
            self.mask = mask
            if self.mask is None:
                return False
            else:
                return np.count_nonzero(self.mask) > 0

    def crop_mask(self):
        mask = self.mask
        mask = self.keep_rois(mask, ["keep"])
        self.store_image(mask, "mask_s_safe_only")
        self.mask = mask
        return True

    def clean_mask(self, source_image):
        try:
            mask = self.mask
            if (self.mask is None) or (np.count_nonzero(mask) <= 0):
                return False
            if self.is_msp:
                if "sable" in self.plant:
                    mask = self.keep_linked_contours(
                        src_image=source_image,
                        src_mask=mask,
                        tolerance_distance=64,
                        tolerance_area=11000,
                        root_position="MIDDLE_CENTER",
                    )
                else:
                    mask = self.keep_linked_contours(
                        src_image=source_image,
                        src_mask=mask,
                        tolerance_distance=100,
                        tolerance_area=11000,
                        root_position="MIDDLE_CENTER",
                    )
            elif self.is_cf_calc:
                mask = self.keep_linked_contours(
                    src_image=source_image,
                    src_mask=mask,
                    tolerance_distance=70,
                    tolerance_area=1200,
                    root_position="MIDDLE_CENTER",
                )
            else:
                self.error_holder.add_error(
                    "Failed to build channel mask for, unknown camera"
                )
                return False

            self.store_image(mask, "mask")
        except Exception as e:
            self.error_holder.add_error(f'Failed to clean mask because "{repr(e)}"')
            return False
        else:
            self.mask = mask
            if self.mask is None:
                return False
            else:
                return np.count_nonzero(self.mask) > 0

    def build_mosaic_data(self, **kwargs):
        if self.store_mosaic.lower() == "debug":
            self._mosaic_data = np.array(
                [
                    ["source", "src_img_with_cnt_after_agg_iter_last"],
                    ["mask", "pseudo_on"],
                ]
            )
        return True

    @property
    def is_corrupted(self):
        return not os.path.isfile(self.file_path) or self.is_before_date(
            year="2018", month="02", day="02"
        )

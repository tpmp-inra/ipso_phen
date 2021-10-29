import numpy as np

from ipso_phen.ipapi.base.ip_abstract import BaseImageProcessor
from ipso_phen.ipapi.tools.csv_writer import AbstractCsvWriter


class ImageFluoCsvWriter(AbstractCsvWriter):
    def __init__(self):
        super().__init__()
        self.data_list = dict.fromkeys(
            [
                # Header - text values
                "experiment",
                "plant",
                "plant_id",
                "treatment",
                "date_time",
                "hist_bins",
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


class ImageMpsCsvWriter(AbstractCsvWriter):
    def __init__(self):
        super().__init__()
        self.data_list = dict.fromkeys(
            [
                # Header - text values
                "experiment",
                "plant",
                "plant_id",
                "treatment",
                "date_time",
                "hist_bins",
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


class Ip0102405ggt(BaseImageProcessor):
    def init_csv_writer(self):
        if "fluo" in self.camera:
            return ImageFluoCsvWriter()
        else:
            return ImageMpsCsvWriter()

    @staticmethod
    def can_process(dict_data: dict) -> bool:
        """
        Checks if the class can process the image
        :param dict_data: Dictionary containing filter data
        :return: True if current class can process data
        """
        return dict_data["experiment"] in ["0102405_ggt"]

    def check_source(self):
        if self.is_corrupted:
            self.error_holder.add_error(
                "HANDLED FAILURE Image has been tagged as corrupted",
                new_error_kind="source_issue",
            )
            return False

        if self.is_color_checker:
            self.error_holder.add_error("HANDLED FAILURE Image is color checker")
            return False

        # if not self.is_good_batch:
        #     self.error_holder.add_error('HANDLED FAILURE Image some images are missing', new_error_kind='source_issue')
        #     return False

        return True

    def init_csv_data(self, source_image):
        [treatment_1, treatment_2, plant_id_] = self.plant.split("_")
        self.csv_data_holder.update_csv_value("plant_id", plant_id_)
        self.csv_data_holder.update_csv_value("treatment", f"{treatment_1}_{treatment_2}")

    def init_rois(self):
        if self.is_cf_calc:
            main_roi_radius = 404 / 2
            self.add_circle_roi(
                int(118 + main_roi_radius),
                int(24 + main_roi_radius),
                int(main_roi_radius),
                "main_roi",
                "keep",
            )

        else:
            main_roi_radius = 2012 / 2
            self.add_circle_roi(
                int(246 + main_roi_radius),
                int(20 + main_roi_radius),
                int(main_roi_radius),
                "main_roi",
                "keep",
            )

    def build_channel_mask(self, source_image, **kwargs):
        try:
            if self.is_cf_calc:
                params_dict = [
                    dict(channel="v", min_t=50),
                    dict(channel="bl", min_t=50),
                ]
                op = "multi_or"
            else:
                params_dict = [
                    dict(channel="h", min_t=15, max_t=80, median_filter_size=5),
                    dict(channel="s", min_t=15, max_t=120, median_filter_size=5),
                    dict(channel="a", min_t=105, max_t=130, median_filter_size=5),
                    dict(channel="b", min_t=125, max_t=170, median_filter_size=5),
                ]
                op = "multi_and"

            mask = self.build_mask(
                source_image,
                **dict(is_store_images=True, merge_action=op, params_list=params_dict),
            )

        except Exception as e:
            self.error_holder.add_error(
                f'Failed to build channel mask because "{repr(e)}"'
            )
            return False
        else:
            self.mask = mask
            self.store_image(self.mask, "channel_mask", self.rois_list)
            if self.mask is None:
                return False
            else:
                return np.count_nonzero(self.mask) > 0

    def clean_mask(self, source_image):
        try:
            if self.is_cf_calc:
                mask = self.keep_linked_contours(
                    src_image=source_image,
                    src_mask=self.mask,
                    root_position="MIDDLE_CENTER",
                )
            else:
                mask = self.open(self.mask, 5)
                self.store_image(mask, "mask_open", rois=self.rois_list)

                mask = self.keep_linked_contours(
                    src_image=source_image,
                    src_mask=mask,
                    tolerance_area=5000,
                    root_position="MIDDLE_CENTER",
                )
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

    def build_mosaic_data(self, **kwargs):
        return True

    @property
    def is_good_batch(self):
        return self.is_cf_calc or (
            self.is_after_date(year="2018", month="06", day="06")
            and self.is_before_date(year="2018", month="06", day="13")
        )

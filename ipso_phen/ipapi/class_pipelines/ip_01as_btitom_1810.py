import numpy as np

from ipso_phen.ipapi.base.ip_abstract import BaseImageProcessor
from ipso_phen.ipapi.tools.csv_writer import AbstractCsvWriter

_01a_EXPERIMENT = "01as_btitom_1810".lower()


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
                # Chlorophyll data
                "chlorophyll_mean",
                "chlorophyll_std_dev",
            ]
        )


class Ip01asBtiTom1810(BaseImageProcessor):
    @staticmethod
    def can_process(dict_data: dict) -> bool:
        """
        Checks if the class can process the image
        :param dict_data: Dictionary containing filter data
        :return: True if current class can process data
        """
        return dict_data["experiment"] in [_01a_EXPERIMENT]

    def init_csv_writer(self):
        return ImageCsvWriter()

    def check_source(self):
        res = super(Ip01asBtiTom1810, self).check_source()
        if res:
            res = not self.is_empty_conveyor
            if not res:
                self.error_holder.add_error(
                    "Conveyor is empty", new_error_kind="source_issue"
                )
        return res

    def init_csv_data(self, source_image):
        plant_, *_ = self.plant.split("_")
        _, id_ = plant_.split("a")
        self.csv_data_holder.update_csv_value("plant_id", id_)

    def init_rois(self):
        self.add_rect_roi(0, 2050, 0, 2448, "main_roi", "keep")
        self.add_rect_roi(126, 1734, 244, 1776, "safe_zone", "safe")
        self.add_rect_roi(0, 2050, 2048, 108, "middle_zone", "erode")
        self.add_rect_roi(0, 2050, 2156, 292, "bottom_zone", "erode")

    def build_channel_mask(self, source_image, **kwargs):
        try:
            mask_top, _ = self.get_mask(source_image, "b", min_t=120)

            op = "multi_and"
            params_dict = [
                dict(channel="h", min_t=15, max_t=105, morph_op="erode", kernel_size=3),
                dict(channel="b", min_t=120, morph_op="erode", kernel_size=3),
                dict(channel="bl", max_t=95, morph_op="erode", kernel_size=3),
                dict(channel="rd", min_t=20, morph_op="erode", kernel_size=3),
            ]
            mask_middle = self.build_mask(
                source_image,
                **dict(is_store_images=True, merge_action=op, params_list=params_dict),
            )

            mask_bottom = self.erode(
                mask_middle, rois=self.get_rois({"erode"}), proc_times=2
            )
            self.store_image(mask_bottom, "mask_bottom", self.rois_list)

            mask_top = self.delete_roi(mask_top, "middle_zone")
            mask_top = self.delete_roi(mask_top, "bottom_zone")
            self.store_image(mask_top, "mask_top", self.rois_list)
            mask_middle = self.keep_roi(mask_middle, "middle_zone")
            self.store_image(mask_middle, "mask_middle", self.rois_list)
            mask_bottom = self.keep_roi(mask_bottom, "bottom_zone")
            self.store_image(mask_bottom, "mask_bottom", self.rois_list)

            mask = self.multi_or((mask_top, mask_middle, mask_bottom))
            self.store_image(mask, "last_built_mask", self.rois_list)
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
            mask = self.mask
            if (self.mask is None) or (np.count_nonzero(mask) <= 0):
                return False
            mask = self.keep_linked_contours(
                src_image=source_image,
                src_mask=mask,
                tolerance_distance=64,
                tolerance_area=50,
                root_position="BOTTOM_CENTER",
            )

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
        mask = self.keep_roi(mask, "safe_zone")
        return np.count_nonzero(mask) > 0

    def build_mosaic_data(self, **kwargs):
        if self.store_mosaic.lower() == "debug":
            self._mosaic_data = np.array(["source", "img_wth_tagged_cnt", "pseudo_on"])
        return True

    @property
    def is_empty_pot(self):
        return self.plant in [
            "001a0022_la_xx_xx",
            "001a0053_la_xx_xx",
            "001a0065_la_xx_xx",
            "001a0067_la_xx_xx",
        ]

    @property
    def is_empty_conveyor(self):
        return self.is_after_date_time(
            year="2018", month="10", day="26", hour="10", minute="00", second="00"
        )

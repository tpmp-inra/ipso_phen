import numpy as np

from ipso_phen.ipapi.base.ip_abstract import BaseImageProcessor
from ipso_phen.ipapi.tools.csv_writer import AbstractCsvWriter


class ImageShortCsvWriter(AbstractCsvWriter):
    def __init__(self):
        super().__init__()
        self.data_list = dict.fromkeys(
            [
                # Header - text values
                "experiment",
                "plant",
                "plant_id",
                "plant_suffix",
                "date_time",
                "view_option",
                "series_id",
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


class ImageLongCsvWriter(AbstractCsvWriter):
    def __init__(self):
        super().__init__()
        self.data_list = dict.fromkeys(
            [
                # Header - text values
                "experiment",
                "plant",
                "plant_id",
                "genotype",
                "watering",
                "myc",
                "date_time",
                "view_option",
                "series_id",
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


class IpBrachySymStd(BaseImageProcessor):
    @staticmethod
    def can_process(dict_data: dict) -> bool:
        """
        Checks if the class can process the image
        :param dict_data: Dictionary containing filter data
        :return: True if current class can process data
        """
        return dict_data["experiment"] in [
            "022s1806_sym",
            "018s1804_sym",
            "024s1809_sym",
        ]

    def init_csv_writer(self):
        if self.experiment in ["022s1806_sym", "018s1804_sym"]:
            return ImageShortCsvWriter()
        elif self.experiment == "024s1809_sym":
            return ImageLongCsvWriter()
        else:
            self.error_holder.add_error("Unknown CSV writer")
            return AbstractCsvWriter()

    def check_source(self):
        res = super(IpBrachySymStd, self).check_source()
        return res

    def init_csv_data(self, source_image):
        if self.experiment in ["022s1806_sym", "018s1804_sym"]:
            [_, _, plant_id_, plant_suffix] = self.plant.split("_")
            self.csv_data_holder.update_csv_value("plant_id", plant_id_)
            self.csv_data_holder.update_csv_value("plant_suffix", plant_suffix)
        else:
            _, _, id_, *genotype_, watering_, myc_ = self.plant.split("_")
            self.csv_data_holder.update_csv_value("plant_id", id_)
            self.csv_data_holder.update_csv_value("genotype", "_".join(genotype_))
            self.csv_data_holder.update_csv_value("watering", watering_)
            self.csv_data_holder.update_csv_value("myc", myc_)

    def init_rois(self):
        self.add_rect_roi(90, 1900, 300, 1740, "main_roi", "keep")
        self.add_rect_roi(230, 1550, 350, 1546, "safe_zone", "safe")

    def build_channel_mask(self, source_image, **kwargs):
        try:
            mask_data = self.prepare_masks_data_dict(
                (
                    ("h", 10, 100, 3),
                    ("s", 25, 160, 3),
                    ("l", 5, 145, 3),
                    ("b", 115, 160, 3),
                    ("bl", 0, 125, 3),
                )
            )
            mask_data = self.apply_mask_data_dict(source_image, mask_data, True)
            msk_lst = [dic_info["mask"] for dic_info in mask_data]
            mask = self.multi_and(tuple(msk_lst))
            mask = self.keep_roi(mask, self.get_roi("main_roi"))
            self.store_image(mask, "mask_after_roi", rois=self.rois_list)
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
            mask = self.keep_linked_contours(
                src_image=source_image,
                dilation_iter=2,
                tolerance_distance=150,
                tolerance_area=200,
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

    def ensure_mask_zone(self):
        mask = self.mask
        mask = self.keep_roi(mask, "safe_zone")
        return np.count_nonzero(mask) > 0

    def build_mosaic_data(self, **kwargs):
        if self.store_mosaic.lower() == "debug":
            self._mosaic_data = np.array(["source", "img_wth_tagged_cnt", "pseudo_on"])
        return True

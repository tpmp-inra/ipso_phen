import numpy as np

from ipso_phen.ipapi.base.ip_abstract import BaseImageProcessor
from ipso_phen.ipapi.ipt.ipt_check_exposure import IptExposureChecker
from ipso_phen.ipapi.tools.csv_writer import AbstractCsvWriter

_EXPERIMENT = "03AC_ISCA01_1811".lower()


class ImageCsvWriter(AbstractCsvWriter):
    def __init__(self):
        super().__init__()
        self.data_list = dict.fromkeys(
            [
                # Header - text values
                "experiment",
                "plant",
                "plant_id",
                "lbl_1",
                "lbl_2",
                "lbl_3",
                "date_time",
                "angle",
                # Morphology
                "area",
                "hull_area",
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


class Ip03acIsca011811(BaseImageProcessor):
    @staticmethod
    def can_process(dict_data: dict) -> bool:
        """
        Checks if the class can process the image
        :param dict_data: Dictionary containing filter data
        :return: True if current class can process data
        """
        return dict_data["experiment"] in [_EXPERIMENT]

    def init_csv_writer(self):
        return ImageCsvWriter()

    def check_source(self):
        res = super().check_source()
        return res

    def init_csv_data(self, source_image):
        plant_id, lbl_1, lbl_2, lbl_3 = self.plant.split("_")
        _, plant_id = plant_id.split("c")
        self.csv_data_holder.update_csv_value("plant", self.plant)
        self.csv_data_holder.update_csv_value("plant_id", plant_id)
        self.csv_data_holder.update_csv_value("lbl_1", lbl_1)
        self.csv_data_holder.update_csv_value("lbl_2", lbl_2)
        self.csv_data_holder.update_csv_value("lbl_3", lbl_3)

    def init_rois(self):
        if self.is_msp:
            _radius = 1002 / 2
            x, y = 790, 504
        elif self.is_cf_calc:
            _radius = 238 / 2
            x, y = 172, 108
        else:
            self.error_holder.add_error("Failed to init ROIs , unknown camera")
            return
        self.add_circle_roi(
            int(x + _radius), int(y + _radius), int(_radius), "main_roi", "keep"
        )

    def preprocess_source_image(self, **kwargs):
        with IptExposureChecker(
            wrapper=self,
            overexposed_limit=190,
            over_color="black",
            underexposed_limit=35,
            under_color="black",
        ) as (res, ed):
            if res:
                return ed.result
            else:
                return self.current_image

    def build_channel_mask(self, source_image, **kwargs):
        try:
            mask = self.build_mask(
                source_image=source_image,
                is_store_images=True,
                merge_action="multi_and",
                params_list=[
                    dict(
                        channel="bl", min_t=35, max_t=150, morph_op="open", proc_times=2
                    ),
                    dict(channel="b", min_t=120, morph_op="erode"),
                    dict(
                        channel="wl_800",
                        min_t=15,
                        max_t=105,
                        morph_op="open",
                        kernel_size=5,
                    ),
                ],
            )

            self.mask = mask
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
        mask = self.keep_roi(mask, "main_roi")
        return np.count_nonzero(mask) > 0

    def build_mosaic_data(self, **kwargs):
        if self.store_mosaic.lower() == "debug":
            self._mosaic_data = np.array(["source", "img_wth_tagged_cnt", "pseudo_on"])
        else:
            self._mosaic_data = np.array([["source", "mask"], ["bounds", "shapes"]])
        return True

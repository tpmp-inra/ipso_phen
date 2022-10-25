from typing import Any, Union

import numpy as np

from ipso_phen.ipapi.base.ip_abstract import BaseImageProcessor
from ipso_phen.ipapi.tools.csv_writer import AbstractCsvWriter
from ipso_phen.ipapi.ipt.ipt_check_exposure import IptExposureChecker
from ipso_phen.ipapi.base.ipt_functional import call_ipt

_EXPERIMENTS = [
    "02as_mappi1_1810".lower(),
    "09AS_MAPPI2_1903".lower(),
    "16AS_MAPPI3_1605".lower(),
    "21AS_MAPPI4_1911".lower(),
    "TomatoSampleExperiment".lower(),
    "20as_zipfel_1910".lower(),
]


class Ip02asMappi11810(BaseImageProcessor):
    @staticmethod
    def can_process(dict_data: dict) -> bool:
        """
        Checks if the class can process the image
        :param dict_data: Dictionary containing filter data
        :return: True if current class can process data
        """
        return dict_data["experiment"] in _EXPERIMENTS

    def check_source(self):
        res = super().check_source()
        return res

    def init_csv_writer(self):
        return AbstractCsvWriter()

    def update_analysis_params(self, **kwargs) -> dict:
        """Overrides parent to set boundary position

        Returns:
            dict -- dictionnary containing analysis options
        """
        ad = super().update_analysis_params(**kwargs)
        ad["boundary_position"] = 2070

        return ad

    def init_csv_data(self, source_image):
        if "_" in self.plant:
            plant_, exit_order_, *_ = self.plant.split("_")
            _, id_ = plant_.split("a")
            self.csv_data_holder.update_csv_value("plant", self.plant)
            self.csv_data_holder.update_csv_value("plant_id", id_)
            self.csv_data_holder.update_csv_value("exit_order", exit_order_)
        else:
            self.csv_data_holder.update_csv_value("plant", self.plant)
            self.csv_data_holder.update_csv_value("plant_id", 0)
            self.csv_data_holder.update_csv_value("exit_order", 0)

    def init_rois(self):
        # self.add_rect_roi(left=10, width=1800, top=100, height=2050, name="main_roi", tag="keep")
        self.add_rect_roi(width=2050, height=2448, name="main_roi", tag="keep")
        self.add_rect_roi(
            left=126, width=1734, top=244, height=1800, name="safe_zone", tag="safe"
        )
        self.add_rect_roi(
            left=410, width=1200, top=2078, height=78, name="middle_zone", tag="erode"
        )
        self.add_rect_roi(
            left=410, width=1200, top=2156, height=292, name="bottom_zone", tag="erode"
        )
        self.add_rect_roi(
            left=0, width=20, top=1686, height=216, name="black_side", tag="erode"
        )

    def preprocess_source_image(self, **kwargs):
        with IptExposureChecker(
            wrapper=self, overexposed_limit=100, over_color="blue"
        ) as (
            res,
            ed,
        ):
            if res:
                return ed.result
            else:
                return self.source_image

    def build_channel_mask(self, source_image, **kwargs):
        try:
            mask_top = self.build_mask(
                source_image=source_image,
                is_store_images=True,
                merge_action="multi_and",
                params_list=[
                    dict(channel="b", min_t=120, morph_op="erode", kernel_size=3)
                ],
            )
            mask_top = self.delete_roi(mask_top, self.get_roi("middle_zone"))
            mask_top = self.delete_roi(mask_top, self.get_roi("bottom_zone"))
            self.store_image(mask_top, "mask_top", self.rois_list)

            mask_middle = self.build_mask(
                source_image=source_image,
                is_store_images=True,
                merge_action="multi_and",
                params_list=[
                    dict(
                        channel="h",
                        min_t=35,
                        max_t=95,
                        median_filter_size=3,
                        morph_op="open",
                        kernel_size=3,
                        proc_times=2,
                    ),
                    dict(channel="b", min_t=120, morph_op="erode", kernel_size=3),
                    dict(channel="bl", max_t=95, morph_op="erode", kernel_size=3),
                ],
            )

            mask_bottom = self.erode(
                mask_middle, rois=self.get_rois({"erode"}), proc_times=2
            )
            self.store_image(mask_bottom, "mask_bottom", self.rois_list)

            mask_middle = self.keep_roi(
                mask_middle,
                self.get_roi(roi_name="middle_zone"),
            )
            self.store_image(mask_middle, "mask_middle", self.rois_list)
            mask_bottom = self.keep_roi(
                mask_bottom,
                self.get_roi(roi_name="bottom_zone"),
            )
            self.store_image(mask_bottom, "mask_bottom", self.rois_list)

            mask = self.erode(
                image=self.multi_or((mask_top, mask_middle, mask_bottom)),
                proc_times=3,
                rois=(self.get_roi("black_side"),),
            )
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
        mask = self.keep_roi(mask, self.get_roi("safe_zone"))
        return np.count_nonzero(mask) > 0

    def build_mosaic_data(self, **kwargs):
        if self.store_mosaic.lower() == "debug":
            self._mosaic_data = np.array(["source", "img_wth_tagged_cnt", "shapes"])
        else:
            self._mosaic_data = np.array([["source", "mask"], ["bounds", "shapes"]])
        return True

    def extract_image_data(
        self,
        mask: Any,
        source_image: Union[None, str, Any] = None,
        pseudo_color_channel: str = "v",
        pseudo_color_map: int = 2,
        boundary_position: int = -1,
        pseudo_background_type="bw",
    ):
        try:
            dictionary = call_ipt(
                ipt_id="IptAnalyseObservation",
                source=self,
                return_type="data",
                split_plant_name=0 if "zipfel" in self.experiment else 1,
                new_column_names="plant,plant_id,exit_order",
            )
            if isinstance(dictionary, dict):
                self.csv_data_holder.data_list.update(dictionary)
            else:
                self.error_holder.add_error("Failed to add extracted data")

            dictionary = call_ipt(
                ipt_id="IptAnalyzeBound",
                source=self,
                return_type="data",
                line_position=2090,
            )
            if isinstance(dictionary, dict):
                self.csv_data_holder.data_list.update(dictionary)
            else:
                self.error_holder.add_error("Failed to add extracted data")

            dictionary = call_ipt(
                ipt_id="IptAnalyzeChlorophyll", source=self, return_type="data"
            )
            if isinstance(dictionary, dict):
                self.csv_data_holder.data_list.update(dictionary)
            else:
                self.error_holder.add_error("Failed to add extracted data")

            dictionary = call_ipt(
                ipt_id="IptAnalyzeColor", source=self, return_type="data"
            )
            if isinstance(dictionary, dict):
                self.csv_data_holder.data_list.update(dictionary)
            else:
                self.error_holder.add_error("Failed to add extracted data")

            dictionary = call_ipt(
                ipt_id="IptAnalyzeObject", source=self, return_type="data"
            )
            if isinstance(dictionary, dict):
                self.csv_data_holder.data_list.update(dictionary)
            else:
                self.error_holder.add_error("Failed to add extracted data")

            self.csv_data_holder.data_list = {
                k: v for k, v in self.csv_data_holder.data_list.items() if v is not None
            }
        except Exception as e:
            print(f"Failed to extract data because {repr(e)}")
            return False
        else:
            return True

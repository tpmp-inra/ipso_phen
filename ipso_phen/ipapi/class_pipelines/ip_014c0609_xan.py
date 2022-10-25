import os
import pickle
from collections import namedtuple

import numpy as np

from ipso_phen.ipapi.base.ip_abstract import BaseImageProcessor
from ipso_phen.ipapi.ipt.ipt_hough_circles_detector import IptHoughCircles
from ipso_phen.ipapi.tools.csv_writer import AbstractCsvWriter
from ipso_phen.ipapi.tools.common_functions import force_directories

_ExpPlantNameData = namedtuple(
    "NameData", "ecotype, infection_type, age, strain, plant_id"
)

EXPERIMENT_ = "014C0609XAN".lower()


class ImageCsvWriter(AbstractCsvWriter):
    def __init__(self):
        super().__init__()
        self.data_list = dict.fromkeys(
            [
                # Header - text values
                "experiment",
                "plant",
                "plant_id",
                "treatment",
                "plant_location",
                "ecotype",
                "infection_type",
                "age",
                "strain",
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


class Ip014c0609Xan(BaseImageProcessor):
    @staticmethod
    def can_process(dict_data: dict) -> bool:
        """
        Checks if the class can process the image
        :param dict_data: Dictionary containing filter data
        :return: True if current class can process data
        """
        return dict_data["experiment"] in [EXPERIMENT_]

    def init_csv_writer(self):
        return ImageCsvWriter()

    def check_source(self):
        res = super(Ip014c0609Xan, self).check_source()
        return res

    def init_csv_data(self, source_image):
        plant_data = self.extract_name_data()
        plant_id = int(plant_data.plant_id)
        self.csv_data_holder.update_csv_value("plant_id", plant_id)
        self.csv_data_holder.update_csv_value(
            "treatment",
            f"{plant_data.ecotype}_{plant_data.infection_type}_{plant_data.age}_{plant_data.strain}",
        )
        self.csv_data_holder.update_csv_value(
            "plant_location", f"P{plant_id // 36 + 1}_A{plant_id % 36}"
        )
        self.csv_data_holder.update_csv_value("ecotype", plant_data.ecotype)
        self.csv_data_holder.update_csv_value(
            "infection_type", plant_data.infection_type
        )
        self.csv_data_holder.update_csv_value("age", plant_data.age)
        self.csv_data_holder.update_csv_value("strain", plant_data.strain)

    def init_rois(self):
        _MAIN_ROI_RADIUS = 1552 / 2
        self.add_circle_roi(
            int(502 + _MAIN_ROI_RADIUS),
            int(224 + _MAIN_ROI_RADIUS),
            int(_MAIN_ROI_RADIUS),
            "main_roi",
            "keep",
        )

    def build_channel_mask(self, source_image, **kwargs):
        try:
            # Add cover ROI
            folder_ = os.path.join(os.path.dirname(__file__), "stored_data/")
            pickled_file = f"{folder_}{self.name}_inneCircleRegion.pkl"
            force_directories(folder_)
            if os.path.isfile(pickled_file):
                with open(pickled_file, "rb") as f:
                    circle = pickle.load(f)
            else:
                kwargs_ = dict(
                    wrapper=self,
                    source_file="cropped_source",
                    operator="sobel",
                    min_radius=550,
                    max_radius=700,
                    min_distance=10,
                )
                if self.is_dark_cover():
                    kwargs_.update(
                        dict(channel="s", step_radius=10, max_peaks=4, threshold=80)
                    )
                else:
                    kwargs_.update(dict(channel="rd", threshold=133, max_peaks=2))
                with IptHoughCircles(**kwargs_) as (res, ed):
                    if not res or not ed.result:
                        self.error_holder.add_error("Unable to detect circles")
                        circle = None
                    else:
                        circles = sorted(ed.result, key=lambda circle_: circle_[2])
                        circle = circles[0]
                        with open(pickled_file, "wb") as f:
                            pickle.dump(circle, f)

            if self.is_dark_cover():
                if circle is not None:
                    self.add_circle_roi(
                        circle[0] + 502,
                        circle[1] + 224,
                        circle[2] - 4,
                        "safe_ish_roi",
                        "safe_ish",
                    )
                    self.add_circle_roi(
                        circle[0] + 502,
                        circle[1] + 224,
                        circle[2] - 32,
                        "safe_roi",
                        "safe",
                    )

                    mask_inner = self.build_mask(
                        source_image,
                        **dict(
                            is_store_images=True,
                            merge_action="multi_and",
                            params_list=[
                                dict(channel="h", method="otsu", invert=True),
                                dict(channel="b", method="otsu", invert=False),
                            ],
                        ),
                    )
                    mask_inner = self.open(mask_inner, kernel_size=3, proc_times=1)
                    mask_inner = self.keep_roi(
                        src_mask=mask_inner, roi="safe_ish_roi", dbg_str="mask_inner"
                    )

                    mask_outer = self.build_mask(
                        source_image,
                        **dict(
                            is_store_images=True,
                            merge_action="multi_and",
                            params_list=[
                                dict(channel="wl_680", method="otsu", invert=True),
                                dict(channel="wl_905", method="otsu", invert=False),
                                dict(
                                    channel="h",
                                    min_t=10,
                                    max_t=70,
                                    morph_op="open",
                                    kernel_size=3,
                                    proc_times=2,
                                ),
                                dict(channel="b", method="otsu", invert=False),
                            ],
                        ),
                    )
                    mask_outer = self.delete_roi(
                        mask_outer, "safe_ish_roi", "mask_outer"
                    )
                    mask_outer = self.open(
                        mask_outer, kernel_size=5, proc_times=2, dbg_text="mask_open"
                    )

                    mask = self.multi_or((mask_inner, mask_outer))
                    mask = self.keep_roi(mask, "main_roi")
                else:
                    mask = self.build_mask(
                        source_image,
                        **dict(
                            is_store_images=True,
                            merge_action="multi_and",
                            params_list=[
                                dict(channel="wl_680", method="otsu", invert=True),
                                dict(channel="wl_905", method="otsu", invert=False),
                                dict(channel="h", method="otsu", invert=True),
                                dict(channel="b", method="otsu", invert=False),
                            ],
                        ),
                    )
                    mask = self.keep_roi(mask, "main_roi", dbg_str="mask_roi_raw")
                    mask = self.open(
                        mask, kernel_size=5, proc_times=2, dbg_text="mask_open"
                    )
            else:
                self.add_circle_roi(
                    circle[0] + 502,
                    circle[1] + 224,
                    circle[2] - 4,
                    "safe_ish_roi",
                    "safe_ish",
                )
                self.add_circle_roi(
                    circle[0] + 502, circle[1] + 224, circle[2] - 64, "safe_roi", "safe"
                )
                mask_inner = self.build_mask(
                    source_image,
                    **dict(
                        is_store_images=True,
                        merge_action="multi_and",
                        params_list=[
                            dict(
                                channel="h",
                                min_t=3,
                                max_t=70,
                                morph_op="close",
                                kernel_size=3,
                                proc_times=2,
                            ),
                            dict(channel="b", method="otsu", invert=False),
                        ],
                    ),
                )
                mask_inner = self.keep_roi(
                    mask_inner, "safe_ish_roi", dbg_str="mask_inner"
                )

                mask_outer = self.build_mask(
                    source_image,
                    **dict(
                        is_store_images=True,
                        merge_action="multi_and",
                        params_list=[
                            dict(channel="h", method="otsu", invert=True),
                            dict(channel="s", method="otsu", invert=False),
                            dict(channel="l", method="otsu", invert=False),
                            dict(channel="b", method="otsu", invert=False),
                        ],
                    ),
                )
                mask_outer = self.delete_roi(mask_outer, "safe_ish_roi", "mask_outer")

                mask = self.multi_or((mask_inner, mask_outer))
                mask = self.open(
                    mask, kernel_size=5, proc_times=1, dbg_text="mask_open"
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
            mask = self.mask
            if (self.mask is None) or (np.count_nonzero(mask) <= 0):
                return False
            if self.is_dark_cover():
                mask = self.keep_linked_contours(
                    src_image=source_image,
                    src_mask=mask,
                    tolerance_distance=1,
                    tolerance_area=1322,
                    root_position="MIDDLE_CENTER",
                    dilation_iter=0,
                    area_override_size=0,
                )
            else:
                mask = self.keep_linked_contours(
                    src_image=source_image,
                    src_mask=mask,
                    tolerance_distance=100,
                    tolerance_area=2300,
                    root_position="MIDDLE_CENTER",
                    dilation_iter=0,
                    area_override_size=0,
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
        mask = self.keep_roi(mask, "main_roi")
        return np.count_nonzero(mask) > 0

    def build_mosaic_data(self, **kwargs):
        if self.store_mosaic.lower() == "debug":
            self._mosaic_data = np.array(
                [["source", "img_wth_tagged_cnt"], ["mask", "pseudo_on"]]
            )
        return True

    def extract_name_data(self):
        return _ExpPlantNameData(*self.plant.split("_"))

    def is_dark_cover(self):
        return self.extract_name_data().infection_type == "s2"

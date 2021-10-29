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
                "has_cover",
                "bad_cover",
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
                "has_cover",
                "bad_cover",
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


class Ip012c0629ggt(BaseImageProcessor):
    @staticmethod
    def can_process(dict_data: dict) -> bool:
        """
        Checks if the class can process the image
        :param dict_data: Dictionary containing filter data
        :return: True if current class can process data
        """
        return dict_data["experiment"] in ["012C0629_GGT".lower()]

    def init_csv_writer(self):
        if self.wavelength == "fluo-":
            return ImageFluoCsvWriter()
        else:
            return ImageMpsCsvWriter()

    def check_source(self):
        res = super(Ip012c0629ggt, self).check_source()
        if res:
            res = not self.is_under_exposed
            if not res:
                self.error_holder.add_error("HANDLED FAILURE Image is under exposed")
        if res:
            res = not self.is_over_exposed
            if not res:
                self.error_holder.add_error(
                    "HANDLED FAILURE Image is over exposed",
                    new_error_kind="source_issue",
                )
        if res:
            res = not (self.is_cf_calc and self.is_cover_missing)
            if not res:
                self.error_holder.add_error(
                    "HANDLED FAILURE Cover missing for fluorescence image",
                    new_error_kind="source_issue",
                )
        if res:
            res = not self.is_test_acquisition
            if not res:
                self.error_holder.add_error(
                    "HANDLED FAILURE Image image is from a test",
                    new_error_kind="source_issue",
                )
        if res:
            res = not self.is_bad_acquisition
            if not res:
                self.error_holder.add_error(
                    "HANDLED FAILURE Image image is corrupted",
                    new_error_kind="source_issue",
                )
        return res

    def init_csv_data(self, source_image):
        [treatment_1, treatment_2, plant_id_] = self.plant.split("_")
        self.csv_data_holder.update_csv_value("plant_id", plant_id_)
        self.csv_data_holder.update_csv_value("treatment", f"{treatment_1}_{treatment_2}")
        self.csv_data_holder.update_csv_value("has_cover", not self.is_cover_missing)
        self.csv_data_holder.update_csv_value("bad_cover", self.is_cover_bad)

    def init_rois(self):
        if self.is_cf_calc:
            roi_radius = 404 / 2
            self.add_circle_roi(
                int(118 + roi_radius),
                int(24 + roi_radius),
                int(roi_radius),
                "main_roi",
                "keep",
            )
        else:
            roi_radius = 2012 / 2
            self.add_circle_roi(
                int(246 + roi_radius),
                int(20 + roi_radius),
                int(roi_radius),
                "main_roi",
                "keep",
            )
            roi_radius = 922 / 2
            self.add_circle_roi(
                int(835 + roi_radius),
                int(508 + roi_radius),
                int(roi_radius),
                "cover_roi",
                "safe_ish",
            )
            roi_radius = 794 / 2
            self.add_circle_roi(
                int(878 + roi_radius),
                int(620 + roi_radius),
                int(roi_radius),
                "earth_roi",
                "safe_ish",
            )

    def build_channel_mask(self, source_image, **kwargs):
        try:
            if self.is_cf_calc:
                params_dict = [
                    dict(channel="v", min_t=50),
                    dict(channel="bl", min_t=50),
                ]
                op = "multi_or"
                mask = self.build_mask(
                    source_image,
                    **dict(
                        is_store_images=True, merge_action=op, params_list=params_dict
                    ),
                )
            else:
                op = "multi_and"
                if self.is_cover_missing:
                    params_dict = [
                        dict(channel="h", min_t=15, max_t=80, median_filter_size=5),
                        dict(channel="s", min_t=15, max_t=120, median_filter_size=5),
                        dict(channel="a", min_t=105, max_t=130, median_filter_size=5),
                        dict(channel="b", min_t=125, max_t=170, median_filter_size=5),
                    ]
                    mask = self.build_mask(
                        source_image,
                        **dict(
                            is_store_images=True,
                            merge_action=op,
                            params_list=params_dict,
                        ),
                    )
                    mask = self.multi_or(
                        (
                            self.keep_roi(mask, "earth_roi"),
                            self.open(self.delete_roi(mask, "earth_roi"), 5),
                        )
                    )
                else:
                    # Build center mask
                    mask_h = self.build_mask(
                        source_image,
                        **dict(
                            is_store_images=True,
                            merge_action="none",
                            params_list=[
                                dict(
                                    channel="h",
                                    max_t=100,
                                    morph_op="close",
                                    kernel_size=7,
                                )
                            ],
                        ),
                    )
                    mask_h = self.close(mask_h, 11)
                    mask_b = self.build_mask(
                        source_image,
                        **dict(
                            is_store_images=True,
                            merge_action=op,
                            params_list=[
                                dict(
                                    channel="b",
                                    min_t=127,
                                    max_t=160,
                                    morph_op="close",
                                    kernel_size=7,
                                    median_filter_size=3,
                                )
                            ],
                        ),
                    )
                    mask_inner = self.multi_and((mask_h, mask_b))
                    mask_inner = self.keep_roi(mask_inner, "cover_roi")
                    self.store_image(mask_inner, "mask_inner")
                    # Build outside mask
                    params_dict = [
                        dict(channel="h", min_t=15, max_t=80, median_filter_size=5),
                        dict(channel="s", min_t=15, max_t=120, median_filter_size=5),
                        dict(channel="a", min_t=105, max_t=130, median_filter_size=5),
                        dict(channel="b", min_t=125, max_t=170, median_filter_size=5),
                    ]
                    mask_outer = self.build_mask(
                        source_image,
                        **dict(
                            is_store_images=True,
                            merge_action=op,
                            params_list=params_dict,
                        ),
                    )

                    mask = self.multi_or((mask_inner, mask_outer))
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
                mask = self.erode(mask, 3)
                self.store_image(mask, "mask_eroded", rois=self.rois_list)

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

    def ensure_mask_zone(self):
        mask = self.mask
        if self.is_cf_calc:
            mask = self.keep_roi(mask, "main_roi")
        else:
            mask = self.keep_roi(mask, "cover_roi")
        return np.count_nonzero(mask) > 0

    def build_mosaic_data(self, **kwargs):
        if self.store_mosaic.lower() == "debug":
            self._mosaic_data = np.array(
                [["source", "img_wth_tagged_cnt"], ["mask", "shapes"]]
            )
        return True

    @property
    def is_cover_missing(self):
        _06_30_no_cover_lst = [f"2603_oro_{idx}" for idx in range(325, 361)]
        _06_30_no_cover_lst += ["xrq_oro_37".lower(), "xrq_oro_39".lower()]
        _06_30_no_cover_lst += [f"xrq_oro_{idx}" for idx in range(44, 60)]
        _06_30_no_cover_lst += [f"xrq_oro_{idx}" for idx in range(61, 72)]
        _06_30_no_cover_lst += [f"xrq_oro_{idx}" for idx in range(73, 109)]
        if self.day in ["30", "01", "02"]:
            return self.plant in _06_30_no_cover_lst

        _07_03_no_cover_lst = ["2603_oro_348", "2603_oro_356"]
        _07_03_no_cover_lst += [f"xrq_oro_{idx}" for idx in range(73, 109)]
        if self.day in ["03", "04"]:
            return self.plant in _07_03_no_cover_lst

        _07_09_no_cover_lst = [
            "xrq_oro_101",
            "xrq_oro_75",
            "xrq_oro_77",
            "xrq_oro_82",
            "xrq_oro_89",
        ]
        return self.plant in _07_09_no_cover_lst

    @property
    def is_cover_bad(self):
        return ((self.plant == "2603_oro_320") and (self.day == "11")) or (
            (self.plant == "2603_oro_358") and (self.day in ["11", "15", "16"])
        )

    @property
    def is_under_exposed(self):
        return (self.month == "07") and (self.day == "03") and (self.hour == "15")

    @property
    def is_over_exposed(self):
        return (
            (self.plant == "xrq_oro_37") and (self.month == "07") and (self.day == "04")
        )

    @property
    def is_test_acquisition(self):
        if self.is_cf_calc:
            if self.day == "11":
                return not self.is_between_times(start_hour="12", end_hour="15")
            elif self.day == "12":
                return not self.is_between_times(start_hour="12", end_hour="15")
            else:
                return False
        else:
            return False

    @property
    def is_bad_acquisition(self):
        return self.is_cf_calc and (
            (self.plant == "xrq_oro_85")
            and (self.day == "12")
            and (self.hour == "13")
            or (self.plant == "2603_oro_339")
            and (self.day == "15")
            and (self.hour == "14")
            or (self.plant == "2603_oro_337")
            and (self.day == "16")
            and (self.hour == "14")
            or (self.plant == "2603_oro_334")
            and (self.day == "16")
            and (self.hour == "14")
        )

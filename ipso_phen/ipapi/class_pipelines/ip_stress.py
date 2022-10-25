import numpy as np

from ipso_phen.ipapi.base.ip_abstract import BaseImageProcessor
from ipso_phen.ipapi.ipt.ipt_linear_transformation import IptLinearTransformation
from ipso_phen.ipapi.ipt.ipt_check_exposure import IptExposureChecker
from ipso_phen.ipapi.tools.csv_writer import AbstractCsvWriter

_EXPERIMENTS = ["05AS_STRESS_1812".lower(), "08AS_STRES3_1902".lower()]


class ImageCsvWriter(AbstractCsvWriter):
    def __init__(self):
        super().__init__()
        self.data_list = dict.fromkeys(
            [
                # Header - text values
                "experiment",
                "plant",
                "plant_id",
                "data_1",
                "data_2",
                "date_time",
                "hist_bins",
                # Morphology
                "area",
                "hull_area",
                "width_data",
                "shape_height",
                "centroid",
                "shape_solidity",
                "shape_extend",
                "straight_bounding_rectangle",
                "rotated_bounding_rectangle",
                "minimum_enclosing_circle",
                "bound_data",
                "quantile_width_4",
                # Color descriptors
                "color_std_dev",
                "color_mean",
                "quantile_color_5",
                # Chlorophyll data
                "chlorophyll_mean",
                "chlorophyll_std_dev",
            ]
        )


class IpStress(BaseImageProcessor):
    @staticmethod
    def can_process(dict_data: dict) -> bool:
        """
        Checks if the class can process the image
        :param dict_data: Dictionary containing filter data
        :return: True if current class can process data
        """
        return dict_data["experiment"] in _EXPERIMENTS

    def init_csv_writer(self):
        return ImageCsvWriter()

    def check_source(self):
        res = super().check_source()
        return res

    def init_csv_data(self, source_image):
        main_, dt1_, dt2_, _ = self.plant.split("_")
        _, id_ = main_.split("a")
        self.csv_data_holder.update_csv_value("plant_id", id_)
        self.csv_data_holder.update_csv_value("data_1", dt1_)
        self.csv_data_holder.update_csv_value("data_2", dt2_)

    def init_rois(self):
        self.add_rect_roi(90, 1900, 300, 1740, "main_roi", "keep")
        self.add_rect_roi(230, 1550, 350, 1546, "safe_zone", "safe")

    # def _fix_source_image(self, img):
    #     tmp_wrapper = BaseImageProcessor(self.file_path)
    #     with IptLinearTransformation(wrapper=tmp_wrapper,
    #                                  method='gamma_target',
    #                                  target_brightness=150) as (res, ed):
    #         if res:
    #             tmp_wrapper.source_image = ed.result
    #         else:
    #             tmp_wrapper.source_image = img
    #     with IptLinearTransformation(wrapper=tmp_wrapper,
    #                                  alpha_gamma=130) as (res, ed):
    #         if res:
    #             return ed.result
    #         else:
    #             return img

    def preprocess_source_image(self, **kwargs):
        with IptExposureChecker(
            wrapper=self,
            overexposed_limit=170,
            over_color="blue",
            underexposed_limit=70,
            under_color="blue",
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
                    dict(channel="h", min_t=20, max_t=100, morph_op="close"),
                    dict(
                        channel="v",
                        min_t=75,
                        max_t=192,
                        morph_op="close",
                        kernel_size=7,
                        proc_times=3,
                    ),
                    # dict(channel='gr',
                    #      min_t=90,
                    #      morph_op='open',
                    #      kernel_size=9,
                    #      proc_times=2),
                    dict(channel="wl_550", min_t=20, morph_op="open", kernel_size=5),
                    dict(
                        channel="wl_800",
                        min_t=30,
                        max_t=100,
                        morph_op="open",
                        kernel_size=5,
                        proc_times=3,
                    ),
                ],
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
        mask = self.keep_roi(mask, "")
        return np.count_nonzero(mask) > 0

    def build_mosaic_data(self, **kwargs):
        return True

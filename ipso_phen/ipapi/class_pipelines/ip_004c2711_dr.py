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
                "treatment",
                "genotype",
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


_MAIN_ROI_RADIUS = 1552 / 2
_SAFE_ROI_RADIUS = 944 / 2
_REQUIRED_ROI_RADIUS = 286 / 2


class Ip004c2711dr(BaseImageProcessor):
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
        return dict_data["experiment"] in ["004c2711_dr".lower()]

    def init_rois(self):
        self.add_circle_roi(
            int(502 + _MAIN_ROI_RADIUS),
            int(224 + _MAIN_ROI_RADIUS),
            int(_MAIN_ROI_RADIUS),
            "main_roi",
            "keep",
        )
        self.add_circle_roi(
            int(774 + _SAFE_ROI_RADIUS),
            int(500 + _SAFE_ROI_RADIUS),
            int(_SAFE_ROI_RADIUS),
            "safe_roi",
            "safeish",
        )
        self.add_circle_roi(
            int(1122 + _REQUIRED_ROI_RADIUS),
            int(828 + _REQUIRED_ROI_RADIUS),
            int(_REQUIRED_ROI_RADIUS),
            "required_roi",
            "required",
        )

    def check_source(self):
        if self.is_color_checker:
            self.error_holder.add_error("HANDLED FAILURE color checker")
            return False

        if self.is_corrupted:
            self.error_holder.add_error(
                "Image has been tagged as corrupted", new_error_kind="source_issue"
            )
            return False

        return True

    def init_csv_data(self, source_image):
        try:
            _, treatment_, *genotype_ = self.plant.split("_")
            self.csv_data_holder.update_csv_value("treatment", treatment_)
            self.csv_data_holder.update_csv_value("genotype", "".join(genotype_))
        except:
            self.csv_data_holder.update_csv_value("treatment", "unknown")

    def build_channel_mask(self, source_image, **kwargs):
        try:
            op = "multi_and"
            params_dict = [
                dict(channel="h", min_t=5, max_t=75, morph_op="open", kernel_size=5),
                dict(channel="a", min_t=95, max_t=135, morph_op="open", kernel_size=5),
                dict(channel="b", min_t=125, max_t=175, morph_op="open", kernel_size=5),
            ]
            mask_inner = self.build_mask(
                source_image,
                **dict(is_store_images=True, merge_action=op, params_list=params_dict),
            )
            mask_inner = self.keep_roi(mask_inner, "safe_roi", "mask_inner")

            params_dict = [
                dict(channel="h", min_t=20, max_t=60, morph_op="open", kernel_size=5),
                dict(channel="s", min_t=35, max_t=130, morph_op="erode", kernel_size=5),
                dict(channel="a", max_t=130, morph_op="open", kernel_size=5),
            ]
            mask_outer = self.build_mask(
                source_image,
                **dict(is_store_images=True, merge_action=op, params_list=params_dict),
            )
            mask_outer = self.delete_roi(mask_outer, "safe_roi", "mask_outer")

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
            if self.is_cover_missing:
                mask = self.keep_linked_contours(
                    tolerance_distance=0,
                    tolerance_area=500,
                    root_position="MIDDLE_CENTER",
                )
            else:
                mask = self.keep_linked_contours(
                    tolerance_distance=55,
                    tolerance_area=500,
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
        mask = self.keep_roi(mask, "required_roi")
        return np.count_nonzero(mask) > 0

    def build_mosaic_data(self, **kwargs):
        if self.store_mosaic.lower() == "debug":
            self._mosaic_data = np.array(
                [["source", "src_img_with_cnt_after_agg_iter_last"], ["mask", "shapes"]]
            )
        return True

    # Properties

    @property
    def is_cover_missing(self):
        return self.is_before_date(year="2017", month="12", day="14")

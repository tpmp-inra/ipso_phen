import cv2
import numpy as np

from ipso_phen.ipapi.base.ip_abstract import BaseImageProcessor
from ipso_phen.ipapi.ipt.ipt_check_exposure import IptExposureChecker
from ipso_phen.ipapi.tools.csv_writer import AbstractCsvWriter

_020_EXPERIMENT = "020s1804_nem".lower()


class ImageCsvWriter(AbstractCsvWriter):
    def __init__(self):
        super().__init__()
        self.data_list = dict.fromkeys(
            [
                # Header - text values
                "experiment",
                "plant",
                "plant_id",
                "angle",
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
                "rotated_bounding_rectangle",
                "minimum_enclosing_circle",
                "bound_data",
                "quantile_width_4",
                # Color descriptors
                "color_std_dev",
                "color_mean",
                # Chlorophyll data
                "chlorophyll_mean",
                "chlorophyll_std_dev",
            ]
        )


class Ip020s1804nem(BaseImageProcessor):
    @staticmethod
    def can_process(dict_data: dict) -> bool:
        """
        Checks if the class can process the image
        :param dict_data: Dictionnary containing filter data
        :return: True if current class can process data
        """
        return dict_data["experiment"] in [_020_EXPERIMENT]

    def init_csv_writer(self):
        return ImageCsvWriter()

    def check_source(self):
        res = super(Ip020s1804nem, self).check_source()
        if not res:
            return False

        if self.is_corrupted:
            self.error_holder.add_error(
                "Image has been tagged as corrupted", new_error_kind="source_issue"
            )
            return False

        if self.is_empty_pot:
            self.error_holder.add_error(
                "Image has been tagged as empty", new_error_kind="source_issue"
            )
            return False

        return True

    def init_csv_data(self, source_image):
        *_, id_ = self.plant.split("_")
        self.csv_data_holder.update_csv_value("plant_id", id_)

    def _fix_source_image(self, img):
        if "top" in self.camera:
            min_s = [23, 16, 17]
            max_s = [230, 187, 167]
            return self.fix_white_balance(img, min_s, max_s)
        else:
            return img

    def init_rois(self):
        if "top" in self.camera:
            self.add_rect_roi(824, 850, 622, 846, "safe_zone", "safe")

            self.add_rect_roi(732, 1041, 522, 1040, "pot_holder", "pot_holder")

            self.add_rect_roi(4, 2440, 4, 518, "top", "cardinals")

            self.add_rect_roi(675, 51, 913, 422, "stain", "stain")
            self.add_rect_roi(0, 735, 536, 184, "belt_top_left", "belt")
            self.add_rect_roi(1776, 669, 525, 210, "belt_top_right", "belt")
            self.add_rect_roi(0, 738, 1365, 186, "belt_bottom_left", "belt")
            self.add_rect_roi(1767, 675, 1356, 201, "belt_bottom_right", "belt")

            self.add_rect_roi(66, 64, 789, 64, "dot_1", "dot")
            self.add_rect_roi(531, 64, 788, 64, "dot_2", "dot")
            self.add_rect_roi(68, 64, 1235, 64, "dot_3", "dot")
            self.add_rect_roi(531, 64, 1237, 64, "dot_4", "dot")
            self.add_rect_roi(1777, 64, 939, 64, "dot_5", "dot")
            self.add_rect_roi(2150, 64, 940, 64, "dot_6", "dot")
            self.add_rect_roi(2379, 64, 790, 64, "dot_7", "dot")
            self.add_rect_roi(1776, 64, 1252, 64, "dot_8", "dot")
            self.add_rect_roi(2149, 64, 1252, 64, "dot_9", "dot")
            self.add_rect_roi(2378, 64, 1235, 64, "dot_10", "dot")
            self.add_rect_roi(686, 40, 792, 64, "dot_11", "dot")
        else:
            self.add_rect_roi(6, 2038, 6, 1482, "main_roi", "keep")
            self.add_rect_roi(168, 1736, 144, 1184, "safe_roi", "safeish")
            self.add_rect_roi(550, 900, 1212, 142, "cover", "erode")
            self.add_rect_roi(520, 980, 1324, 184, "label", "erode")

    def build_channel_mask(self, source_image, **kwargs):
        try:
            if "top" in self.camera:
                mask_s, stored_name = self.get_mask(
                    source_image, "s", 70, 255, self.rois_list, False, 15
                )
                self.store_image(mask_s, stored_name, self.rois_list)
                mask_a, stored_name = self.get_mask(
                    source_image, "a", 105, 125, self.rois_list, False, 15
                )
                self.store_image(mask_a, stored_name, self.rois_list)
                mask_b, stored_name = self.get_mask(
                    source_image, "b", 130, 175, self.rois_list, False, 15
                )
                self.store_image(mask_b, stored_name, self.rois_list)

                mask_belt_a = self.keep_rois(
                    mask_a.copy(), ["belt", "dot"], "mask_belt_a"
                )
                mask_belt_b = self.keep_rois(
                    mask_b.copy(), ["belt", "dot"], "mask_belt_b"
                )
                mask_belt = self.multi_and((mask_belt_a, mask_belt_b))
                self.store_image(mask_belt, "mask_belt", self.rois_list)

                mask_stain = self.keep_rois(mask_a.copy(), ["stain"], "mask_stain")

                mask_top = self.keep_rois(mask_s, ["cardinals"])
                self.store_image(mask_top, "mask_top", self.rois_list)

                mask_unsafe = self.multi_or((mask_belt, mask_stain))
                self.store_image(mask_unsafe, "mask_unsafe", self.rois_list)

                mask = self.multi_or(
                    (
                        mask_unsafe,
                        mask_top,
                        self.delete_rois(mask_b, ("belt", "stain", "dot", "cardinals")),
                    )
                )
                self.store_image(mask, "mask_median_clean")
            else:
                # Get main mask
                mask, stored_name = self.get_mask(
                    source_image, "b", 115, 255, self.rois_list, False, 5
                )
                self.store_image(mask, stored_name, self.rois_list)
                mask = self.apply_rois(mask, "get_mask_and_apply_rois")

                # Get label mask
                mask_bl, stored_name = self.get_mask(
                    source_image, "bl", 0, 110, self.rois_list, False, 5
                )
                self.store_image(mask_bl, stored_name, self.rois_list)
                mask_h, stored_name = self.get_mask(
                    source_image, "h", 0, 95, self.rois_list, False, 5
                )
                self.store_image(mask_h, stored_name, self.rois_list)
                mask_label = self.multi_and((mask, mask_h, mask_bl))
                mask_label = self.keep_roi(mask_label, self.get_roi("label"))
                self.store_image(mask_label, "mask_label", self.rois_list)

                # Merge masks
                mask = self.delete_roi(mask, self.get_roi("label"))
                mask = self.multi_or((mask, mask_label))
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

    def crop_mask(self):
        if "top" in self.camera:
            pass
        else:
            pass
        return True

    def clean_mask(self, source_image):
        try:
            mask = self.mask
            if "top" in self.camera:
                mask = self.keep_linked_contours(
                    src_image=source_image,
                    src_mask=mask,
                    dilation_iter=7,
                    tolerance_distance=30,
                    tolerance_area=64 * 64,
                    roi=self.get_roi("pot_holder"),
                    root_position="MIDDLE_CENTER",
                    trusted_safe_zone=True,
                )
                self.store_image(mask, "mask", self.rois_list)
            else:
                # Clean masks
                mask = self.erode(
                    mask,
                    5,
                    cv2.MORPH_ELLIPSE,
                    (self.get_roi("cover"), self.get_roi("label")),
                )
                self.store_image(mask, "mask_after_erosion", self.rois_list)
                mask = self.keep_linked_contours(
                    src_image=source_image,
                    src_mask=mask,
                    tolerance_distance=-1,
                    tolerance_area=2500,
                    roi=self.get_roi("safe_roi"),
                )
                mask = self.dilate(
                    mask,
                    5,
                    cv2.MORPH_ELLIPSE,
                    (self.get_roi("cover"), self.get_roi("label")),
                )
                self.store_image(mask, "mask", self.rois_list)
                self.mask = mask
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
        if "top" in self.camera:
            mask = self.keep_roi(mask, "safe_zone")
        else:
            mask = self.keep_roi(mask, "safe_roi")
        return np.count_nonzero(mask) > 0

    def build_mosaic_data(self, **kwargs):
        if self.store_mosaic.lower() == "debug":
            self._mosaic_data = np.array(["source", "img_wth_tagged_cnt", "pseudo_on"])
        return True

    @property
    def is_empty_pot(self):
        return self.plant in [
            "s1804_nem_04",
            "s1804_nem_16",
            "s1804_nem_43",
            "s1804_nem_61",
            "s1804_nem_75",
            "s1804_nem_76",
        ]

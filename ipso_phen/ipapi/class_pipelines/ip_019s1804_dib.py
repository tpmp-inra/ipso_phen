import numpy as np

from ipso_phen.ipapi.base.ip_abstract import BaseImageProcessor
from ipso_phen.ipapi.tools.csv_writer import AbstractCsvWriter
from ipso_phen.ipapi.tools.common_functions import add_header_footer
from ipso_phen.ipapi.tools.common_functions import time_method


class ImageCsvWriter(AbstractCsvWriter):
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
                "angle",
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


class Ip019s1804dib(BaseImageProcessor):
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
        return dict_data["experiment"] in ["019s1804_dib"]

    def init_rois(self):
        self.add_rect_roi(90, 1900, 300, 1740, "main_roi", "keep")
        self.add_rect_roi(230, 1550, 350, 1546, "safe_zone", "safe")

    def _process_job_vis(self, img):
        self.init_rois()

        mask_data = self.prepare_masks_data_dict(
            (("h", 15, 100, 3), ("s", 20, 170, 3), ("b", 110, 180, 3))
        )
        mask_data = self.apply_mask_data_dict(img, mask_data, True)
        msk_lst = [dic_info["mask"] for dic_info in mask_data]
        mask = self.multi_and(msk_lst)
        mask = self.keep_roi(mask, self.get_roi("main_roi"))
        self.store_image(mask, "mask_after_roi", rois=self.rois_list)

        mask = self.keep_linked_contours(
            src_image=img,
            src_mask=mask,
            dilation_iter=2,
            tolerance_distance=150,
            tolerance_area=200,
            root_position="MIDDLE_CENTER",
        )
        self.store_image(mask, "mask")
        self.mask = mask

        masked_whole = self.apply_mask(img, mask, "white")
        self.store_image(masked_whole, "masked_whole")

        self._mosaic_data = np.array(
            [
                ["source", "masked_whole"],
                ["src_img_with_cnt_after_agg_iter_last", "mask_clean"],
            ]
        )

        return True, mask

    def _process_job_nir(self, img):
        self._mosaic_data, mosaic_image_ = self.build_channels_mosaic(img, self.rois_list)
        self.store_image(mosaic_image_, "full_channel_mosaic")
        return True, None

    def _process_job_fluo(self, img):
        self._mosaic_data, mosaic_image_ = self.build_channels_mosaic(img, self.rois_list)
        self.store_image(mosaic_image_, "full_channel_mosaic")
        return True, None

    @add_header_footer
    @time_method
    def process_image(self, **kwargs):
        """Executes pipeline instructions to process image

        Raises:
            NotImplementedError -- Only VIS, FLUO are implemented

        Returns:
            boolean -- is job successful
        """

        res = False
        threshold_only_ = kwargs.get("threshold_only", 0) == 1
        try:
            if self.is_corrupted:
                self.error_holder.add_error(
                    "Image has been tagged as corrupted", new_error_kind="source_issue"
                )
                return False

            img = self.source_image

            [_, _, plant_id_, plant_suffix] = self.plant.split("_")
            self.csv_data_holder.update_csv_value("plant_id", plant_id_)
            self.csv_data_holder.update_csv_value("plant_suffix", plant_suffix)

            if self.is_vis:
                res, mask = self._process_job_vis(img)
            elif self.is_nir:
                res, mask = self._process_job_nir(img)
            elif self.is_fluo:
                res, mask = self._process_job_fluo(img)
            else:
                mask = None
                res = False

            if not res:
                self.error_holder.add_error("Segmentation failed")

            if res and not threshold_only_:
                res = self.extract_image_data(mask)
        except Exception as e:
            self.error_holder.add_error(f'Failed to process image because "{repr(e)}"')
            res = False

        self.print_images()
        return res

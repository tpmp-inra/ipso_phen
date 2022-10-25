import numpy as np

from ipso_phen.ipapi.tools.common_functions import add_header_footer

from ipso_phen.ipapi.base.ip_abstract import BaseImageProcessor
from ipso_phen.ipapi.tools.common_functions import time_method
from ipso_phen.ipapi.tools.csv_writer import AbstractCsvWriter

_MAIN_ROI_RADIUS = 1240 / 2


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
                "date_time",
                "hist_bins",
                # Morphology
                "area",
                "hull_area",
                "width_data",
                "shape_height",
                "shape_solidity",
                "shape_extend",
                "rotated_bounding_rectangle",
                "minimum_enclosing_circle",
                # Histogram
                "color_std_dev",
                "color_mean",
            ]
        )


class Ip0017s1804eff(BaseImageProcessor):
    def init_csv_writer(self):
        return ImageCsvWriter()

    @staticmethod
    def can_process(dict_data: dict) -> bool:
        """
        Checks if the class can process the image
        :param dict_data: Dictionary containing filter data
        :return: True if current class can process data²
        """
        return dict_data["experiment"] in ["0017s1804_eff"]

    def _apply_std_threshold(self, img):
        fwb_img = self.fix_white_balance(img, (0, 0, 0), (220, 220, 220))
        self.store_image(fwb_img, "fwb_img_blue")

        op = "multi_and"
        params_dict = [
            dict(channel="h", min_t=5, max_t=175),
            dict(channel="v", min_t=20, max_t=250),
            dict(channel="a", min_t=95, max_t=135),
            dict(channel="b", min_t=100, max_t=195),
        ]
        mask = self.build_mask(
            fwb_img,
            **dict(is_store_images=True, merge_action=op, params_list=params_dict),
        )

        mask = self.keep_roi(mask, self.get_roi("main_roi"))
        self.store_image(mask, "mask")
        self.mask = mask

        return mask, fwb_img

    def init_rois(self):
        self.add_circle_roi(
            int(600 + _MAIN_ROI_RADIUS),
            int(436 + _MAIN_ROI_RADIUS),
            int(_MAIN_ROI_RADIUS),
            "main_roi",
            "keep",
        )

    def _process_job_vis(self, img):
        self.init_rois()

        mask, fwb_img = self._apply_std_threshold(img)

        mask = self.keep_linked_contours(
            src_image=fwb_img,
            src_mask=mask,
            dilation_iter=5,
            tolerance_distance=100,
            tolerance_area=500,
            root_position="MIDDLE_CENTER",
        )
        self.store_image(mask, "mask_clean")

        masked_whole = self.apply_mask(fwb_img, mask, "white")
        self.store_image(masked_whole, "masked_whole")

        return True, mask

    def _process_job_nir(self, img):
        self.default_process()
        return True, None

    def _process_job_fluo(self, img):
        self.default_process()
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
        try:
            if self.is_corrupted:
                self.error_holder.add_error(
                    "Image has been tagged as corrupted", new_error_kind="source_issue"
                )
                return False

            if self.is_at_date(year=2018, month="05", day=21):
                self.error_holder.add_error(
                    "Image is too dark", new_error_kind="source_issue"
                )
                return False

            img = self.source_image
            self.csv_data_holder.update_csv_dimensions(img, self.scale_width)

            if self.is_vis:
                res, self.mask = self._process_job_vis(img)
            elif self.is_nir:
                res, self.mask = self._process_job_nir(img)
            elif self.is_fluo:
                res, self.mask = self._process_job_fluo(img)
            else:
                self.mask = None
                res = False

            if not res:
                self.error_holder.add_error("Segmentation failed")

            if self.is_msp:
                pseudo_color_channel = "l"
            else:
                pseudo_color_channel = "v"
            pseudo_color_channel = kwargs.get(
                "pseudo_color_channel", pseudo_color_channel
            )

            if kwargs.get("threshold_only", 0) != 1:
                res = self.extract_image_data(self.mask, pseudo_color_channel)
            else:
                pseudo_color_img = self.draw_image(
                    channel=pseudo_color_channel, background="source"
                )
                self.store_image(pseudo_color_img, "pseudo_on")

            self.build_mosaic_data(**kwargs)
        except Exception as e:
            self.error_holder.add_error(f'Failed to process, because "{repr(e)}"')
            res = False

        self.print_images()
        return res

import os

import cv2
import numpy as np

from ipso_phen.ipapi.base.ip_abstract import BaseImageProcessor
from ipso_phen.ipapi.tools.common_functions import time_method, add_header_footer


class TpmpImageProcessorBrachy(BaseImageProcessor):
    @staticmethod
    def can_process(dict_data: dict) -> bool:
        """
        Checks if the class can process the image
        :param dict_data: Dictionary containing filter data
        :return: True if current class can process data
        """
        return dict_data["experiment"] in [
            "009s1709_sym",
            "011s1801_sym",
            "012s1801_sym",
            "013s1801_sym",
        ]

    def _calculate_senescence(self, src_img, plant_mask):
        """Calculates senescence area from plant mask

        :param src_img: Source image
        :param plant_mask: Plant mask
        """
        mask_, _ = self.get_mask(src_img, "a", 140, 255)
        mask_ = self.dilate(mask_, 3, cv2.MORPH_ELLIPSE)
        self.store_image(mask_, "mask_sene_dilate", self.rois_list)
        mask_ = cv2.bitwise_and(plant_mask, mask_)
        self.store_image(mask_, "mask_sene_only", self.rois_list)
        self.csv_data_holder.update_csv_value("senescence_area", np.sum(mask_ != 0))

    def _threshold_vis_blue_background(self, img):
        # Init
        self.init_standard_rois()

        # Grab selected masks
        mask_h, stored_name = self.get_mask(img, "h", 0, 100, (), False, 3)
        self.store_image(mask_h, stored_name, self.rois_list)
        mask_l, stored_name = self.get_mask(img, "l", 40, 255, (), False, 5)  # Pot
        self.store_image(mask_l, stored_name, self.rois_list)
        mask_b, stored_name = self.get_mask(img, "b", 115, 255, (), False, 3)
        self.store_image(mask_b, stored_name, self.rois_list)
        mask_gr, stored_name = self.get_mask(img, "gr", 35, 255, (), False, 3)  # Pot
        self.store_image(mask_gr, stored_name, self.rois_list)

        # Merge selected masks
        mask = self.multi_and([mask_h, mask_l, mask_b, mask_gr], True)
        self.store_image(mask, "mask", self.rois_list)
        self.mask = mask

        mask = self.erode(
            mask, 5, cv2.MORPH_ELLIPSE, self.get_rois({"erode"}), "ellipse"
        )
        self.store_image(mask, "mask_eroded", self.rois_list)

        # Apply all ROI at once
        mask = self.apply_rois(mask, "mask_roi_all")

        # Apply linked selection
        mask = self.keep_linked_contours(
            src_image=img.copy(),
            src_mask=mask,
            dilation_iter=10,
            tolerance_distance=67,
            tolerance_area=1003,
        )
        self.store_image(mask, "mask")
        self.mask = mask

        return mask

    def _threshold_vis_std(self, img):
        # Init
        self.init_standard_rois()

        if self.is_no_wb_fix:
            fwb_img = img.copy()  # self.apply_CLAHE(img)
            self.store_image(fwb_img, "clahe", self.rois_list)
        else:
            fwb_img = self.simplest_cb(img.copy(), [20, 40])
            self.store_image(fwb_img, "wb_fix", ())

        mask_b, stored_name = self.get_mask(
            fwb_img, "b", 135, 255, self.rois_list, False, 7
        )
        self.store_image(mask_b, stored_name, self.rois_list)
        mask_s, stored_name = self.get_mask(
            fwb_img, "s", 30, 255, self.rois_list, False, 5
        )
        self.store_image(mask_s, stored_name, self.rois_list)
        mask = cv2.bitwise_and(mask_b, mask_s)
        self.store_image(mask, "mask_b_and_s", self.rois_list)

        # Apply erosion to selected zones
        mask = self.erode(
            mask, 7, cv2.MORPH_ELLIPSE, self.get_rois({"erode"}), "ellipse"
        )
        self.store_image(mask, "mask_eroded", self.rois_list)

        # Apply all ROI at once
        mask = self.apply_rois(mask, "mask_roi_all")

        # Create safe zone mask and apply it to safe zone
        mask_s, stored_name = self.get_mask(
            fwb_img, "s", 30, 255, self.rois_list, False, 5
        )
        self.store_image(mask_s, stored_name, self.rois_list)
        mask_s = self.keep_rois(mask_s, ["safe"])
        self.store_image(mask_s, "mask_s_safe_only", self.rois_list)
        # mask_s = self.open(mask_s, 3, cv2.MORPH_ELLIPSE)
        # self.store_image(mask_s, 'mask_s_safe_opened', self.rois_list)
        mask = self.multi_or([mask, mask_s])
        self.store_image(mask, "mask_before_keep")

        mask = self.keep_linked_contours(
            src_image=fwb_img.copy(),
            src_mask=mask,
            dilation_iter=10,
            tolerance_distance=67,
            tolerance_area=1003,
        )
        self.store_image(mask, "mask")
        self.mask = mask

        if self.csv_data_holder.has_csv_key("senescence_area"):
            self._calculate_senescence(fwb_img, mask)

        return mask

    def _process_job_vis(self, img):
        """Applies visible pipeline to image

        Arguments:
            img {numpy array} -- source image

        Returns:
            boolean -- true if pipeline succeded
        """

        # Apply threshold
        if self.is_blue_background:
            return True, self._threshold_vis_blue_background(img)
        else:
            return True, self._threshold_vis_std(img)

    def _process_job_nir(self, img):
        """Processes image using NIR pipeline (NOT IMPLEMENTED)

        Arguments:
            img {numpy array} -- source image

        Returns:
            boolean -- always tru to avoid unneeded exceptions
        """
        self._mosaic_data, mosaic_image_ = self.build_channels_mosaic(
            img, self.rois_list
        )
        self.store_image(mosaic_image_, "full_channel_mosaic")
        return True, None

    def _threshold_fluo_std(self, img):
        # Init
        self.init_standard_rois()
        roi_main = self.get_roi("main_roi")
        roi_sticker = self.get_roi("roi_sticker")

        # Apply blur, some noisy images here
        median_blur_img = cv2.medianBlur(img, 5)
        self.store_image(median_blur_img, "median_blur", [roi_main])

        # self.print_channels(median_blur_img, [roi_main])

        # Build threshold mask
        # Prepare positive mask
        min_a, max_a = 155, 255
        mask_a, _ = self.get_mask(median_blur_img, "a", min_a, max_a)
        self.store_image(mask_a, "mask_rd_{}_{}".format(min_a, max_a), [roi_main])
        min_rd, max_rd = 93, 255
        mask_rd, _ = self.get_mask(median_blur_img, "rd", min_rd, max_rd)
        self.store_image(mask_rd, "mask_rd_{}_{}".format(min_rd, max_rd), [roi_main])
        mask = cv2.bitwise_or(mask_a, mask_rd)
        mask = self.keep_roi(mask, roi_main, "apply_sticker_roi_2_mask_a_rd")
        # Prepare negative mask
        min_bl, max_bl = 25, 255
        mask_bl, _ = self.get_mask(median_blur_img, "bl", min_bl, max_bl)
        # Clean
        mask_bl = self.keep_roi(mask_bl, roi_sticker, "mask_blue")
        mask_bl = 255 - mask_bl
        self.store_image(
            mask_bl, "mask_not_bl_{}_{}".format(min_bl, max_bl), [roi_main]
        )
        # Merge masks
        mask = cv2.bitwise_and(mask_bl, mask)
        self.store_image(mask, "mask_(a_or_rd)_and_bl", [roi_main])

        # Remove noisy contours
        mask = self.keep_linked_contours(
            src_image=median_blur_img,
            src_mask=mask,
            dilation_iter=10,
            tolerance_distance=84,
            tolerance_area=1298,
        )
        self.store_image(mask, "mask")
        self.mask = mask
        return mask

    def _threshold_fluo_low_light(self, img):
        # Init
        self.init_standard_rois()
        roi_main = self.get_roi("main_roi")

        # Apply blur, some noisy images here
        median_blur_img = cv2.medianBlur(img, 5)
        self.store_image(median_blur_img, "median_blur", [roi_main])

        self.print_channels(median_blur_img, [], False)
        self.print_channels(median_blur_img, [], True)

        # self.get_mask(median_blur_img, 'rd', 0, 255, [], False, 0, 'MinUp')#self.rois_list)

        # Keep channels
        min_a, max_a = 135, 255
        min_b, max_b = 160, 255
        min_v, max_v = 80, 255
        min_rd, max_rd = 50, 255
        mask_a, _ = self.get_mask(
            median_blur_img, "a", min_a, max_a, []
        )  # self.rois_list)
        mask_b, _ = self.get_mask(
            median_blur_img, "b", min_b, max_b, []
        )  # self.rois_list)
        mask_v, _ = self.get_mask(
            median_blur_img, "v", min_v, max_v, []
        )  # self.rois_list)
        mask_rd, _ = self.get_mask(
            median_blur_img, "rd", min_rd, max_rd, []
        )  # self.rois_list)

        # Delete channels
        min_gr, max_gr = 0, 85
        min_bl, max_bl = 0, 25
        mask_gr, _ = self.get_mask(
            median_blur_img, "gr", min_gr, max_gr, []
        )  # self.rois_list)
        mask_bl, _ = self.get_mask(
            median_blur_img, "bl", min_bl, max_bl, []
        )  # self.rois_list)

        mask = cv2.bitwise_or(mask_a, mask_b)
        mask = cv2.bitwise_or(mask, mask_v)
        mask = cv2.bitwise_or(mask, mask_rd)
        mask = cv2.bitwise_and(mask, mask_gr)
        mask = cv2.bitwise_and(mask, mask_bl)

        self.store_image(mask, "mask_output", self.rois_list)

        mask = self.keep_roi(mask, roi_main, "apply_roi_2_mask_output")

        # Remove noisy contours
        mask = self.keep_linked_contours(
            src_image=median_blur_img,
            src_mask=mask,
            dilation_iter=10,
            tolerance_distance=84,
            tolerance_area=1298,
        )
        self.store_image(mask, "mask")
        self.mask = mask
        return mask

    def _threshold_fluo_overexposed(self, img):
        # Init
        self.init_standard_rois()

        # Apply blur, some noisy images here
        median_blur_img = cv2.medianBlur(img, 5)
        self.store_image(median_blur_img, "median_blur")

        # Build threshold mask
        # Prepare negative mask
        min_bl, max_bl = 0, 25
        mask_bl, _ = self.get_mask(median_blur_img, "bl", min_bl, max_bl)
        # Prepare positive mask
        mask_r, _ = self.get_mask(median_blur_img, "rd", 135, 255)
        # Merge masks
        mask = cv2.bitwise_and(mask_bl, mask_r)
        self.store_image(mask, "mask_r_and_bl", self.rois_list)

        # Apply ROIs
        mask = self.apply_rois(mask, "mask")
        self.mask = mask

        return mask

    def _process_job_fluo(self, img):
        """Applies florescent pipeline to image

        Arguments:
            img {numpy array} -- source image

        Returns:
            boolean -- true if pipeline succeded
        """

        if self.is_low_light:
            return True, self._threshold_fluo_low_light(img)
        elif self.is_overexposed:
            return True, self._threshold_fluo_overexposed(img)
        else:
            return True, self._threshold_fluo_std(img)

    @add_header_footer
    @time_method
    def process_image(self, **kwargs):
        """Executes pipeline instructions to process image

        Raises:
            NotImplementedError -- Only VIS, FLUO are implemented

        Returns:
            boolean -- is job successful
        """

        threshold_only_ = kwargs.get("threshold_only", 0) == 1
        try:
            if self.is_corrupted:
                return False

            img = self.current_image
            self.csv_data_holder.update_csv_dimensions(img, self.scale_width)

            if self.is_vis:
                res, mask = self._process_job_vis(img)
            elif self.is_nir:
                res, mask = self._process_job_nir(img)
            elif self.is_fluo:
                res, mask = self._process_job_fluo(img)
            else:
                mask = None
                res = False

            if res and not threshold_only_:
                res = self.extract_image_data(mask)
            else:
                pseudo_color_channel = kwargs.get("pseudo_color_channel", "v")
                pseudo_color_img = self.draw_image(
                    channel=pseudo_color_channel, background="source"
                )
                self.store_image(pseudo_color_img, "pseudo_on")

        except Exception as e:
            self.error_holder.add_error(f'Failed to process image because "{repr(e)}"')
            res = False

        self.print_images()
        return res

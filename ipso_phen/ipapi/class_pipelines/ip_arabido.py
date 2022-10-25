import numpy as np
import cv2
import os

from ipso_phen.ipapi.base.ip_abstract import BaseImageProcessor
from ipso_phen.ipapi.tools.common_functions import time_method, force_directories


class TpmpImageProcessorArabido(BaseImageProcessor):
    @staticmethod
    def can_process(dict_data: dict) -> bool:
        """
        Checks if the class can process the image
        :param dict_data: Dictionnary containing filter data
        :return: True if current class can process data
        """
        return False  # dict_data['experiment'] in ['004c2711_dr', '007c2702_dr']

    def _write_images_output_mosaic(self):
        """Prints debug mosaic"""
        try:
            canvas = self.build_mosaic((1440, 2560, 3), self._mosaic_data)
            tmp_path = "{}{}".format(self.dst_path, "mosaics")
            tmp_path = os.path.join(tmp_path, "")
            force_directories(tmp_path)
            tmp_path = "{}{}.jpg".format(tmp_path, self.name)
            cv2.imwrite(tmp_path, canvas)
        except Exception as e:
            # Unsupported format detected
            print(
                'Exception: "{}" - Image: "{}", unsupported mosaic'.format(
                    repr(e), str(self)
                )
            )

    def _threshold_std(self, img):

        mosaic_line_1 = ["source"]
        mosaic_line_2 = []

        self.add_rect_roi(516, 1550, 270, 1454, "main_roi", "keep")

        mask_h, stored_name = self.get_mask(img, "h", 15, 60, self.rois_list, False)
        self.store_image(mask_h, stored_name, self.rois_list, mosaic_line_1)
        mask_h = self.open(mask_h, 5, cv2.MORPH_ELLIPSE, [], "mask_h")

        mask_b, stored_name = self.get_mask(img, "b", 215, 255, self.rois_list, True)
        self.store_image(mask_b, stored_name, self.rois_list, mosaic_line_1)
        mask_b = self.open(mask_b, 5, cv2.MORPH_ELLIPSE, [], "mask_b")

        mask_rd, stored_name = self.get_mask(img, "rd", 0, 225, self.rois_list, True)
        self.store_image(mask_rd, stored_name, self.rois_list, mosaic_line_1)
        mask_rd = self.open(mask_rd, 5, cv2.MORPH_ELLIPSE, [], "mask_rd")

        mask_and = cv2.bitwise_and(mask_h, mask_b)
        self.store_image(mask_and, "mask_h_and_b", self.rois_list, mosaic_line_2)
        mask_and = cv2.bitwise_and(mask_and, mask_rd)
        self.store_image(mask_and, "mask_and", self.rois_list, mosaic_line_2)

        mask_and = self.apply_rois(mask_and, "apply_roi")

        mask_erosion = self.erode(mask_and, 3, cv2.MORPH_ELLIPSE)
        self.store_image(mask_erosion, "mask_erosion", self.rois_list, mosaic_line_2)

        mask = self.keep_linked_contours(
            src_image=img,
            src_mask=mask_erosion,
            dilation_iter=5,
            tolerance_distance=-1,
            tolerance_area=4000,
        )
        self.store_image(mask, "mask", self.rois_list, mosaic_line_2)
        self.mask = mask

        return mask, [mosaic_line_1, mosaic_line_2], True

    def _threshold_and(self, img):

        mosaic_line_1 = ["source", "mask_hab"]

        self.add_rect_roi(516, 1550, 270, 1454, "main_roi", "keep")

        mask_h, stored_name = self.get_mask(img, "h", 20, 75, self.rois_list, False, 5)
        self.store_image(mask_h, stored_name, self.rois_list)

        mask_a, stored_name = self.get_mask(img, "a", 0, 130, self.rois_list, False, 5)
        self.store_image(mask_a, stored_name, self.rois_list)
        mask_b, stored_name = self.get_mask(
            img, "b", 130, 255, self.rois_list, False, 5
        )
        self.store_image(mask_b, stored_name, self.rois_list)

        mask = cv2.bitwise_and(mask_h, mask_a)
        self.store_image(mask, "mask_ha", self.rois_list)
        mask = cv2.bitwise_and(mask, mask_b)
        self.store_image(mask, "mask_hab", self.rois_list)

        return mask, [mosaic_line_1], False

    def _threshold_overexposed(self, img):

        mosaic_line_1 = ["source", "source", "source"]
        mosaic_line_2 = []

        self.add_rect_roi(890, 784, 654, 726, "main_roi", "keep")

        mask_h, stored_name = self.get_mask(img, "h", 0, 75, self.rois_list)
        self.store_image(mask_h, stored_name, self.rois_list)
        mask_b, stored_name = self.get_mask(img, "b", 125, 255, self.rois_list)
        self.store_image(mask_b, stored_name, self.rois_list)

        mask = cv2.bitwise_and(mask_h, mask_b)
        self.store_image(mask, "mask_h_and_b", self.rois_list, mosaic_line_2)

        mask = self.apply_rois(mask)
        self.store_image(mask, "mask_wth_roi", self.rois_list)

        mask = self.erode(mask, 3, cv2.MORPH_ELLIPSE, [], "", 2)
        self.store_image(mask, "mask_eroded_2_times", self.rois_list)
        mask = self.keep_linked_contours(
            src_image=img,
            src_mask=mask,
            tolerance_distance=25,
            tolerance_area=1500,
            root_position="MIDDLE_CENTER",
        )
        self.store_image(mask, "mask_final", self.rois_list, mosaic_line_2)
        mask = self.dilate(mask, 3, cv2.MORPH_ELLIPSE, [], "", 2)
        mask = self.close(mask, 3, cv2.MORPH_ELLIPSE, [], "", 2)
        self.store_image(mask, "mask_dilated_and_closed", self.rois_list, mosaic_line_2)

        return mask, [mosaic_line_1, mosaic_line_2], True

    @time_method
    def process_image(self, **kwargs):
        """Executes pipeline instructions to process image

        Returns:
            boolean -- is job successfull
        """

        threshold_only_ = kwargs.get("threshold_only", 0) == 1
        try:
            img = self.current_image

            if self.is_overexposed:
                mask, mosaic_lines, res = self._threshold_overexposed(img)
            # elif self.plant == 'p6_xcc_a1-93':
            #     mask, mosaic_lines, res = self._threshold_and(img)
            else:
                mask, mosaic_lines, res = self._threshold_std(img)

            if res and not threshold_only_:
                res = self.extract_image_data(mask)
                mosaic_lines[1].append("pseudo_on")
                mosaic_lines[1].append("shapes")

            self._mosaic_data = np.array(mosaic_lines)

        except Exception as e:
            print(
                'Failed to process image: "{}", because "{}"'.format(str(self), repr(e))
            )
            self.print_images()
            return False

        self.print_images()
        return res

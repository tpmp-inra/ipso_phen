import cv2
import os
import numpy as np

from ipso_phen.ipapi.base.ip_abstract import BaseImageProcessor
from ipso_phen.ipapi.tools.common_functions import (
    time_method,
    add_header_footer,
    force_directories,
)


class TpmpImageProcessorTabac(BaseImageProcessor):
    @staticmethod
    def can_process(dict_data: dict) -> bool:
        """
        Checks if the class can process the image
        :param dict_data: Dictionnary containing filter data
        :return: True if current class can process data
        """
        return dict_data["experiment"] in ["016s1803_nem"]

    def _write_images_output_mosaic(self):
        """Prints debug mosaic"""
        try:
            if self.is_vis:
                canvas = self.build_mosaic(
                    (1440, 2560, 3),
                    np.array(
                        [
                            [
                                "source",
                                "fix_wb_0_50",
                                "mask_vab",
                                "mask_erode_3_2_times",
                            ],
                            [
                                "mask_dilate_3_2_times",
                                "mask_rois_applyed",
                                "pseudo_on",
                                "shapes",
                            ],
                        ]
                    ),
                )
            elif self.is_fluo:
                canvas = self.build_mosaic((1440, 2560, 3), self._mosaic_data)
            elif self.is_nir:
                canvas = self.build_mosaic(
                    (1440, 2560, 3),
                    np.array(["source", "", "", "", "", "", "pseudo_on", "shapes"]),
                )
            else:
                raise NotImplementedError
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

    def _process_job_vis(self, img, **kwargs):
        """Applyes visible pipeline to image

        Arguments:
            img {numpy array} -- source image

        Returns:
            boolean -- true if pipeline succeded
        """

        try:
            self.add_rect_roi(372, 2002, 130, 1720, "main_roi", "keep")

            fwb_img = self.simplest_cb(img.copy(), [0, 50])
            self.store_image(fwb_img, "fix_wb_0_50", self.rois_list)
            # self.print_channels(fwb_img)

            # self.get_mask(fwb_img, 'v', 0, 255, [], False, 0, 'MinUp')
            # self.get_mask(fwb_img, 'v', 0, 255, [], False, 0, 'MaxDown')
            # self.get_mask(fwb_img, 'a', 0, 255, [], False, 0, 'MaxDown')
            # self.get_mask(fwb_img, 'b', 0, 255, [], False, 0, 'MinUp')

            # mask_v, _ = self.get_mask(fwb_img, 'v', 35, 250, self.rois_list)
            mask_a, _ = self.get_mask(fwb_img, "a", 0, 125, self.rois_list)
            mask_b, _ = self.get_mask(fwb_img, "b", 145, 255, self.rois_list)

            # mask_vab = cv2.bitwise_and(mask_v, mask_a)
            mask_vab = cv2.bitwise_and(mask_a, mask_b)
            self.store_image(mask_vab, "mask_vab", self.rois_list)

            mask_erod = self.erode(
                mask_vab, 3, cv2.MORPH_ELLIPSE, self.rois_list, "mask", 2
            )
            mask_dil = self.dilate(
                mask_erod, 3, cv2.MORPH_ELLIPSE, self.rois_list, "mask", 2
            )

            self.mask = self.apply_rois(mask_dil, "mask_rois_applyed")

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

            return True

        except Exception as e:
            print(
                'Failed to process VIS: "{}", because "{}"'.format(
                    repr(self.file_path), repr(e)
                )
            )
            return False

    def _process_job_nir(self, img, **kwargs):
        """Precesses image using NIR pipeline (NOT IMPLEMENTED)

        Arguments:
            img {numpy array} -- source image

        Returns:
            boolean -- always tru to avoid unneeded exceptions
        """

        try:
            self.print_channels(img)

            return True

        except Exception as e:
            print(
                'Failed to process NIR: "{}", because "{}"'.format(
                    repr(self.file_path), repr(e)
                )
            )
            return False

    def _process_job_fluo(self, img, **kwargs):
        """Applyes florescent pipeline to image

        Arguments:
            img {numpy array} -- source image

        Returns:
            boolean -- true if pipeline succeded
        """
        try:
            # Init
            self.add_rect_roi(169, 1213, 20, 983, "main_roi", "keep")

            mosaic_line_1 = ["source"]
            mosaic_line_2 = []

            # Build leaf extended mask
            mask_a_med, stored_img = self.get_mask(
                img, "a", 140, 255, self.rois_list, False, 15
            )
            self.store_image(mask_a_med, stored_img, self.rois_list, mosaic_line_1)

            # Build noisy leaf mask
            mask_a_coarse, stored_img = self.get_mask(
                img, "a", 145, 255, self.rois_list
            )
            self.store_image(mask_a_coarse, stored_img, self.rois_list, mosaic_line_1)

            # Merge masks and apply ROIs
            mask_holed = self.apply_rois(cv2.bitwise_and(mask_a_coarse, mask_a_med), "")
            self.store_image(mask_holed, "mask_a_clean", self.rois_list, mosaic_line_1)

            # Fill didease holes
            mask = self.fill_mask_holes(mask_holed)
            self.store_image(mask, "mask_fill", self.rois_list, mosaic_line_2)

            leafs_only_black = self.apply_mask(img, mask, "black")
            self.store_image(leafs_only_black, "leafs_only_black", [], mosaic_line_2)

            leafs_only_white = self.apply_mask(img, mask, "white")
            self.store_image(leafs_only_white, "leafs_only_white", [], mosaic_line_2)

            self._mosaic_data = np.array([mosaic_line_1, mosaic_line_2])

            return True

        except Exception as e:
            print(
                'Failed to process FLUO: "{}", because "{}"'.format(
                    self.file_path, repr(e)
                )
            )
            return False

    @add_header_footer
    @time_method
    def process_image(self, **kwargs):
        """Executes pipeline instructions to process image

        Raises:
            NotImplementedError -- Only VIS, FLUO are implemented

        Returns:
            boolean -- is job successfull
        """
        try:
            img = self.current_image

            if self.is_vis:
                result = self._process_job_vis(img, **kwargs)
            elif self.is_nir:
                result = self._process_job_nir(img, **kwargs)
            elif self.is_fluo:
                result = self._process_job_fluo(img, **kwargs)
            else:
                raise NotImplementedError

        except Exception as e:
            print(
                'Failed to process image: "{}", because "{}"'.format(
                    self.file_path, repr(e)
                )
            )
            self.print_images()
            return False

        self.print_images()

        return result

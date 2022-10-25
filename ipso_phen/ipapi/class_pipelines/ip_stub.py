import os
import numpy as np

import logging

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))

from ipso_phen.ipapi.base.ip_abstract import BaseImageProcessor
from ipso_phen.ipapi.base.ip_common import DefaultCsvWriter

_EXPERIMENT = "".lower()  # Put the name of the experiment attached to this pipeline


class IpStub(BaseImageProcessor):
    @staticmethod
    def can_process(dict_data: dict) -> bool:
        """
        Checks if the class can process the image
        :param dict_data: Dictionary containing filter data
        :return: True if current class can process data
        """
        return False and (dict_data["experiment"] in [_EXPERIMENT])

    def init_csv_writer(self):
        """
        Defines the variables that will be extracted from the image
        by default all possible variables are extracted, all variables are not always relevant

        Returns:
            DefaultCsvWriter -- [A holder to contain all data extracted]
        """
        return DefaultCsvWriter()

    def check_source(self):
        """
        Performs all tests needed to check if the image is valid

        Returns:
            bool -- True if image is valid
        """
        res = super().check_source()
        return res

    def init_csv_data(self, source_image):
        """
        Add all data not extracted from the image to the observation
        ex: genotypes, treatment, ...
        """
        pass

    def preprocess_source_image(self, **kwargs):
        """
        Apply pre-processing to image to fix exposure, white balance, ...
        Transformations will be taken into account when analysing image colors.
        IPSO Phen can generate code that can be directly pasted in this section.
        """
        pass

    def init_rois(self):
        """
        Initialize ROIs
        Depending on their tag some ROIs like crop will be automatically applied
        cf.BaseImageProcessor.add_roi family methods for more details.
        IPSO Phen can generate code that can be directly pasted in this section.
        """
        pass

    def build_channel_mask(self, source_image, **kwargs):
        """
            Build a coarse mask of the wanted object
            at the end of the method, self.mask must contain a binary 2D image.
            IPSO Phen can generate code that can be directly pasted in this section.

        Arguments:
            source_image {ndarray} -- Image resulting from all previous steps

        Returns:
            bool -- True if successful
        """
        try:
            pass
        except Exception as e:
            self.error_holder.add_error(
                f'Failed to build channel mask because "{repr(e)}"',
                target_logger=logger,
            )
            return False
        else:
            self.mask = None
            if self.mask is None:
                return False
            else:
                self.store_image(self.mask, "channel_mask", self.rois_list)
                return np.count_nonzero(self.mask) > 0

    def clean_mask(self, source_image):
        """
        Clean the coarse mask built in the previous step.
        IPSO Phen can generate code that can be directly pasted in this section.

        Arguments:
            source_image {ndarray} -- Image resulting from all previous steps

        Returns:
            bool -- True if successful
        """
        try:
            mask = self.mask
            self.store_image(mask, "mask")
        except Exception as e:
            self.error_holder.add_error(
                f'Failed to clean mask because "{repr(e)}"', target_logger=logger
            )
            return False
        else:
            self.store_image(mask, "mask")
            self.mask = mask
            if self.mask is None:
                return False
            else:
                return np.count_nonzero(self.mask) > 0

    def ensure_mask_zone(self):
        """
            Check that the mask corresponding to the object is where we expected\n
            All masks tagged "enforcer" will be automatically checked here

        Returns:
            bool -- True is mask is correctly positionned
        """
        mask = self.mask
        rois = self.get_rois({"enforce"})
        for roi in rois:
            mask = self.keep_roi(src_mask=mask, roi=roi)
            if np.count_nonzero(mask) == 0:
                return False
        return True

    def build_mosaic_data(self, **kwargs):
        """
            Use a ndarray to select which images will be used in the output mosaic\n
            names in the array must correspond to images built durring the process\n
            ex:  np.array([['source', 'src_img_with_cnt_after_agg_iter_last'], ['mask', 'pseudo_on']])
        Returns:
            ndarray -- images names
        """
        return True

    def update_analysis_params(self, **kwargs) -> dict:
        """
        Overrides parent to set boundary position, params expected:
            * background
            * foreground
            * pseudo_color_channel
            * boundary_position

        Returns:
            dict -- dictionnary containing analysis options
        """
        analysis_params = super().update_analysis_params(**kwargs)

        return analysis_params

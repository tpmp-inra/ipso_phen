import os
import pickle

import cv2
import numpy as np

from ipso_phen.ipapi.base.ip_abstract import BaseImageProcessor
from ipso_phen.ipapi.ipt.ipt_check_exposure import IptExposureChecker
from ipso_phen.ipapi.ipt.ipt_hough_circles_detector import IptHoughCircles
from ipso_phen.ipapi.ipt.ipt_linear_transformation import IptLinearTransformation
from ipso_phen.ipapi.tools.csv_writer import AbstractCsvWriter
from ipso_phen.ipapi.tools.common_functions import force_directories

_EXPERIMENT = "06ac_phenor_1901".lower()


class ImageCsvWriter(AbstractCsvWriter):
    def __init__(self):
        super().__init__()
        self.data_list = dict.fromkeys(
            [
                # Header - text values
                "experiment",
                "plant",
                "plant_id",
                "date_time",
                "genotype",
                "treatment",
                # Morphology
                "area",
                "hull_area",
                "shape_solidity",
                "shape_extend",
                "minimum_enclosing_circle",
                "rotated_bounding_rectangle",
                # Color descriptors
                "color_std_dev",
                "color_mean",
                # Chlorophyll data
                "chlorophyll_mean",
                "chlorophyll_std_dev",
            ]
        )


class Ip06acPhenor1901(BaseImageProcessor):
    @staticmethod
    def can_process(dict_data: dict) -> bool:
        """
        Checks if the class can process the image
        :param dict_data: Dictionary containing filter data
        :return: True if current class can process data
        """
        return dict_data["experiment"] in [_EXPERIMENT]

    def init_csv_writer(self):
        return ImageCsvWriter()

    def check_source(self):
        if self.is_color_checker:
            self.error_holder.add_error("HANDLED FAILURE color checker")
            return False

        # if self.is_msp and (self.retrieve_linked_images() != 8):
        #     self.error_holder.add_error(f'Wrong number of MSP files expected 8, received {self.retrieve_linked_images()}',
        #                                 new_error_kind='source_issue')
        #     return False

        if self.is_corrupted:
            self.error_holder.add_error(
                "Image has been tagged as corrupted", new_error_kind="source_issue"
            )
            return False

        return True

    def init_csv_data(self, source_image):
        _, genotype, *treatment_, plant_id_ = self.plant.split("_")
        self.csv_data_holder.update_csv_value("plant", self.plant)
        self.csv_data_holder.update_csv_value("plant_id", plant_id_)
        self.csv_data_holder.update_csv_value("genotype", genotype)
        self.csv_data_holder.update_csv_value(
            "treatment", "".join(treatment_) if len(treatment_) > 1 else treatment_[0]
        )

    def init_rois(self):
        folder_ = os.path.join(os.path.dirname(__file__), "stored_data/")
        pickled_file = f"{folder_}{self.name}_inneCircleRegion.pkl"
        force_directories(folder_)
        if os.path.isfile(pickled_file):
            with open(pickled_file, "rb") as f:
                circle = pickle.load(f)
        else:
            with IptHoughCircles(
                wrapper=self,
                min_radius=498,
                max_radius=598,
                max_peaks=4,
                line_width=20,
                keep_only_one=1,
                target_position="MIDDLE_CENTER",
                expand_circle=-40,
                operator="sobel",
                threshold=135,
            ) as (res, ed):
                if not res or not ed.result:
                    self.error_holder.add_error("Unable to detect circles")
                    circle = None
                else:
                    circles = sorted(ed.result, key=lambda circle_: circle_[2])
                    circle = circles[0]
                    with open(pickled_file, "wb") as f:
                        pickle.dump(circle, f)
        if circle is not None:
            self.add_circle_roi(
                left=circle[0],
                top=circle[1],
                radius=circle[2] - 20,
                name="pot_exterior",
                tag="none",
            )
            self.add_circle_roi(
                left=circle[0],
                top=circle[1],
                radius=circle[2] - 150,
                name="IptExposureChecker",
                tag="process_roi",
            )
            self.add_circle_roi(
                left=circle[0],
                top=circle[1],
                radius=circle[2] - 150,
                name="IptLinearTransformation",
                tag="process_roi",
            )
        else:
            self.error_holder.add_error("Unable to detect pot")
            radius_ = 500
            self.add_circle_roi(
                left=730 + radius_,
                top=484 + radius_,
                radius=radius_,
                name="pot_exterior",
                tag="none",
            )
        self.add_rect_roi(
            left=872,
            width=666,
            top=820,
            height=728,
            name="plant_guessed_position",
            tag="helper",
        )

    def _fix_source_image(self, img):
        if self.is_msp:
            # Fix brightness for darker images
            tmp_wrapper = BaseImageProcessor(self.file_path)
            with IptLinearTransformation(
                wrapper=tmp_wrapper,
                method="gamma_target",
                apply_case="if_under",
                target_brightness=75,
                max_delta_for_brightness=20,
            ) as (res, ed):
                if res:
                    return ed.result
        else:
            return img

    def preprocess_source_image(self, **kwargs):
        # Create outer image
        with IptExposureChecker(
            wrapper=self,
            overexposed_limit=215,
            over_color="blue",
            underexposed_limit=35,
            brg_calc="none",
            under_color="blue",
        ) as (res, ed):
            if res:
                outer_ = ed.result
            else:
                outer_ = self.current_image
        # Create inner image
        with IptExposureChecker(
            wrapper=self,
            over_color="none",
            under_color="blue",
            source_brightness="process_roi",
            average_as="average_as_lower",
            avg_weight=70,
        ) as (res, ed):
            if res:
                inner_ = ed.result
            else:
                inner_ = self.current_image

        outer_ = self.delete_roi(src_mask=outer_, roi="pot_exterior")
        inner_ = self.keep_roi(src_mask=inner_, roi="pot_exterior")

        ret = cv2.bitwise_or(outer_, inner_)
        self.store_image(ret, "preprocessed_image")

        return ret

    def build_channel_mask(self, source_image, **kwargs):
        try:
            mask = self.build_mask(
                source_image=source_image,
                is_store_images=True,
                merge_action="multi_and",
                params_list=[
                    dict(
                        channel="h",
                        max_t=105,
                        morph_op="open",
                        kernel_size=9,
                        proc_times=2,
                    ),
                    dict(
                        channel="b",
                        min_t=120,
                        morph_op="open",
                        kernel_size=7,
                        proc_times=2,
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
            mask = self.keep_linked_contours(
                src_image=source_image,
                tolerance_distance=30,
                tolerance_area=1861,
                root_position="MIDDLE_CENTER",
                dilation_iter=-3,
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
        mask = self.keep_roi(mask, "plant_guessed_position")
        return np.count_nonzero(mask) > 0

    def build_mosaic_data(self, **kwargs):
        return True

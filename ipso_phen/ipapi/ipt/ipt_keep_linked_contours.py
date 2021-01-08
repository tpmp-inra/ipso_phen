import logging
import os

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))
from ipso_phen.ipapi.base.ipt_abstract import IptBase
from ipso_phen.ipapi.base.ip_common import ToolFamily


class IptKeepLinkedContours(IptBase):
    def build_params(self):
        self.add_spin_box(
            name="tolerance_distance",
            desc="Allowed distance to main contour",
            default_value=100,
            minimum=0,
            maximum=5000,
        )
        self.add_spin_box(
            name="tolerance_area",
            desc="Min contour area size",
            default_value=5000,
            minimum=2,
            maximum=50000,
        )
        self.add_combobox(
            name="root_position",
            desc="Root contour position",
            default_value="BOTTOM_CENTER",
            values=dict(
                TOP_LEFT="TOP_LEFT",
                TOP_CENTER="TOP_CENTER",
                TOP_RIGHT="TOP_RIGHT",
                MIDDLE_LEFT="MIDDLE_LEFT",
                MIDDLE_CENTER="MIDDLE_CENTER",
                MIDDLE_RIGHT="MIDDLE_RIGHT",
                BOTTOM_LEFT="BOTTOM_LEFT",
                BOTTOM_CENTER="BOTTOM_CENTER",
                BOTTOM_RIGHT="BOTTOM_RIGHT",
            ),
        )
        self.add_slider(
            name="dilation_iter",
            desc="Erosion/dilation iterations (kernel size 3)",
            default_value=0,
            minimum=-100,
            maximum=100,
        )
        self.add_spin_box(
            name="area_override_size",
            desc="Include all contours bigger than",
            default_value=0,
            minimum=0,
            maximum=50000,
        )
        self.add_spin_box(
            name="delete_all_bellow",
            desc="Delete all contours smaller than",
            default_value=0,
            minimum=0,
            maximum=50000,
            hint="The more smaller contours are delete, the faster the algorithm",
        )
        self.add_text_input(
            name="safe_roi_name",
            desc="Safe ROI name",
            default_value="",
        )
        self.add_checkbox(
            name="keep_safe_close_enough",
            desc="Keep close contours inside safe ROI",
            default_value=0,
            hint="If a contour is inside the safe zone keep it if it's close enough regardless of size",
        )
        self.add_checkbox(
            name="keep_safe_big_enough",
            desc="Keep big contours inside safe ROI",
            default_value=0,
            hint="If a contour is inside the safe zone keep it if it's big enough regardless of distance",
        )
        self.add_channel_selector(default_value="l", desc="Pseudo color channel")

    def process_wrapper(self, **kwargs):
        """
        Keep linked Contours:
        Keeps contours related to the main object, removes the others
        Needs to be part of a pipeline where a mask has already been generated
        Real time : False

        Keyword Arguments (in parentheses, argument name):
            * Allowed distance to main contour (tolerance_distance):
            * Min contour area size (tolerance_area):
            * Root contour position (root_position):
            * Erosion/dilation iterations (kernel size 3) (dilation_iter):
            * Include all contours bigger than (area_override_size):
            * Delete all contours smaller than (delete_all_bellow): The more small contours are delete, the faster the algorithm
            * Pseudo color channel (channel):
        """
        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return False

        tolerance_distance = self.get_value_of("tolerance_distance")
        tolerance_area = self.get_value_of("tolerance_area")
        root_position = self.get_value_of("root_position")
        dilation_iter = self.get_value_of("dilation_iter")
        channel = self.get_value_of("channel")
        area_override_size = self.get_value_of("area_override_size")
        delete_all_bellow = self.get_value_of("delete_all_bellow")

        try:
            img = self.wrapper.current_image
            mask = self.get_mask()
            if mask is None:
                logger.error(f"FAIL {self.name}: mask must be initialized")
                return

            self.result = wrapper.keep_linked_contours(
                src_image=wrapper.current_image,
                src_mask=mask,
                dilation_iter=dilation_iter,
                tolerance_distance=tolerance_distance,
                tolerance_area=tolerance_area,
                root_position=root_position,
                area_override_size=area_override_size,
                delete_all_bellow=delete_all_bellow,
                safe_roi_name=self.get_value_of("safe_roi_name"),
                keep_safe_close_enough=self.get_value_of("keep_safe_close_enough") == 1,
                keep_safe_big_enough=self.get_value_of("keep_safe_big_enough") == 1,
            )
            wrapper.store_image(self.result, "mask", text_overlay=False)
            self.demo_image = wrapper.retrieve_stored_image(
                "src_img_with_cnt_after_agg_iter_last"
            )

            res = True
        except Exception as e:
            logger.error(f'Failed to process {self. name}: "{repr(e)}"')
            return False
        else:
            return res

    @property
    def name(self):
        return "Keep linked Contours"

    @property
    def real_time(self):
        return False

    @property
    def result_name(self):
        return "mask"

    @property
    def output_kind(self):
        return "mask"

    @property
    def use_case(self):
        return [ToolFamily.MASK_CLEANUP]

    @property
    def description(self):
        return "Keeps contours related to the main object, removes the others.\nNeeds to be part of a pipeline where a mask has already been generated"

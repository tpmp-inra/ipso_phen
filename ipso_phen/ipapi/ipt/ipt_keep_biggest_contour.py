import logging
import os

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))
from ipso_phen.ipapi.base.ipt_abstract import IptBase
from ipso_phen.ipapi.base.ip_common import ToolFamily


class IptKeepBiggestContours(IptBase):
    def build_params(self):
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
        self.add_channel_selector(default_value="l", desc="Pseudo color channel")

    def process_wrapper(self, **kwargs):
        """
        Keep Biggest Contours:
        Keeps the contours inside the biggest one.
        Needs to be part of a pipeline where a mask has already been generated
        Real time : False

        Keyword Arguments (in parentheses, argument name):
            * Root contour position (root_position):
            * Erosion/dilation iterations (kernel size 3) (dilation_iter):
            * Pseudo color channel (channel):
        """

        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return False

        root_position = self.get_value_of("root_position")
        dilation_iter = self.get_value_of("dilation_iter")
        channel = self.get_value_of("channel")

        try:
            img = self.wrapper.current_image
            mask = self.get_mask()
            if mask is None:
                logger.error(f"FAIL {self.name}: mask must be initialized")
                return

            params_as_str = self.input_params_as_str(exclude_defaults=True)

            self.result = wrapper.keep_biggest_contour(
                src_image=wrapper.current_image,
                src_mask=mask,
                dilation_iter=dilation_iter,
                root_position=root_position,
            )
            wrapper.store_image(self.result, "mask", text_overlay=False)

            self.demo_image = wrapper.retrieve_stored_image(img_name="img_wth_tagged_cnt")

            res = wrapper.ensure_mask_zone()
            if not res:
                logger.error("HANDLED FAILURE Mask not where expected to be")
        except Exception as e:
            logger.error(f'Failed to process {self. name}: "{repr(e)}"')
            return False
        else:
            return res

    @property
    def name(self):
        return "Keep Biggest Contours"

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
        return "Keeps the contours inside the biggest one.\nNeeds to be part of a pipeline where a mask has already been generated"

import logging
import os

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))

from ipso_phen.ipapi.base.ipt_abstract import IptBase
from ipso_phen.ipapi.tools.regions import CompositeRegion, EmptyRegion


class IptRoiComposition(IptBase):
    def build_params(self):
        self.add_roi_settings(default_name="unnamed_roi", default_type="keep")
        self.add_enabled_checkbox()
        self.add_roi_selector()
        self.add_combobox(
            name="op",
            desc="Composition method",
            default_value="intersection",
            values={
                "intersection": "Intersection of ROIs",
                "union": "Union of ROIs",
            },
        )

    def process_wrapper(self, **kwargs):
        """
        ROI composition:
        Create an ROI by composing other ROIs
        Real time: True

        Keyword Arguments (in parentheses, argument name):
            * ROI name (roi_name):
            * Select action linked to ROI (roi_type): no clue
            * Target IPT (tool_target): no clue
            * Activate tool (enabled): Toggle whether or not tool is active
            * Name of ROI to be used (roi_names): Operation will only be applied inside of ROI
            * ROI selection mode (roi_selection_mode):
            * Composition method (op):
        """

        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return False

        res = False
        try:
            if self.get_value_of("enabled") == 1:
                self.result = self.generate_roi()
                if self.result is not None:
                    img = self.result.draw_to(
                        dst_img=wrapper.current_image, line_width=wrapper.width // 200
                    )
                else:
                    img = wrapper.current_image
                self.demo_image = img
                wrapper.store_image(image=img, text="image_with_roi")

                res = True
            else:
                wrapper.store_image(wrapper.current_image, "current_image")
                res = True
        except Exception as e:
            res = False
            wrapper.error_holder.add_error(
                f"ROI composition FAILED, exception: {repr(e)}", target_logger=logger
            )
        else:
            pass
        finally:
            return res

    def generate_roi(self, **kwargs):
        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return EmptyRegion()

        return CompositeRegion(
            items=self.get_ipt_roi(
                wrapper=wrapper,
                roi_names=self.get_value_of("roi_names").replace(" ", "").split(","),
                selection_mode=self.get_value_of("roi_selection_mode"),
            ),
            name=self.get_value_of("roi_name"),
            op=self.get_value_of("op"),
            width=wrapper.width,
            height=wrapper.height,
        )

    @property
    def name(self):
        return "ROI composition"

    @property
    def package(self):
        return "TPMP"

    @property
    def real_time(self):
        return True

    @property
    def result_name(self):
        return "None"

    @property
    def output_kind(self):
        return "None"

    @property
    def use_case(self):
        return ["Create an ROI"]

    @property
    def description(self):
        return "Create an ROI by composing other ROIs"

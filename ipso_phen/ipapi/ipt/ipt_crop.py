import cv2

from ipso_phen.ipapi.base.ipt_abstract_analyzer import IptBaseAnalyzer
from ipso_phen.ipapi.base import ip_common as ipc
import ipso_phen.ipapi.tools.regions as regions

import logging

logger = logging.getLogger(__name__)


class IptCrop(IptBaseAnalyzer):
    def build_params(self):
        self.add_enabled_checkbox()
        self.add_combobox(
            name="source_selector",
            desc="Select source",
            default_value="current_image",
            values={
                "current_image": "Current image",
                "mask": "Mask",
            },
            hint="Select which image will be used as source",
        )
        self.add_text_input(
            name="roi_name",
            desc="Name of ROI to be used",
            default_value="",
            hint="Crop Image/mask to ROI, only one ROI accepted",
        )

    def process_wrapper(self, **kwargs):
        """
        Crop:
        'Crop image or mask to rectangular ROI
        Real time: True

        Keyword Arguments (in parentheses, argument name):
            * Activate tool (enabled): Toggle whether or not tool is active
            * Select source (source_selector): Select which image will be used as source
            * Name of ROI to be used (roi_name): Crop Image/mask to ROI, only one ROI accepted
        """
        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return False

        res = False
        try:
            if self.get_value_of("enabled") == 1:
                # Get Source
                input_kind = self.get_value_of("source_selector")
                if input_kind == "mask":
                    img = self.get_mask()
                elif input_kind == "current_image":
                    img = wrapper.current_image
                else:
                    img = None
                    logger.error(f"Unknown source: {input_kind}")
                    self.result = None
                    return

                # Get ROI
                roi_list = self.get_ipt_roi(
                    wrapper=wrapper,
                    roi_names=self.get_value_of("roi_name").replace(" ", "").split(","),
                    selection_mode="all_named",
                )
                if len(roi_list) <= 0:
                    logger.warning("No ROI detected, will return source image")
                elif len(roi_list) > 1:
                    logger.warning("Multiple ROIs detected, first one will be used")
                if len(roi_list) <= 0:
                    roi = None
                elif isinstance(roi_list[0], regions.RectangleRegion):
                    roi: regions.RectangleRegion = roi_list[0]
                else:
                    logger.warning("ROI has been converted to rectangle rectangle")
                    roi: regions.RectangleRegion = roi_list[0].as_rect()

                # Crop image
                if roi is not None:
                    img = roi.crop(src_image=img)

                # Finalize
                wrapper.store_image(img, "cropped_image")
                self.demo_image = img
                self.result = img
                res = True

            else:
                wrapper.store_image(wrapper.current_image, "current_image")
                res = True
        except Exception as e:
            res = False
            logger.error(f"Crop FAILED, exception: {repr(e)}")
        else:
            pass
        finally:
            return res

    @property
    def name(self):
        return "Crop"

    @property
    def package(self):
        return "TPMP"

    @property
    def real_time(self):
        return True

    @property
    def result_name(self):
        return "image"

    @property
    def output_kind(self):
        return "image"

    @property
    def use_case(self):
        return [ipc.ToolFamily.PRE_PROCESSING]

    @property
    def description(self):
        return """'Crop image or mask to rectangular ROI"""

    @property
    def input_type(self):
        if self.get_value_of("source_selector") == "mask":
            return ipc.IO_MASK
        else:
            return ipc.IO_IMAGE

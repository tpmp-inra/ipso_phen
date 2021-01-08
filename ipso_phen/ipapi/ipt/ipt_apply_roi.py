import logging
import os

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))

from ipso_phen.ipapi.base.ipt_abstract import IptBase
import ipso_phen.ipapi.base.ip_common as ipc
import ipso_phen.ipapi.tools.regions as regions


class IptApplyRoi(IptBase):
    def build_params(self):
        self.add_enabled_checkbox()
        self.add_roi_selector()
        self.add_combobox(
            name="roi_type",
            desc="Select action",
            default_value="keep",
            values=dict(
                keep="Keep region inside ROI",
                delete="Delete region inside ROI",
                crop="Crop image to ROI (most tools don not support this option)",
            ),
        )
        self.add_checkbox(
            name="erase_outside",
            desc="Erase contents outside ROI if cropping with not rectangular shape",
            default_value=1,
        )
        self.add_combobox(
            name="io_mode",
            desc="Select target",
            default_value="mask",
            values={"image": "Image", "mask": "Mask"},
        )

    def process_wrapper(self, **kwargs):
        """
        Apply ROI:
        Apply selected ROI to image/mask
        ROI can be of type "keep", "delete", "erode", "dilate", "open", "close"
        Select correct IO type for pipeline use
        Real time: True

        Keyword Arguments (in parentheses, argument name):
            * Activate tool (enabled): Toggle whether or not tool is active
            * Name of ROI to be used (roi_names): Operation will only be applied inside of ROI
            * ROI selection mode (roi_selection_mode):
            * Select action (roi_type):
            * Erase contents outside ROI if cropping with not rectangular shape (erase_outside):
            * Select target (io_mode):
        """
        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return False

        res = False
        try:
            if self.get_value_of("enabled") == 1:
                io_mode = self.get_value_of("io_mode")
                if io_mode == "image":
                    img = wrapper.current_image
                elif io_mode == "mask":
                    img = self.get_mask()
                else:
                    img = None
                if img is None:
                    logger.error(f"FAIL {self.name}: mask must be initialized")
                    return

                # Retrieve ROIs
                rois = self.get_ipt_roi(
                    wrapper=wrapper,
                    roi_names=self.get_value_of("roi_names").replace(" ", "").split(","),
                    selection_mode=self.get_value_of("roi_selection_mode"),
                )
                roi_type = self.get_value_of("roi_type")
                if roi_type not in [
                    "keep",
                    "delete",
                    "erode",
                    "dilate",
                    "open",
                    "close",
                ]:
                    return
                erase_outside = self.get_value_of("erase_outside") == 1
                for roi in rois:
                    if roi_type == "keep":
                        img = roi.keep(img)
                    elif roi_type == "delete":
                        img = roi.delete(img)
                    elif roi_type == "crop":
                        img = roi.crop(img, erase_outside_if_not_rect=erase_outside)
                    wrapper.store_image(image=img, text=f"image_after{roi.name}")
                self.result = img
                wrapper.store_image(img, "roi_applied")
                self.demo_image = regions.draw_rois(
                    rois=rois, image=img.copy(), line_width=wrapper.width // 400
                )
                res = True
            else:
                wrapper.store_image(wrapper.current_image, "current_image")
                res = True
        except Exception as e:
            res = False
            logger.error(f'Failed to process {self. name}: "{repr(e)}"')
        else:
            pass
        finally:
            return res

    def apply_test_values_overrides(self, use_cases: tuple = ()):
        if ipc.ToolFamily.PRE_PROCESSING in use_cases:
            self.set_value_of("io_mode", "image")
        elif ipc.ToolFamily.MASK_CLEANUP in use_cases:
            self.set_value_of("io_mode", "mask")

    @property
    def name(self):
        return "Apply ROI"

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
        return [ipc.ToolFamily.PRE_PROCESSING, ipc.ToolFamily.MASK_CLEANUP]

    @property
    def description(self):
        return 'Apply selected ROI to image/mask\nROI can be of type "keep", "delete", "erode", "dilate", "open", "close"\n Select correct IO type for pipeline use'

    @property
    def input_type(self):
        ot = self.get_value_of("io_mode")
        if ot == "mask":
            return ipc.IO_MASK
        elif ot == "image":
            return ipc.IO_IMAGE
        else:
            return ipc.IO_NONE

    @property
    def output_type(self):
        ot = self.get_value_of("io_mode")
        if ot == "mask":
            return ipc.IO_MASK
        elif ot == "image":
            return ipc.IO_IMAGE
        else:
            return ipc.IO_NONE

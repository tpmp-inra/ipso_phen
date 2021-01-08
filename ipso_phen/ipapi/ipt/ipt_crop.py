import os
import cv2

from ipso_phen.ipapi.base.ipt_abstract_analyzer import IptBaseAnalyzer
from ipso_phen.ipapi.tools.common_functions import force_directories
from ipso_phen.ipapi.file_handlers.fh_base import file_handler_factory
from ipso_phen.ipapi.base import ip_common as ipc
import ipso_phen.ipapi.tools.regions as regions

import logging

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))


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
        self.add_checkbox(
            name="grab_linked_images",
            desc="Add linked images",
            default_value=0,
            hint="Crop also all linked images",
        )
        self.add_checkbox(
            name="save_image",
            desc="Save generated image",
            default_value=0,
        )
        self.add_text_input(
            name="img_name",
            desc="Name in csv",
            default_value="img",
        )
        self.add_file_naming()
        self.add_text_input(
            name="roi_name",
            desc="Name of ROI to be used",
            default_value="",
            hint="Crop Image/mask to ROI, only one ROI accepted",
        )
        self.add_spin_box(
            name="fixed_width",
            desc="Resize images to width",
            default_value=0,
            minimum=0,
            maximum=10000,
        )
        self.add_spin_box(
            name="fixed_height",
            desc="Resize images to height",
            default_value=0,
            minimum=0,
            maximum=10000,
        )
        self.add_checkbox(
            name="store_transformation",
            desc="Store transformation",
            default_value=1,
            hint="Store transformation so it will be applied to linked images",
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
                    roi: regions.RectangleRegion = roi_list[0].as_rect()

                # Crop image
                additional_images = {}
                if roi is not None:
                    if self.get_value_of("store_transformation") == 1:
                        wrapper.image_transformations.append(
                            {
                                "action": "crop",
                                "roi": roi,
                                "fixed_width": self.get_value_of("fixed_width"),
                                "fixed_height": self.get_value_of("fixed_height"),
                            }
                        )
                    self.result = roi.crop(
                        src_image=img,
                        fixed_width=self.get_value_of("fixed_width"),
                        fixed_height=self.get_value_of("fixed_height"),
                    )
                    if self.get_value_of("grab_linked_images") == 1:
                        for lnk_img in wrapper.file_handler.linked_images:
                            try:
                                fh = file_handler_factory(
                                    lnk_img,
                                    database=wrapper.target_database,
                                )
                                additional_images[fh.view_option] = roi.crop(
                                    src_image=fh.load_source_file(),
                                    fixed_width=self.get_value_of("fixed_width"),
                                    fixed_height=self.get_value_of("fixed_height"),
                                )
                                wrapper.store_image(
                                    image=additional_images[fh.view_option],
                                    text=f"{fh.view_option}_crop",
                                )
                            except Exception as e:
                                logger.error(f"Unable to process image because {repr(e)}")

                else:
                    self.result = img

                # Finalize
                if self.get_value_of("save_image") != 0:
                    self.save_images(additional_images=additional_images, **kwargs)
                wrapper.store_image(self.result, "cropped_image")
                self.demo_image = self.result
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
        return [
            ipc.ToolFamily.PRE_PROCESSING,
            ipc.ToolFamily.IMAGE_GENERATOR,
        ]

    @property
    def description(self):
        return """'Crop image or mask to rectangular ROI"""

    @property
    def input_type(self):
        return (
            ipc.IO_MASK
            if self.get_value_of("source_selector") == "mask"
            else ipc.IO_IMAGE
        )

    @property
    def output_type(self):
        return ipc.IO_IMAGE

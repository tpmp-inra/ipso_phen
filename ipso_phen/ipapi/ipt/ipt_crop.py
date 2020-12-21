import os
import cv2

from ipso_phen.ipapi.base.ipt_abstract_analyzer import IptBaseAnalyzer
from ipso_phen.ipapi.tools.common_functions import force_directories
from ipso_phen.ipapi.file_handlers.fh_base import file_handler_factory
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
                additional_images = {}
                if roi is not None:
                    fixed_width = self.get_value_of("fixed_width")
                    if (fixed_width != 0) and (fixed_width != roi.width):
                        width_delta = fixed_width - roi.width
                        dl = width_delta // 2
                        dr = width_delta // 2 + (1 if width_delta % 2 != 0 else 0)
                    else:
                        dl = 0
                        dr = 0
                    fixed_height = self.get_value_of("fixed_height")
                    if (fixed_height != 0) and (fixed_height != roi.width):
                        height_delta = fixed_height - roi.width
                        dt = height_delta // 2
                        db = height_delta // 2 + (1 if height_delta % 2 != 0 else 0)
                    else:
                        dt = 0
                        db = 0
                    new_roi = roi.copy()
                    new_roi.inflate(dl=dl, dr=dr, dt=dt, db=db)

                    self.result = new_roi.crop(src_image=img)
                    if self.get_value_of("grab_linked_images") == 1:
                        for lnk_img in wrapper.file_handler.linked_images:
                            try:
                                fh = file_handler_factory(
                                    lnk_img,
                                    database=wrapper.target_database,
                                )
                                additional_images[fh.view_option] = new_roi.crop(
                                    src_image=fh.load_source_file()
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
                    dst_path = self.build_output_filename()
                    self.add_value(
                        key=self.get_value_of("img_name"),
                        value=os.path.basename(dst_path),
                        force_add=True,
                    )
                    force_directories(self.output_path)
                    cv2.imwrite(filename=dst_path, img=self.result)
                    # Add linked images
                    if (
                        self.get_value_of("grab_linked_images") == 1
                    ) and additional_images:
                        file_ext = (
                            wrapper.file_handler.file_ext
                            if self.get_value_of("output_format") == "source"
                            else f".{self.get_value_of('output_format')}"
                        )
                        base_name, _ = os.path.splitext(os.path.basename(dst_path))
                        root_folder = os.path.join(os.path.dirname(dst_path), "")

                        for k, v in additional_images.items():
                            self.add_value(
                                key=f'{self.get_value_of("img_name")}_{k}',
                                value=f"{base_name}_{k}{file_ext}",
                                force_add=True,
                            )
                            cv2.imwrite(
                                filename=os.path.join(
                                    root_folder, f"{base_name}_{k}{file_ext}"
                                ),
                                img=v,
                            )
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
        return ipc.IO_IMAGE if self.get_value_of("save_image") == 0 else ipc.IO_DATA

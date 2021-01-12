import os

import logging

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))

import cv2

from ipso_phen.ipapi.base.ipt_abstract_analyzer import IptBaseAnalyzer
from ipso_phen.ipapi.tools.common_functions import force_directories
from ipso_phen.ipapi.base import ip_common as ipc
from ipso_phen.ipapi.tools import regions


class IptCopyOrRenameImage(IptBaseAnalyzer):
    def build_params(self):
        self.add_enabled_checkbox()
        self.add_combobox(
            name="source_image",
            desc="Image to copy",
            default_value="source",
            values=dict(
                source="Source image",
                custom="Select from name below",
            ),
        )
        self.add_text_input(
            name="named_source",
            desc="Custom image name",
            default_value="mask",
        )
        self.add_file_naming()
        self.add_roi_selector()
        self.add_separator(name="sep1")
        self.add_spin_box(
            name="max_width",
            desc="Resize images if with is larger than",
            default_value=0,
            minimum=0,
            maximum=10000,
        )
        self.add_spin_box(
            name="max_height",
            desc="Resize images if height is larger than",
            default_value=0,
            minimum=0,
            maximum=10000,
        )
        self.add_checkbox(name="kar", desc="Keep aspect ratio", default_value=1)

    def process_wrapper(self, **kwargs):
        """
        Copy or rename image:
        Copies an image, renaming it if needed
        Real time: False

        Keyword Arguments (in parentheses, argument name):
            * Activate tool (enabled): Toggle whether or not tool is active
            * Target folder (path): Can be overridden at process call
            * Image to copy (source_image):
            * Custom image name (named_source):
            * Image output format (output_format):
            * Output naming convention (output_name):
            * Prefix or suffix (prefix_suffix):
            * Name of ROI to be used (roi_names): Operation will only be applied inside of ROI
            * ROI selection mode (roi_selection_mode):
            * Resize images if with is larger than (max_width):
            * Resize images if height is larger than (max_height):
            * Keep aspect ratio (kar):
        """

        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return False

        res = False
        try:
            self.data_dict = {}
            if self.get_value_of("enabled") == 1:
                # Get source image
                source = self.get_value_of("source_image")
                var_name = source
                if source == "source":
                    img = wrapper.source_image
                elif source == "custom":
                    var_name = self.get_value_of("named_source")
                    img = wrapper.retrieve_stored_image(var_name)
                else:
                    img = None
                    logger.error(f"Copy or rename image FAILED, unknown source: {source}")
                    return
                if img is None:
                    logger.error(f"Copy or rename image FAILED, missing source: {source}")
                    return

                # Apply ROIs
                rois = self.get_ipt_roi(
                    wrapper=wrapper,
                    roi_names=self.get_value_of("roi_names").replace(" ", "").split(","),
                    selection_mode=self.get_value_of("roi_selection_mode"),
                )
                img = wrapper.apply_roi_list(img=img, rois=rois)

                dst_path = self.build_output_path()

                # Add image to list
                wrapper.store_image(image=img, text="copied_or_renamed_image")

                # Add data
                self.add_value(key="source_name", value=wrapper.name, force_add=True)
                if "image" not in var_name:
                    var_name += "_image"
                self.add_value(key=var_name, value=dst_path, force_add=True)

                # Resize if needed
                max_width = self.get_value_of("max_width")
                max_height = self.get_value_of("max_height")
                kar = self.get_value_of("kar") == 1

                if max_width != 0 and max_height != 0:
                    r = regions.RectangleRegion(width=max_width, height=max_height)
                elif max_width == 0 and max_height != 0:
                    r = regions.RectangleRegion(width=wrapper.width, height=max_height)
                elif max_width != 0 and max_height == 0:
                    r = regions.RectangleRegion(width=max_width, height=wrapper.height)
                else:
                    r = None
                if r is not None:
                    img = ipc.resize_image(
                        src_img=img, target_rect=r, keep_aspect_ratio=kar
                    )

                # Copy image
                force_directories(self.output_path)
                cv2.imwrite(filename=dst_path, img=img)
                res = True
            else:
                wrapper.store_image(wrapper.current_image, "current_image")
                res = True
        except Exception as e:
            res = False
            logger.exception(f'Failed to process {self. name}: "{repr(e)}"')
        else:
            pass
        finally:
            self.result = res
            return res

    @property
    def name(self):
        return "Copy or rename image"

    @property
    def package(self):
        return "IPSO_Phen"

    @property
    def real_time(self):
        return False

    @property
    def result_name(self):
        "dictionary"

    @property
    def output_kind(self):
        "dictionary"

    def apply_test_values_overrides(self, use_cases: tuple = ()):
        self.output_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "test",
            "output_files",
            "",
        )

    @property
    def use_case(self):
        return [ipc.ToolFamily.IMAGE_GENERATOR]

    @property
    def description(self):
        return "Copies an image, renaming it if needed"

    @property
    def required_images(self):
        return (
            [self.get_value_of("named_source")]
            if self.get_value_of("source_image") == "custom"
            else []
        )

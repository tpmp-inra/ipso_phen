import os

import logging

logger = logging.getLogger(__name__)

import cv2

from base.ipt_abstract_analyzer import IptBaseAnalyzer
from tools.common_functions import force_directories
from base import ip_common as ipc
from tools import regions


class IptCopyOrRenameImage(IptBaseAnalyzer):
    def build_params(self):
        self.add_enabled_checkbox()
        self.add_text_input(
            name="path",
            desc="Target folder",
            default_value="",
            hint="Can be overridden at process call",
        )
        self.add_combobox(
            name="source_image",
            desc="Image to copy",
            default_value="source",
            values=dict(
                source="Source image",
                fixed="Fixed image",
                preprocessed="Pre processed image",
                custom="Select from name below",
            ),
        )
        self.add_text_input(
            name="named_source", desc="Custom image name", default_value="mask",
        )
        self.add_combobox(
            name="output_format",
            desc="Image output format",
            default_value="source",
            values=dict(source="As source image", jpg="JPEG", png="PNG", tiff="TIFF"),
        )
        self.add_combobox(
            name="output_name",
            desc="Output naming convention",
            default_value="as_source",
            values=dict(
                as_source="Same as source",
                hash="Use hash for anonymous names",
                suffix="Add suffix to name",
                prefix="Add prefix to name",
            ),
        )
        self.add_text_input(
            name="prefix_suffix", desc="Prefix or suffix", default_value="",
        )
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
                elif source == "fixed":
                    img = wrapper.retrieve_stored_image("exposure_fixed")
                elif source == "preprocessed":
                    img = wrapper.retrieve_stored_image("pre_processed_image")
                elif source == "custom":
                    var_name = self.get_value_of("named_source")
                    img = wrapper.retrieve_stored_image(var_name)
                else:
                    img = None
                    wrapper.error_holder.add_error(
                        f"Copy or rename image FAILED, unknown source: {source}",
                        target_logger=logger,
                    )
                    return
                if img is None:
                    wrapper.error_holder.add_error(
                        f"Copy or rename image FAILED, missing source: {source}",
                        target_logger=logger,
                    )
                    return

                # Apply ROIs
                rois = self.get_ipt_roi(
                    wrapper=wrapper,
                    roi_names=self.get_value_of("roi_names").replace(" ", "").split(","),
                    selection_mode=self.get_value_of("roi_selection_mode"),
                )
                img = wrapper.apply_roi_list(img=img, rois=rois)

                # Build output file name
                output_name_mode = self.get_value_of("output_name")
                if output_name_mode == "as_source":
                    dst_name = wrapper.file_handler.file_name_no_ext
                elif output_name_mode == "hash":
                    var_name = "hash_val"
                    dst_name = self.get_short_hash(add_plant_name=False)
                elif output_name_mode == "suffix":
                    var_name = self.get_value_of("prefix_suffix")
                    dst_name = wrapper.file_handler.file_name_no_ext + "_" + var_name
                elif output_name_mode == "prefix":
                    var_name = self.get_value_of("prefix_suffix")
                    dst_name = var_name + "_" + wrapper.file_handler.file_name_no_ext
                else:
                    wrapper.error_holder.add_error(
                        f"Copy or rename image FAILED, unknown naming convention: {output_name_mode}",
                        target_logger=logger,
                    )
                    return
                dst_path = self.get_value_of("path")

                # Get new extension
                file_ext = self.get_value_of("output_format")
                if file_ext == "source":
                    file_ext = self.wrapper.file_handler.file_ext
                else:
                    file_ext = f".{file_ext}"

                # Build destination full path
                dst_path = os.path.join(dst_path, f"{dst_name}{file_ext}")

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
                    img = ipc.resize_image(src_img=img, target_rect=r, keep_aspect_ratio=kar)

                # Copy image
                force_directories(self.get_value_of("path"))
                cv2.imwrite(filename=dst_path, img=img)
                res = True
            else:
                wrapper.store_image(wrapper.current_image, "current_image")
                res = True
        except Exception as e:
            res = False
            wrapper.error_holder.add_error(
                new_error_text=f'Failed to process {self. name}: "{repr(e)}"',
                new_error_level=3,
                target_logger=logger,
            )
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
        self.set_value_of(
            "path", os.path.join(os.path.dirname(__file__), "..", "test", "output_files", "")
        )

    @property
    def use_case(self):
        return ["Image generator"]

    @property
    def description(self):
        return "Copies an image, renaming it if needed"

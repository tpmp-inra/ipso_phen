import os

import cv2

import logging

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))

from ipso_phen.ipapi.base.ipt_abstract_analyzer import IptBaseAnalyzer
from ipso_phen.ipapi.tools.common_functions import make_safe_name
from ipso_phen.ipapi.base.ip_common import ToolFamily


class IptImageSplitter(IptBaseAnalyzer):
    def build_params(self):
        self.add_checkbox(
            name="save_image",
            desc="Save generated image",
            default_value=0,
        )
        self.add_file_naming()
        self.add_text_input(
            name="exp",
            desc="Experiment name",
            default_value="exp",
            hint="Enter experiment used for naming, only alphanumerical values",
        )
        self.add_text_input(
            name="tray_id",
            desc="Tray Id",
            default_value="1",
            hint="Enter plaque Id, only alphanumerical values",
        )
        self.add_slider(
            name="line_count", desc="Line count", default_value=1, minimum=1, maximum=20
        )
        self.add_spin_box(
            name="column_count",
            desc="Column count",
            default_value=1,
            minimum=1,
            maximum=20,
        )
        self.add_spin_box(
            name="padding_hor",
            desc="Horizontal padding",
            default_value=0,
            minimum=0,
            maximum=100,
            hint="Horizontal padding applied to the slices, will apply crop",
        )
        self.add_spin_box(
            name="padding_ver",
            desc="Vertical padding",
            default_value=0,
            minimum=0,
            maximum=100,
            hint="Vertical padding applied to the slices, will apply crop",
        )

    def process_wrapper(self, **kwargs):
        """
        Image slicer:
        Splits image into sub images using grid pattern
        Real time: False

        Keyword Arguments (in parentheses, argument name):
            * Save generated image (save_image):
            * Image output format (output_format):
            * Subfolders (subfolders): Subfolder names separated byt ","
            * Output naming convention (output_name):
            * Prefix (prefix): Use text as prefix
            * Suffix (suffix): Use text as suffix
            * Replace unsafe caracters (make_safe_name): Will replace *"/\[]:;|=,<> with "_"
            * Experiment name (exp): Enter experiment used for naming, only alphanumerical values
            * Tray Id (tray_id): Enter plaque Id, only alphanumerical values
            * Line count (line_count):
            * Column count (column_count):
            * Horizontal padding (padding_hor): Horizontal padding applied to the slices, will apply crop
            * Vertical padding (padding_ver): Vertical padding applied to the slices, will apply crop
        """
        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return False

        res = False
        try:
            exp = self.get_value_of("exp")
            tray_id = self.get_value_of("tray_id")
            line_count = self.get_value_of("line_count")
            column_count = self.get_value_of("column_count")
            padding_hor = self.get_value_of("padding_hor")
            padding_ver = self.get_value_of("padding_ver")
            save_image = self.get_value_of("save_image") == 1

            img = self.wrapper.current_image

            h, w = img.shape[:2]
            h_step, w_step = h // line_count, w // column_count

            for i in range(0, line_count):
                for j in range(0, column_count):
                    salt = f"_{exp}_t{tray_id}-l{i+1}-c{j+1}-p{i*column_count + j + 1}"
                    file_name = self.build_path(salt=salt)
                    slice_ = img[
                        i * h_step + padding_ver : i * h_step + h_step - padding_ver,
                        j * w_step + padding_hor : j * w_step + w_step - padding_hor,
                    ]
                    wrapper.store_image(slice_, salt)
                    if save_image:
                        cv2.imwrite(file_name, slice_)

                res = True
        except Exception as e:
            wrapper.error_holder.add_error(
                new_error_text=f'Failed to process {self. name}: "{repr(e)}"',
                new_error_level=35,
                target_logger=logger,
            )
            res = False
        else:
            pass
        finally:
            return res

    @property
    def name(self):
        return "Image slicer"

    @property
    def is_wip(self):
        return True

    @property
    def real_time(self):
        return False

    @property
    def result_name(self):
        return "none"

    @property
    def output_kind(self):
        return "none"

    @property
    def use_case(self):
        return [ToolFamily.IMAGE_GENERATOR]

    @property
    def description(self):
        return """Splits image into sub images using grid pattern"""

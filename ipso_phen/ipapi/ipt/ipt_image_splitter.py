import os

import cv2

import logging

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))

from ipso_phen.ipapi.base.ipt_abstract import IptBase
from ipso_phen.ipapi.tools.common_functions import make_safe_name
from ipso_phen.ipapi.base.ip_common import ToolFamily


class IptImageSplitter(IptBase):
    def build_params(self):
        self.add_source_selector(default_value="source")
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
        self.add_slider(
            name="column_count",
            desc="Column count",
            default_value=1,
            minimum=1,
            maximum=20,
        )
        self.add_slider(
            name="padding_hor",
            desc="Horizontal padding",
            default_value=0,
            minimum=0,
            maximum=100,
            hint="Horizontal padding applied to the slices, will apply crop",
        )
        self.add_slider(
            name="padding_ver",
            desc="Vertical padding",
            default_value=0,
            minimum=0,
            maximum=100,
            hint="Vertical padding applied to the slices, will apply crop",
        )
        self.add_checkbox(
            name="write_to_disc", desc="Save images to disc", default_value=1
        )

    def process_wrapper(self, **kwargs):
        """
        Image slicer:
        Splits image into sub images using grid pattern
        Real time : False

        Keyword Arguments (in parentheses, argument name):
            * Select source file type (source_file): no clue
            * Experiment name (exp): Enter experiment used for naming, only alphanumerical values
            * Tray Id (tray_id): Enter plaque Id, only alphanumerical values
            * Line count (line_count):
            * Column count (column_count):
            * Horizontal padding (padding_hor): Horizontal padding applied to the slices, will apply crop
            * Vertical padding (padding_ver): Vertical padding applied to the slices, will apply crop
            * Save images to disc (write_to_disc):
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
            write_to_disc = self.get_value_of("write_to_disc") == 1

            img = self.wrapper.current_image

            fn, ext = os.path.splitext(wrapper.file_name)
            h, w = img.shape[:2]
            h_step, w_step = h // line_count, w // column_count

            if not self.output_path:
                logger.error("Failed : Missing folder parameter")
            else:
                for i in range(0, line_count):
                    for j in range(0, column_count):
                        file_name = make_safe_name(
                            f"gridsplit_{exp}_t{tray_id}-l{i+1}-c{j+1}-p{i*column_count + j + 1}"
                        )
                        slice_ = img[
                            i * h_step + padding_ver : i * h_step + h_step - padding_ver,
                            j * w_step + padding_hor : j * w_step + w_step - padding_hor,
                        ]
                        wrapper.store_image(slice_, file_name)
                        if write_to_disc:
                            cv2.imwrite(
                                os.path.join(self.output_path, f"{file_name}{ext}"),
                                slice_,
                            )

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

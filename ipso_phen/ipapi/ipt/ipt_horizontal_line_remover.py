import cv2
import numpy as np

import logging
import os

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))

from ipso_phen.ipapi.base.ipt_abstract import IptBase
from ipso_phen.ipapi.base.ip_common import ToolFamily


class IptHorizontalLineDetector(IptBase):
    def build_params(self):
        self.add_source_selector(default_value="source")
        self.add_channel_selector(default_value="l")
        self.add_checkbox(
            name="is_apply_rois",
            desc="Apply ROIs to source image",
            default_value=0,
            hint="If true ROIs will be applied to source image",
        )
        self.add_checkbox(
            name="fully_isolated",
            desc="Only detect isolated lines",
            default_value=1,
            hint="If true, 1 side lines will be ignored",
        )
        self.add_slider(
            name="min_line_size",
            desc="Min line size p only",
            default_value=100,
            minimum=0,
            maximum=1000,
        )
        self.add_checkbox(
            name="build_mosaic",
            desc="Build mosaic",
            default_value=1,
            hint="If true edges and result will be displayed side by side",
        )
        self.add_separator(name="sep_1")
        self.add_morphology_operator(default_operator="none")

    def process_wrapper(self, **kwargs):
        """
        Horizontal line remover:
        Developped for Heliasen light barrier
        Removes horizontal noise lines

        Real time : False

        Keyword Arguments (in parentheses, argument name):
            * Select source file type (source_file): no clue
            * Channel (channel):
            * Apply ROIs to source image (is_apply_rois): If true ROIs will be applied to source image
            * Only detect isolated lines (fully_isolated): If true, 1 side lines will be ignored
            * Min line size p only (min_line_size):
            * Build mosaic (build_mosaic): If true edges and result will be displayed side by side
            * Morphology operator (morph_op):
            * Kernel size (kernel_size):
            * Kernel shape (kernel_shape):
            * Iterations (proc_times):
        """

        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return False

        res = False
        try:
            is_apply_rois = self.get_value_of("is_apply_rois", 0) == 1
            fully_isolated = self.get_value_of("fully_isolated", 1) == 1
            build_mosaic = self.get_value_of("build_mosaic") == 1
            channel = self.get_value_of("channel")
            min_line_size = self.get_value_of("min_line_size", 100)

            params_to_string_ = self.input_params_as_str()

            src_img = self.wrapper.current_image
            c = wrapper.get_channel(src_img, channel)
            if c is None:
                self.do_channel_failure(channel)
                return

            if is_apply_rois:
                wrapper.init_rois()
                c = wrapper.apply_rois(c, f"ROIs_{params_to_string_}")

            if build_mosaic:
                wrapper.store_image(c, "source_channel")

            lr = wrapper.remove_hor_noise_lines(
                mask=c,
                min_line_size=min_line_size,
                fully_isolated=fully_isolated,
                max_iter=100,
            )

            all_lines = lr["lines"]
            if all_lines and wrapper.is_store_image:
                img_drawned_lines = np.dstack((c, c, c))
                for j, lines in enumerate(all_lines):
                    for i, line in enumerate(lines):
                        h_color = int(i / len(lines) * 180)
                        s_color = int(j / len(all_lines) * 255)
                        line_color = (h_color, s_color, 255)
                        cv2.line(
                            img_drawned_lines,
                            (line[1], line[0]),
                            (line[2], line[0]),
                            line_color,
                            1,
                        )
                img_drawned_lines = cv2.cvtColor(img_drawned_lines, cv2.COLOR_HSV2BGR)
                wrapper.store_image(img_drawned_lines, f"removed_lines")

            c = lr["mask"]

            wrapper.store_image(c, f"cleaned_image_{params_to_string_}")

            self.result = self.apply_morphology_from_params(c)
            wrapper.store_image(self.result, f"after_morphology_{params_to_string_}")

            if build_mosaic:
                canvas = wrapper.build_mosaic(
                    image_names=np.array(
                        [
                            "source_channel",
                            f"removed_lines",
                            f"cleaned_image_{params_to_string_}",
                            f"after_morphology_{params_to_string_}",
                        ]
                    )
                )
                wrapper.store_image(canvas, "mosaic")

            res = True
        except Exception as e:
            logger.error(f'Failed to process {self. name}: "{repr(e)}"')
            res = False
        else:
            pass
        finally:
            return res

    @property
    def name(self):
        return "Horizontal line remover"

    @property
    def description(self):
        return (
            "Developped for Heliasen light barrier\n" "Removes horizontal noise lines\n"
        )

    @property
    def package(self):
        return "Heliasen"

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
        return [ToolFamily.PRE_PROCESSING]

    @property
    def description(self):
        return "Horizontal line remover.\nDevelopped for Heliasen light barrier.\nRemoves horizontal noise lines"

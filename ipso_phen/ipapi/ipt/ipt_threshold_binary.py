import numpy as np

import logging
import os

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))

from ipso_phen.ipapi.base.ipt_abstract import IptBase
from ipso_phen.ipapi.base.ip_common import all_colors_dict
from ipso_phen.ipapi.base.ip_common import ToolFamily


class IptThreshold(IptBase):
    def build_params(self):
        self.add_enabled_checkbox()
        self.add_channel_selector(default_value="h")
        self.add_checkbox(name="invert", desc="Invert mask", default_value=0)
        self.add_binary_threshold()
        self.add_text_overlay(0)
        self.add_checkbox(
            name="build_mosaic",
            desc="Build mosaic",
            default_value=0,
            hint="If true edges and result will be displayed side by side",
        )
        self.add_color_selector(
            name="background_color",
            desc="Background color",
            default_value="none",
            hint="""Color to be used when printing masked image.\n
             if "None" is selected standard mask will be printed.""",
            enable_none=True,
        )

    def process_wrapper(self, **kwargs):
        """
        Range threshold: Performs range threshold keeping only pixels with values between min and max.
        Morphology operation can be performed afterwards.


        Real time : True

        Keyword Arguments (in parentheses, argument name):
            * Activate tool (enabled): Toggle whether or not tool is active
            * Channel (channel):
            * Threshold min value (min_t):
            * Threshold max value (max_t):
            * Median filter size (odd values only) (median_filter_size):
            * Morphology operator (morph_op):
            * Kernel size (kernel_size):
            * Kernel shape (kernel_shape):
            * Iterations (proc_times):
            * Overlay text on top of images (text_overlay): Draw description text on top of images
            * Build mosaic (build_mosaic): If true edges and result will be displayed side by side
            * Background color (background_color): Color to be used when printing masked image. if "None" is selected standard mask will be printed.
        """
        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return False

        res = False
        try:
            if self.get_value_of("enabled") == 1:
                self.result = self.apply_binary_threshold(
                    wrapper=wrapper,
                    img=self.wrapper.current_image,
                    channel=self.get_value_of("channel"),
                )

                bck_color = self.get_value_of(key="background_color")
                if bck_color != "none":
                    bck_color = all_colors_dict[bck_color]
                    masked_image = wrapper.draw_image(
                        src_image=wrapper.current_image,
                        src_mask=self.result,
                        background=bck_color,
                    )
                    wrapper.store_image(masked_image, "masked_image")
                    main_result_name = "masked_image"
                    wrapper.store_image(self.result, "mask")
                    main_image = masked_image
                else:
                    main_result_name = f"threshold_{self.input_params_as_str()}"
                    main_image = self.result

                if self.get_value_of("invert") == 1:
                    main_image = 255 - main_image

                text_overlay = self.get_value_of("text_overlay") == 1
                if text_overlay:
                    wrapper.store_image(
                        main_image,
                        main_result_name,
                        text_overlay=self.input_params_as_str(
                            exclude_defaults=False,
                            excluded_params=("progress_callback",),
                        ).replace(", ", "\n"),
                    )
                else:
                    wrapper.store_image(
                        main_image, main_result_name, text_overlay=text_overlay
                    )

                if self.get_value_of("build_mosaic") == 1:
                    self.demo_image = wrapper.build_mosaic(
                        image_names=np.array(["current_image", main_result_name])
                    )
                    wrapper.store_image(self.demo_image, "mosaic")
                else:
                    self.demo_image = main_image
            res = True
        except Exception as e:
            res = False
            logger.error(f'Failed to process {self. name}: "{repr(e)}"')
        else:
            pass
        finally:
            return res

    @property
    def name(self):
        return "Range threshold"

    @property
    def real_time(self):
        return True

    @property
    def result_name(self):
        return "mask"

    @property
    def output_kind(self):
        return "mask"

    @property
    def use_case(self):
        return [ToolFamily.THRESHOLD]

    @property
    def description(self):
        return """Performs range threshold keeping only pixels with values between min and max.
        Morphology operation can be performed afterwards"""

import numpy as np

import logging

logger = logging.getLogger(__name__)

from base.ipt_abstract import IptBase
import base.ip_common as ipc
import tools.error_holder as eh


class IptSplittedRangeThreshold(IptBase):
    def build_params(self):
        self.add_enabled_checkbox()
        self.add_channel_selector(default_value="h")
        self.add_checkbox(name="invert", desc="Invert mask", default_value=0)

        self.add_roi_selector()

        self.add_spin_box(
            name="min_inside_t",
            desc="Threshold min value inside ROI",
            default_value=0,
            minimum=0,
            maximum=255,
        )
        self.add_spin_box(
            name="max_inside_t",
            desc="Threshold max value inside ROI",
            default_value=255,
            minimum=0,
            maximum=255,
        )
        self.add_spin_box(
            name="min_outside_t",
            desc="Threshold min value outside ROI",
            default_value=0,
            minimum=0,
            maximum=255,
        )
        self.add_spin_box(
            name="max_outside_t",
            desc="Threshold max value outside ROI",
            default_value=255,
            minimum=0,
            maximum=255,
        )
        self.add_spin_box(
            name="median_filter_size",
            desc="Median filter size (odd values only)",
            default_value=0,
            minimum=0,
            maximum=51,
        )
        self.add_morphology_operator()
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
            Splitted range threshold:
            Performs range threshold with two sets of borders applied inside and outside of linked ROIs.

                    If no ROIs are provided, all image will be considered within ROI.
            Real time: True

            Keyword Arguments (in parentheses, argument name):
                * Activate tool (enabled): Toggle whether or not tool is active
                * Channel (channel):
                * Invert mask (invert):
                * Name of ROI to be used (roi_names): Operation will only be applied inside of ROI
                * ROI selection mode (roi_selection_mode):
                * Threshold min value inside ROI (min_inside_t):
                * Threshold max value inside ROI (max_inside_t):
                * Threshold min value outside ROI (min_outside_t):
                * Threshold max value outside ROI (max_outside_t):
                * Median filter size (odd values only) (median_filter_size):
                * Morphology operator (morph_op):
                * Kernel size (kernel_size):
                * Kernel shape (kernel_shape):
                * Iterations (proc_times):
                * Overlay text on top of images (text_overlay): Draw description text on top of images
                * Build mosaic (build_mosaic): If true edges and result will be displayed side by side
                * Background color (background_color):
                    Color to be used when printing masked image.
                    if "None" is selected standard mask will be printed.
        """

        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return False

        res = False
        try:
            if self.get_value_of("enabled") == 1:
                img = wrapper.current_image
                rois = self.get_ipt_roi(
                    wrapper=wrapper,
                    roi_names=self.get_value_of("roi_names").replace(" ", "").split(","),
                    selection_mode=self.get_value_of("roi_selection_mode"),
                )

                # Build inside mask
                inside_mask, _ = wrapper.get_mask(
                    src_img=img,
                    channel=self.get_value_of("channel"),
                    min_t=self.get_value_of("min_inside_t"),
                    max_t=self.get_value_of("max_inside_t"),
                    median_filter_size=self.get_value_of("median_filter_size"),
                )
                inside_mask = wrapper.keep_rois(src_mask=inside_mask, tags=rois)
                wrapper.store_image(image=inside_mask, text="inside_mask")

                # Build outside mask
                outside_mask, _ = wrapper.get_mask(
                    src_img=img,
                    channel=self.get_value_of("channel"),
                    min_t=self.get_value_of("min_outside_t"),
                    max_t=self.get_value_of("max_outside_t"),
                    median_filter_size=self.get_value_of("median_filter_size"),
                )
                outside_mask = wrapper.delete_rois(src_mask=outside_mask, tags=rois)
                wrapper.store_image(image=outside_mask, text="outside_mask")

                # Merge masks
                self.result = wrapper.multi_or(image_list=(inside_mask, outside_mask))
                self.result = self.apply_morphology_from_params(self.result)

                bck_color = self.get_value_of(key="background_color")
                if bck_color != "none":
                    bck_color = ipc.all_colors_dict[bck_color]
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
                            exclude_defaults=False, excluded_params=("progress_callback",)
                        ).replace(", ", "\n"),
                    )
                else:
                    wrapper.store_image(main_image, main_result_name, text_overlay=text_overlay)
                self.demo_image = main_image

                if self.get_value_of("build_mosaic") == 1:
                    canvas = wrapper.build_mosaic(
                        image_names=np.array(["current_image", main_result_name])
                    )
                    wrapper.store_image(canvas, "mosaic")

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
            return res

    @property
    def name(self):
        return "Splitted range threshold"

    @property
    def package(self):
        return "IPSO Phen"

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
        return ["Threshold"]

    @property
    def description(self):
        return """Performs range threshold with two sets of borders applied inside and outside of linked ROIs.
        If no ROIs are provided, all image will be considered within ROI."""

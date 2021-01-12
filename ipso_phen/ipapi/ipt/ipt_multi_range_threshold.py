import numpy as np
import cv2

import logging
import os

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))

import ipso_phen.ipapi.base.ip_common as ipc
from ipso_phen.ipapi.base.ipt_abstract import IptBase


class IptMultiRangeThreshold(IptBase):
    def build_params(self):
        self.add_enabled_checkbox()

        self.add_channel_selector(default_value="h", name="c1", desc="Channel 1")
        self.add_spin_box(
            name="c1_low",
            desc="Min threshold for channel 1",
            default_value=0,
            minimum=0,
            maximum=255,
        )
        self.add_spin_box(
            name="c1_high",
            desc="Max threshold for channel 1",
            default_value=255,
            minimum=0,
            maximum=255,
        )
        self.add_channel_selector(
            default_value="none", name="c2", desc="Channel 2", enable_none=True
        )
        self.add_spin_box(
            name="c2_low",
            desc="Min threshold for channel 2",
            default_value=0,
            minimum=0,
            maximum=255,
        )
        self.add_spin_box(
            name="c2_high",
            desc="Max threshold for channel 2",
            default_value=255,
            minimum=0,
            maximum=255,
        )
        self.add_channel_selector(
            default_value="none", name="c3", desc="Channel 3", enable_none=True
        )
        self.add_spin_box(
            name="c3_low",
            desc="Min threshold for channel 3",
            default_value=0,
            minimum=0,
            maximum=255,
        )
        self.add_spin_box(
            name="c3_high",
            desc="Max threshold for channel 3",
            default_value=255,
            minimum=0,
            maximum=255,
        )
        self.add_combobox(
            name="merge_mode",
            desc="How to merge thresholds",
            default_value="multi_and",
            values=dict(multi_and="Logical AND", multi_or="Logical OR"),
        )

        self.add_separator(name="sep1")
        self.add_morphology_operator()

        self.add_separator(name="sep2")
        self.add_roi_selector()

        self.add_separator(name="sep3")
        self.add_text_overlay(0)
        self.add_checkbox(
            name="build_mosaic",
            desc="Build mosaic",
            default_value=0,
            hint="If true edges and result will be displayed side by side",
        )

    def process_wrapper(self, **kwargs):
        """
        Multi range threshold:
            Performs range threshold keeping only pixels with values between min and max
            for up to 3 channels.
            Morphology operation can be performed afterwards.
            Masks can be attached, they will be treated as keep masks
        Real time: True

        Keyword Arguments (in parentheses, argument name):
            * Activate tool (enabled): Toggle whether or not tool is active
            * Channel 1 (c1):
            * Min threshold for channel 1 (c1_low):
            * Max threshold for channel 1 (c1_high):
            * Channel 2 (c2):
            * Min threshold for channel 2 (c2_low):
            * Max threshold for channel 2 (c2_high):
            * Channel 3 (c3):
            * Min threshold for channel 3 (c3_low):
            * Max threshold for channel 3 (c3_high):
            * How to merge thresholds (merge_mode):
            * Morphology operator (morph_op):
            * Kernel size (kernel_size):
            * Kernel shape (kernel_shape):
            * Iterations (proc_times):
            * Name of ROI to be used (roi_names): Operation will only be applied inside of ROI
            * ROI selection mode (roi_selection_mode):
            * Overlay text on top of images (text_overlay): Draw description text on top of images
            * Build mosaic (build_mosaic): If true edges and result will be displayed side by side
        """
        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return False

        res = False
        try:
            if self.get_value_of("enabled") != 1:
                wrapper.store_image(wrapper.current_image, "current_image")
                res = True
                return

            img = wrapper.current_image
            build_mosaic = self.get_value_of("build_mosaic") == 1
            text_overlay = self.get_value_of("text_overlay") == 1
            if text_overlay:
                text = self.input_params_as_str(
                    exclude_defaults=False,
                    excluded_params=(
                        "progress_callback",
                        "enabled",
                        "text_overlay",
                        "build_mosaic",
                    ),
                ).replace(", ", "\n")
            else:
                text = ""

            channels = []
            stored_names = []
            dbg_channels = []
            for i in [1, 2, 3]:
                c = self.get_value_of(f"c{i}")
                if c == "none":
                    if build_mosaic:
                        dbg_channels.append(np.full_like(a=img[:, :, 0], fill_value=255))
                    continue
                msk, stored_name = wrapper.get_mask(
                    src_img=img,
                    channel=c,
                    min_t=self.get_value_of(f"c{i}_low"),
                    max_t=self.get_value_of(f"c{i}_high"),
                )
                channels.append(msk)
                if build_mosaic:
                    dbg_channels.append(msk)
                stored_names.append(stored_name)
                wrapper.store_image(image=msk, text=stored_name)

            func = getattr(wrapper, self.get_value_of("merge_mode"), None)
            if func:
                self.result = self.apply_morphology_from_params(
                    func([mask for mask in channels if mask is not None])
                )
                wrapper.store_image(
                    image=self.result,
                    text="multi_threshold_mask",
                    text_overlay=text if not build_mosaic else False,
                )
            else:
                logger.error("Unable to merge partial masks")
                res = False
                return

            rois = self.get_ipt_roi(
                wrapper=wrapper,
                roi_names=self.get_value_of("roi_names").replace(" ", "").split(","),
                selection_mode=self.get_value_of("roi_selection_mode"),
            )
            if len(rois) > 0:
                self.result = wrapper.keep_rois(self.result, rois)
                wrapper.store_image(image=self.result, text="rois_applied")

            if build_mosaic:
                wrapper.store_image(image=cv2.merge(dbg_channels), text="colored_mask")
                wrapper.store_image(image=self.result, text="mask")
                wrapper.store_image(
                    image=np.dstack(
                        (
                            dbg_channels[0],
                            np.zeros_like(dbg_channels[0]),
                            np.zeros_like(dbg_channels[0]),
                        )
                    ),
                    text="mask_1",
                )
                wrapper.store_image(
                    image=np.dstack(
                        (
                            np.zeros_like(dbg_channels[1]),
                            dbg_channels[1],
                            np.zeros_like(dbg_channels[1]),
                        )
                    ),
                    text="mask_2",
                )
                wrapper.store_image(
                    image=np.dstack(
                        (
                            np.zeros_like(dbg_channels[2]),
                            np.zeros_like(dbg_channels[2]),
                            dbg_channels[2],
                        )
                    ),
                    text="mask_3",
                )
                mosaic = wrapper.build_mosaic(
                    image_names=np.array(
                        [
                            ["current_image", "colored_mask", "mask"],
                            ["mask_1", "mask_2", "mask_3"],
                        ]
                    )
                )
                wrapper.store_image(
                    image=mosaic,
                    text="mosaic",
                    text_overlay=text,
                    font_color=ipc.C_WHITE,
                )
                self.demo_image = mosaic

        except Exception as e:
            res = False
            logger.error(f'Failed to process {self. name}: "{repr(e)}"')
        else:
            res = True
        finally:
            return res

    @property
    def name(self):
        return "Multi range threshold"

    @property
    def package(self):
        return "TPMP"

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
        return """Performs range threshold keeping only pixels with values between min and max
        for up to 3 channels.
        Morphology operation can be performed afterwards.
        Masks can be attached, they will be treated as keep masks"""

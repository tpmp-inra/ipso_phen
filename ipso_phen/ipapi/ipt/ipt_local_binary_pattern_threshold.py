import numpy as np
import cv2
from scipy.special import expit, logit
from skimage.feature import local_binary_pattern

import logging
import os

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))

from ipso_phen.ipapi.base.ipt_abstract import IptBase
import ipso_phen.ipapi.base.ip_common as ipc
from ipso_phen.ipapi.tools.regions import RectangleRegion


class IptLocalBinaryPatternThreshold(IptBase):
    def build_params(self):
        self.add_enabled_checkbox()
        self.add_channel_selector(default_value="l")
        self.add_spin_box(
            name="P",
            desc="Number of circularly symmetric neighbor",
            default_value=24,
            minimum=1,
            maximum=100,
            hint="Number of circularly symmetric neighbor set points (quantization of the angular space)",
        )
        self.add_spin_box(
            name="R",
            desc="Radius of circle",
            default_value=3,
            minimum=1,
            maximum=100,
            hint="Radius of circle (spatial resolution of the operator)",
        )
        self.add_combobox(
            name="method",
            desc="Method to determine the pattern",
            default_value="default",
            values=dict(
                default="original local binary pattern.",
                ror="extension of default implementation.",
                uniform="improved rotation invariance with uniform patterns.",
                nri_uniform="non rotation-invariant uniform patterns",
                var="rotation invariant variance.",
            ),
        )
        self.add_combobox(
            name=f"transformation",
            desc=f"Transformation applied to output",
            default_value="none",
            values=dict(
                none="None",
                log="log",
                sigmoid="Sigmoid",
                logit="Inverse sigmoid",
                arcsin="Arc sinus",
                sqrt="Square root",
            ),
        )
        self.add_spin_box(
            name="lower_cut",
            desc="Cut x%% lower values",
            default_value=0,
            minimum=0,
            maximum=100,
            hint="Increase to smooth low frequency textures regions and add detail to high frequencies",
        )
        self.add_spin_box(
            name="upper_cut",
            desc="Cut x%% upper values",
            default_value=0,
            minimum=0,
            maximum=100,
            hint="Increase to smooth high frequency textures regions and add detail to low frequencies",
        )
        self.add_combobox(
            name="post_processing",
            desc="Postprocessing option",
            default_value="none",
            values=dict(
                none="None", threshold="Threshold", false_color="Use false color"
            ),
        )
        self.add_binary_threshold(add_morphology=True)
        self.add_color_map_selector()

    def process_wrapper(self, **kwargs):
        """
        Local binary pattern threshold:
        Gray scale and rotation invariant LBP (Local Binary Patterns).
                LBP is an invariant descriptor that can be used for texture classification.
        Real time: False

        Keyword Arguments (in parentheses, argument name):
            * Activate tool (enabled): Toggle whether or not tool is active
            * Channel (channel):
            * Number of circularly symmetric neighbor (P): Number of circularly symmetric neighbor set points (quantization of the angular space)
            * Radius of circle (R): Radius of circle (spatial resolution of the operator)
            * Method to determine the pattern (method):
            * Transformation applied to output (transformation):
            * Cut x%% lower values (lower_cut): Increase to smooth low frequency textures regions and add detail to high frequencies
            * Cut x%% upper values (upper_cut): Increase to smooth high frequency textures regions and add detail to low frequencies
            * Postprocessing option (post_processing):
            * Threshold min value (min_t):
            * Threshold max value (max_t):
            * Median filter size (odd values only) (median_filter_size):
            * Morphology operator (morph_op):
            * Kernel size (kernel_size):
            * Kernel shape (kernel_shape):
            * Iterations (proc_times):
            * Select pseudo color map (color_map):
        """

        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return False

        res = False
        try:
            if self.get_value_of("enabled") == 1:
                c = ipc.resize_image(
                    wrapper.get_channel(
                        wrapper.current_image, self.get_value_of("channel")
                    ),
                    target_rect=RectangleRegion(width=800, height=600),
                    keep_aspect_ratio=True,
                    output_as_bgr=False,
                )
                c = local_binary_pattern(
                    image=c,
                    P=self.get_value_of("P", scale_factor=wrapper.scale_factor),
                    R=self.get_value_of("R", scale_factor=wrapper.scale_factor),
                    method=self.get_value_of("method"),
                )

                # Transform
                ct = self.get_value_of(f"transformation")
                if ct == "sigmoid":
                    c = np.interp(c, (c.min(), c.max()), (0, 5))
                    c = expit(c)
                elif ct == "log":
                    c = np.log(c + 1)
                elif ct == "logit":
                    c = np.interp(c, (c.min(), c.max()), (0.5, 0.99))
                    c = logit(c)
                elif ct == "arcsin":
                    c = np.interp(c, (c.min(), c.max()), (0, 1))
                    c = np.arcsin(c)
                elif ct == "sqrt":
                    c = np.interp(c, (c.min(), c.max()), (0, 1))
                    c = np.sqrt(c)

                # Cut
                lower_cut = self.get_value_of("lower_cut")
                if lower_cut > 0:
                    c[c < np.max(c) * (lower_cut / 100)] = 0
                upper_cut = self.get_value_of("upper_cut")
                if upper_cut > 0:
                    upper_cut = np.max(c) * ((100 - upper_cut) / 100)
                    c[c > upper_cut] = upper_cut

                c = self.to_uint8(c)

                # Post processing
                pp = self.get_value_of("post_processing")
                if pp == "threshold":
                    median_filter_size = self.get_value_of("median_filter_size")
                    median_filter_size = (
                        0
                        if median_filter_size == 1
                        else ipc.ensure_odd(median_filter_size)
                    )
                    c, _ = wrapper.get_mask(
                        src_img=c,
                        channel=None,
                        min_t=self.get_value_of("min_t"),
                        max_t=self.get_value_of("max_t"),
                        median_filter_size=median_filter_size,
                    )
                    self.result = self.apply_morphology_from_params(c)
                elif pp == "false_color":
                    color_map = self.get_value_of("color_map")
                    _, color_map = color_map.split("_")
                    self.result = cv2.applyColorMap(c, int(color_map))
                else:
                    self.result = c

                # Store
                wrapper.store_image(self.result, "local_binary_pattern")
                res = True
            else:
                wrapper.store_image(wrapper.current_image, "current_image")
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
        return "Local binary pattern threshold"

    @property
    def is_wip(self):
        return True

    @property
    def package(self):
        return "Scikit-Learn"

    @property
    def real_time(self):
        return False

    @property
    def result_name(self):
        return "image"

    @property
    def output_kind(self):
        return "image"

    @property
    def use_case(self):
        return [
            ipc.ToolFamily.THRESHOLD,
            ipc.ToolFamily.VISUALIZATION,
            ipc.ToolFamily.PRE_PROCESSING,
        ]

    @property
    def description(self):
        return """Gray scale and rotation invariant LBP (Local Binary Patterns).
        LBP is an invariant descriptor that can be used for texture classification."""

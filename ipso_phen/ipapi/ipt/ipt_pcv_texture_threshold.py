from plantcv import plantcv as pcv

import logging
import os

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))

from ipso_phen.ipapi.base.ipt_abstract import IptBase


class IptPcvTextureThreshold(IptBase):
    def build_params(self):
        self.add_enabled_checkbox()
        self.add_channel_selector(default_value="h")
        self.add_spin_box(
            name="kernel_size",
            desc="Kernel size for texture measure calculation",
            default_value=6,
            minimum=3,
            maximum=21,
        )
        self.add_spin_box(
            name="threshold",
            desc="Threshold value (0-255)",
            default_value=7,
            minimum=0,
            maximum=255,
        )
        self.add_spin_box(
            name="offset",
            desc="Distance offsets",
            default_value=3,
            minimum=0,
            maximum=1000,
        )
        self.add_combobox(
            name="texture_method",
            desc="Feature of a grey level co-occurrence matrix",
            default_value="dissimilarity",
            values=dict(
                contrast="contrast",
                dissimilarity="dissimilarity",
                homogeneity="homogeneity",
                ASM="ASM",
                energy="energy",
                correlation="correlation",
            ),
            hint="For equations of different features see http://scikit-image.org/docs/dev/api/skimage.feature.html#greycoprops",
        )
        self.add_combobox(
            name="borders",
            desc="How the array borders are handled",
            default_value="nearest",
            values=dict(
                reflect="reflect",
                constant="constant",
                nearest="nearest",
                mirror="mirror",
                wrap="wrap",
            ),
        )
        self.add_checkbox(name="invert", desc="Invert mask", default_value=0)

    def process_wrapper(self, **kwargs):
        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return False

        res = False
        try:
            if self.get_value_of("enabled") == 1:
                self.result = pcv.threshold.texture(
                    gray_img=wrapper.get_channel(
                        wrapper.current_image, self.get_value_of("channel")
                    ),
                    ksize=self.get_value_of("kernel_size"),
                    threshold=self.get_value_of("threshold"),
                    offset=self.get_value_of("offset"),
                    texture_method=self.get_value_of("texture_method"),
                    borders=self.get_value_of("borders"),
                    max_value=255,
                )
                if self.get_value_of("invert") == 1:
                    self.result -= 255

                # Write your code here
                wrapper.store_image(self.result, "texture_threshold")
                res = True
            else:
                wrapper.store_image(wrapper.current_image, "current_image")
                res = True
        except Exception as e:
            res = False
            wrapper.error_holder.add_error(
                new_error_text=f'Failed to process {self. name}: "{repr(e)}"',
                new_error_level=35,
                target_logger=logger,
            )
        else:
            pass
        finally:
            return res

    @property
    def name(self):
        return "PCV Texture Threshold"

    @property
    def package(self):
        return "PlantCV"

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
        return ["Threshold", "PlantCV"]

    @property
    def description(self):
        return "Creates a binary image from a grayscale image using skimage texture calculation for thresholding."

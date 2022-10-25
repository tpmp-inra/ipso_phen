from ipso_phen.ipapi.base.ipt_abstract_analyzer import IptBaseAnalyzer


import os
import logging

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))

import ipso_phen.ipapi.base.ip_common as ipc


class IptImageScaler(IptBaseAnalyzer):
    def build_params(self):
        self.add_enabled_checkbox()
        self.add_checkbox(
            name="save_image",
            desc="Save generated image",
            default_value=0,
        )
        self.add_text_input(
            name="img_name",
            desc="Name in csv",
            default_value="img",
        )
        self.add_combobox(
            name="output_selector",
            desc="Select output",
            default_value="image",
            values={
                "image": "image",
                "data": "data",
            },
            hint="Select output type",
        )
        self.add_file_naming()
        self.add_checkbox(
            name="grab_linked_images",
            desc="Add linked images",
            default_value=0,
            hint="Crop also all linked images",
        )
        self.add_combobox(
            name="scale_direction",
            desc="Scaling direction",
            values={
                "up": "Up",
                "down": "Down",
            },
            default_value="down",
        )
        self.add_spin_box(
            name="scale_factor",
            desc="Scale factor",
            default_value=2,
            minimum=1,
            maximum=100,
        )
        self.add_checkbox(
            name="store_transformation",
            desc="Store transformation",
            default_value=1,
            hint="Store transformation so it will be applied to linked images",
        )

    def process_wrapper(self, **kwargs):
        """
        Image scaler:
        'Scale image according to factor
        Real time: True

        Keyword Arguments (in parentheses, argument name):
            * Activate tool (enabled): Toggle whether or not tool is active
            * Save generated image (save_image):
            * Name in csv (img_name):
            * Image output format (output_format):
            * Subfolders (subfolders): Subfolder names separated byt ","
            * Output naming convention (output_name):
            * Prefix (prefix): Use text as prefix
            * Suffix (suffix): Use text as suffix
            * Replace unsafe caracters (make_safe_name): Will replace *"/\[]:;|=,<> with "_"
            * Add linked images (grab_linked_images): Crop also all linked images
            * Scaling direction (scale_direction):
            * Scale factor (scale_factor):"""

        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return False

        res = False
        try:
            if self.get_value_of("enabled") == 1:
                sf = self.get_value_of("scale_factor")
                sf = sf if self.get_value_of("scale_direction") == "up" else 1 / sf
                self.result = ipc.scale_image(
                    src_img=wrapper.current_image,
                    scale_factor=sf,
                )
                if self.get_value_of("store_transformation") == 1:
                    wrapper.image_transformations.append(
                        {
                            "action": "scale",
                            "scale_factor": sf,
                        }
                    )
                self.add_value(
                    "scaled_width",
                    value=self.result.shape[1],
                    force_add=True,
                )
                self.add_value(
                    "scaled_height",
                    value=self.result.shape[0],
                    force_add=True,
                )

                if self.get_value_of("save_image") != 0:
                    self.save_images(additional_images=[], **kwargs)
                wrapper.store_image(self.result, "cropped_image")
                self.demo_image = self.result
                res = True
            else:
                wrapper.store_image(wrapper.current_image, "current_image")
                res = True
        except Exception as e:
            res = False
            logger.error(f"Image scaler FAILED, exception: {repr(e)}")
        else:
            pass
        finally:
            return res

    def apply_test_values_overrides(self, use_cases: tuple = ()):
        if ipc.ToolFamily.FEATURE_EXTRACTION in use_cases:
            self.set_value_of("save_image", 1)
            self.set_value_of("output_selector", "data")

    @property
    def name(self):
        return "Image scaler"

    @property
    def package(self):
        return "TPMP"

    @property
    def real_time(self):
        return True

    @property
    def result_name(self):
        return "image"

    @property
    def output_kind(self):
        return "image"

    @property
    def use_case(self):
        return ["Image generator", "Visualization"]

    @property
    def description(self):
        return """'Scale image according to factor"""

    @property
    def output_type(self):
        return (
            ipc.IO_DATA
            if self.get_value_of("output_selector") == "data"
            else ipc.IO_IMAGE
        )
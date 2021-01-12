import cv2

from ipso_phen.ipapi.tools.common_functions import force_directories
from ipso_phen.ipapi.base.ipt_abstract_analyzer import IptBaseAnalyzer
from ipso_phen.ipapi.base import ip_common as ipc

import logging
import os

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))


class IptDataViz(IptBaseAnalyzer):
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
        self.add_file_naming()
        self.add_channel_selector(
            default_value="l",
            desc="Pseudo color channel",
        )
        self.add_color_map_selector()
        self.add_combobox(
            name="foreground",
            desc="Foreground",
            default_value="source",
            values={
                "source": "Use source image",
                "bw": "Black & White",
                "false_colour": "Selected color map",
                "color": "Color selected below",
            },
        )
        self.add_color_selector(
            name="fore_color",
            desc="Background color",
            default_value="black",
        )
        self.add_combobox(
            name="background",
            desc="Background",
            default_value="bw",
            values={
                "source": "Use source image",
                "bw": "Black & White",
                "color": "Color selected below",
            },
        )
        self.add_color_selector(
            name="bcg_color",
            desc="Background color",
            default_value="black",
        )
        self.add_spin_box(
            name="bck_grd_luma",
            desc="Background intensity",
            default_value=150,
            minimum=0,
            maximum=200,
        )
        self.add_checkbox(
            name="normalize",
            desc="Normalize source image",
            default_value=0,
        )
        self.add_roi_selector()

        self.add_spin_box(
            name="contour_thickness",
            desc="Contour thickness",
            default_value=4,
        )
        self.add_checkbox(
            name="cnt_num",
            desc="Add numeric value for contour",
            default_value=0,
        )
        self.add_spin_box(
            name="hull_thickness",
            desc="Hull thickness",
            default_value=0,
        )
        self.add_spin_box(
            name="bounding_rec_thickness",
            desc="Bounding rectangle thickness",
            default_value=0,
        )
        self.add_spin_box(
            name="straight_bounding_rec_thickness",
            desc="Straight bounding rectangle thickness",
            default_value=0,
        )
        self.add_spin_box(
            name="enclosing_circle_thickness",
            desc="Enclosing circle thickness",
            default_value=0,
        )
        self.add_spin_box(
            name="centroid_width",
            desc="Centroid width",
            default_value=0,
        )
        self.add_spin_box(
            name="centroid_line_width",
            desc="Centroid line width",
            default_value=0,
        )
        self.add_checkbox(
            name="cx_num",
            desc="Add numeric value for centroid x value",
            default_value=0,
        )
        self.add_checkbox(
            name="cy_num",
            desc="Add numeric value for centroid y value",
            default_value=0,
        )
        self.add_spin_box(
            name="height_thickness",
            desc="Height thickness",
            default_value=0,
        )
        self.add_spin_box(
            name="width_thickness",
            desc="Width thickness",
            default_value=0,
        )

    def process_wrapper(self, **kwargs):
        """
        Visualization helper:
        'With the current image and a mask build a visualization for selected features
        Real time: True

        Keyword Arguments (in parentheses, argument name):
            * Activate tool (enabled): Toggle whether or not tool is active
            * Save generated image (save_image):
            * Name in csv (img_name):
            * Image output format (output_format):
            * Output naming convention (output_name):
            * Prefix or suffix (prefix_suffix):
            * Pseudo color channel (channel):
            * Select pseudo color map (color_map):
            * Foreground (foreground):
            * Background color (fore_color):
            * Background (background):
            * Background color (bcg_color):
            * Background intensity (bck_grd_luma):
            * Normalize source image (normalize):
            * Name of ROI to be used (roi_names): Operation will only be applied inside of ROI
            * ROI selection mode (roi_selection_mode):
            * Contour thickness (contour_thickness):
            * Add numeric value for contour (cnt_num):
            * Hull thickness (hull_thickness):
            * Bounding rectangle thickness (bounding_rec_thickness):
            * Straight bounding rectangle thickness (straight_bounding_rec_thickness):
            * Enclosing circle thickness (enclosing_circle_thickness):
            * Centroid width (centroid_width):
            * Centroid line width (centroid_line_width):
            * Add numeric value for centroid x value (cx_num):
            * Add numeric value for centroid y value (cy_num):
            * Height thickness (height_thickness):
            * Width thickness (width_thickness):
        """

        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return False

        res = False
        try:
            if self.get_value_of("enabled") == 1:
                self.result = wrapper.draw_image(
                    src_image=wrapper.current_image,
                    src_mask=self.get_mask(),
                    **self.params_to_dict(
                        include_input=True,
                        include_output=False,
                        include_neutral=False,
                    ),
                )

                if self.get_value_of("save_image") != 0:
                    dst_path = self.build_output_path()
                    self.add_value(
                        key=self.get_value_of("img_name"),
                        value=dst_path,
                        force_add=True,
                    )
                    force_directories(self.output_path)
                    cv2.imwrite(filename=dst_path, img=self.result)
                wrapper.store_image(self.result, "visualization")
                self.demo_image = self.result
                res = True
            else:
                wrapper.store_image(wrapper.current_image, "current_image")
                res = True
        except Exception as e:
            res = False
            logger.error(f"Data viz FAILED, exception: {repr(e)}")
        else:
            pass
        finally:
            return res

    def apply_test_values_overrides(self, use_cases: tuple = ()):
        self.set_value_of("save_image", 1)

    @property
    def name(self):
        return "Visualization helper"

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
        return ["Image generator"]

    @property
    def description(self):
        return """'With the current image and a mask build a visualization for selected features"""

    @property
    def output_type(self):
        return ipc.IO_DATA if self.get_value_of("save_image") != 0 else ipc.IO_IMAGE

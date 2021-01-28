import os
import pickle

import logging

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))

import cv2
import numpy as np
from skimage.transform import hough_ellipse
from skimage.draw import ellipse_perimeter

import ipso_phen.ipapi.base.ip_common as ipc
from ipso_phen.ipapi.base.ipt_abstract_analyzer import IptBaseAnalyzer
from ipso_phen.ipapi.ipt.ipt_edge_detector import IptEdgeDetector
from ipso_phen.ipapi.tools.folders import ipso_folders


class IptHoughEllipses(IptBaseAnalyzer):
    def build_params(self):
        self.add_checkbox(
            name="enable_cache",
            desc="Allow retrieving data from cache",
            default_value=1,
            hint="Data will be retrieved only if params are identical.",
        )
        self.add_combobox(
            name="source_selector",
            desc="Select source",
            default_value="current_image",
            values={"current_image": "Current image", "mask": "Mask"},
            hint="Select which image will be used as source",
        )
        self.add_separator(name="s1")
        self.add_channel_selector(default_value="l")
        self.add_checkbox(
            name="normalize",
            desc="Normalize channel",
            default_value=0,
            hint="Normalize channel before edge detection",
        )
        self.add_slider(
            name="median_filter_size",
            desc="Median filter size (odd values only)",
            default_value=0,
            minimum=0,
            maximum=51,
        )
        self.add_spin_box(
            name="min_radius",
            desc="Minimal radius to consider",
            default_value=400,
            minimum=0,
            maximum=2000,
            hint="All circles smaller than this will be ignored",
        )
        self.add_spin_box(
            name="max_radius",
            desc="Maximal radius to consider",
            default_value=1000,
            minimum=0,
            maximum=2000,
            hint="All circles bigger than this will be ignored",
        )
        self.add_spin_box(
            name="hough_accuracy",
            desc="Accuracy",
            default_value=20,
            minimum=0,
            maximum=2000,
            hint="Bin size on the minor axis used in the accumulator.",
        )
        self.add_spin_box(
            name="hough_threshold",
            desc="Hough threshold",
            default_value=20,
            minimum=0,
            maximum=2000,
            hint="Bin size on the minor axis used in the accumulator.",
        )
        self.add_spin_box(
            name="line_width",
            desc="Draw line width",
            default_value=4,
            minimum=1,
            maximum=20,
        )
        self.add_checkbox(name="edge_only", desc="Edge detection only", default_value=0)
        self.add_edge_detector()

    def process_wrapper(self, **kwargs):

        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return False

        res = False
        try:
            # Read params
            input_kind = self.get_value_of("source_selector")

            edge_only = self.get_value_of("edge_only") == 1

            roi = self.get_ipt_roi(
                wrapper=wrapper,
                roi_names=[self.get_value_of("crop_roi_name")],
                selection_mode="all_named",
            )
            roi = roi[0] if roi else None

            if input_kind == "mask":
                img = self.get_mask()
            elif input_kind == "current_image":
                img = wrapper.current_image
            else:
                img = None
                logger.error(f"Unknown source: {input_kind}")
                self.result = None
                return

            pkl_file = os.path.join(
                ipso_folders.get_path("stored_data"),
                self.get_short_hash(exclude_list=()) + ".pkl",
            )
            if (
                (self.get_value_of("enable_cache") == 1)
                and edge_only is False
                and os.path.isfile(pkl_file)
            ):
                with open(pkl_file, "rb") as f:
                    result = pickle.load(f)
            else:
                # Get the edge
                with IptEdgeDetector(wrapper=wrapper, **self.params_to_dict()) as (
                    res,
                    ed,
                ):
                    if not res:
                        return
                    edges = ed.result
                    if edge_only is True:
                        self.result = ed.result
                        self.demo_image = self.result
                        return True

                result = hough_ellipse(
                    edges,
                    accuracy=self.get_value_of("hough_accuracy"),
                    threshold=self.get_value_of("hough_threshold"),
                    min_size=self.get_value_of("min_radius"),
                    max_size=self.get_value_of("max_radius"),
                )
                result.sort(order="accumulator")

                if self.get_value_of("enable_cache") == 1:
                    with open(pkl_file, "wb") as f:
                        pickle.dump(result, f)

            if result is not None:
                colors = ipc.build_color_steps(step_count=len(result))
                for i, ellipse in enumerate(result):
                    yc, xc, a, b = [int(round(x)) for x in ellipse[1:5]]
                    orientation = ellipse[5]
                    cy, cx = ellipse_perimeter(yc, xc, a, b, orientation)
                    img[cy, cx] = colors[i]
            wrapper.store_image(image=img, text="hough_ellipses")
            self.demo_image = img
            res = True
        except Exception as e:
            logger.exception(f'Failed to process {self. name}: "{repr(e)}"')
            res = False
        else:
            pass
        finally:
            return res

    @property
    def name(self):
        return "Hough ellipses detector"

    @property
    def real_time(self):
        return self.get_value_of("edge_only") == 1

    @property
    def result_name(self):
        return "ellipses"

    @property
    def output_kind(self):
        return "data"

    @property
    def use_case(self):
        return [ipc.ToolFamily.FEATURE_EXTRACTION]

    @property
    def description(self):
        return "Hough ellipses detector: Perform a elliptical Hough transform."

    @property
    def input_type(self):
        if self.get_value_of("source_selector") == "mask":
            return ipc.IO_MASK
        else:
            return ipc.IO_IMAGE

    @property
    def output_type(self):
        if self.get_value_of("edge_only") == 1:
            return ipc.IO_IMAGE  # self.input_type
        else:
            return ipc.IO_DATA

    def apply_test_values_overrides(self, use_cases: tuple = ()):
        self.set_value_of("enable_cache", 0)

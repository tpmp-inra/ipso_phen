import os
import pickle

import logging

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))

import cv2
import numpy as np
from skimage.transform import hough_circle, hough_circle_peaks

import ipso_phen.ipapi.base.ip_common as ipc
from ipso_phen.ipapi.base.ipt_abstract import IptBase
from ipso_phen.ipapi.ipt.ipt_edge_detector import IptEdgeDetector
from ipso_phen.ipapi.tools.regions import (
    RectangleRegion,
    CircleRegion,
    AnnulusRegion,
    Point,
)
from ipso_phen.ipapi.tools.folders import ipso_folders


class IptHoughCircles(IptBase):
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
        self.add_roi_settings(
            default_name="unnamed_roi", default_type="keep", default_shape="rectangle"
        )
        self.add_separator(name="s1")
        self.add_text_input(
            name="crop_roi_name",
            desc="Name of ROI to be used",
            default_value="",
            hint="Circles will only be detected inside ROI",
        )
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
            name="annulus_size",
            desc="Annulus secondary radius delta",
            default_value=0,
            minimum=0,
            maximum=2000,
            hint="Annulus size, 0 means full disc",
        )
        self.add_spin_box(
            name="step_radius",
            desc="Radius granularity",
            default_value=10,
            minimum=0,
            maximum=100,
            hint="Steps for scanning radius",
        )
        self.add_spin_box(
            name="max_peaks",
            desc="Maximum number of detected circles",
            default_value=2,
            minimum=-1,
            maximum=200,
            hint="Keeps only n best circles",
        )
        self.add_spin_box(
            name="min_distance",
            desc="Minimum distance between two circles",
            default_value=20,
            minimum=1,
            maximum=2000,
            hint="Remove circles that are too close",
        )
        self.add_spin_box(
            name="line_width",
            desc="Draw line width",
            default_value=4,
            minimum=1,
            maximum=20,
        )
        self.add_checkbox(
            name="keep_only_one",
            desc="Keep only closest, if not, ROI is larger circle",
            default_value=0,
        )
        self.add_combobox(
            name="target_position",
            desc="Keep the closest circle closest to",
            default_value="BOTTOM_CENTER",
            values=dict(
                TOP_LEFT="TOP_LEFT",
                TOP_CENTER="TOP_CENTER",
                TOP_RIGHT="TOP_RIGHT",
                MIDDLE_LEFT="MIDDLE_LEFT",
                MIDDLE_CENTER="MIDDLE_CENTER",
                MIDDLE_RIGHT="MIDDLE_RIGHT",
                BOTTOM_LEFT="BOTTOM_LEFT",
                BOTTOM_CENTER="BOTTOM_CENTER",
                BOTTOM_RIGHT="BOTTOM_RIGHT",
            ),
        )
        self.add_slider(
            name="max_dist_to_root",
            desc="Maximum distance to root position",
            default_value=1000,
            minimum=0,
            maximum=4000,
        )
        self.add_checkbox(
            name="draw_boundaries", desc="Draw max and min circles", default_value=0
        )
        self.add_checkbox(
            name="draw_candidates", desc="Draw discarded candidates", default_value=0
        )
        self.add_spin_box(
            name="expand_circle",
            desc="Contract/expand circle",
            default_value=0,
            minimum=-1000,
            maximum=1000,
        )
        self.add_checkbox(name="edge_only", desc="Edge detection only", default_value=0)
        self.add_edge_detector()
        self.add_text_overlay()

    def process_wrapper(self, **kwargs):
        """
        Hough circles detector:
        Hough circles detector: Perform a circular Hough transform.
        Can generate ROIs
        Real time: False

        Keyword Arguments (in parentheses, argument name):
            * Allow retrieving data from cache (enable_cache): Data will be retrieved only if params are identical.
            * ROI name (roi_name):
            * Select action linked to ROI (roi_type): no clue
            * Select ROI shape (c): no clue
            * Target IPT (tool_target): no clue
            * Name of ROI to be used (crop_roi_name): Circles will only be detected inside ROI
            * Channel (channel):
            * Normalize channel (normalize): Normalize channel before edge detection
            * Median filter size (odd values only) (median_filter_size):
            * Minimal radius to consider (min_radius): All circles smaller than this will be ignored
            * Maximal radius to consider (max_radius): All circles bigger than this will be ignored
            * Annulus secondary radius delta (annulus_size): Annulus size, 0 means full disc
            * Radius granularity (step_radius): Steps for scanning radius
            * Maximum number of detected circles (max_peaks): Keeps only n best circles
            * Minimum distance between two circles (min_distance): Remove circles that are too close
            * Draw line width (line_width):
            * Keep only closest, if not, ROI is larger circle (keep_only_one):
            * Keep the closest circle closest to (target_position):
            * Maximum distance to root position (max_dist_to_root):
            * Draw max and min circles (draw_boundaries):
            * Draw discarded candidates (draw_candidates):
            * Contract/expand circle (expand_circle):
            * Edge detection only (edge_only):
            * Select edge detection operator (operator):
            * Canny's sigma for scikit, aperture for OpenCV (canny_sigma): Sigma.
            * Canny's first Threshold (canny_first): First threshold for the hysteresis procedure.
            * Canny's second Threshold (canny_second): Second threshold for the hysteresis procedure.
            * Kernel size (kernel_size):
            * Threshold (threshold): Threshold for kernel based operators
            * Apply threshold (apply_threshold):
            * Overlay text on top of images (text_overlay): Draw description text on top of images
        """

        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return False

        res = False
        try:
            # Read params
            min_radius = self.get_value_of(
                "min_radius",
                scale_factor=wrapper.scale_factor,
            )
            max_radius = self.get_value_of(
                "max_radius",
                scale_factor=wrapper.scale_factor,
            )
            step_radius = self.get_value_of(
                "step_radius",
                scale_factor=wrapper.scale_factor,
            )
            max_peaks = self.get_value_of("max_peaks")
            max_peaks = max_peaks if max_peaks > 0 else np.inf
            min_distance = self.get_value_of(
                "min_distance",
                scale_factor=wrapper.scale_factor,
            )
            line_width = self.get_value_of(
                "line_width",
                scale_factor=wrapper.scale_factor,
            )
            draw_candidates = self.get_value_of("draw_candidates") == 1
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
                self.get_short_hash(
                    exclude_list=(
                        "roi_name",
                        "roi_type",
                        "roi_shape",
                        "tool_target",
                        "annulus_size",
                        "line_width",
                        "keep_only_one",
                        "target_position",
                        "max_dist_to_root",
                        "draw_boundaries",
                        "draw_candidates",
                        "expand_circle",
                    )
                )
                + ".pkl",
            )
            if (
                (self.get_value_of("enable_cache") == 1)
                and edge_only is False
                and os.path.isfile(pkl_file)
            ):
                with open(pkl_file, "rb") as f:
                    accu, cx, cy, radii = pickle.load(f)
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

                if roi is not None:
                    edges = wrapper.crop_to_roi(
                        img=edges,
                        roi=roi,
                        erase_outside_if_circle=True,
                        dbg_str="cropped_edges",
                    )

                # Detect circles
                hough_radii = np.arange(min_radius, max_radius, step_radius)
                hough_res = hough_circle(edges, hough_radii)

                # Draw the result
                if len(img.shape) == 2:
                    img = np.dstack((img, img, img))

                # Select the most prominent n circles
                accu, cx, cy, radii = hough_circle_peaks(
                    hough_res,
                    hough_radii,
                    min_xdistance=min_distance,
                    min_ydistance=min_distance,
                    total_num_peaks=max_peaks,
                )

                if self.get_value_of("enable_cache") == 1:
                    with open(pkl_file, "wb") as f:
                        pickle.dump((accu, cx, cy, radii), f)

            if roi is not None:
                roi = roi.as_rect()
                cx += roi.left
                cy += roi.top
            if self.get_value_of("keep_only_one") == 1:
                candidates = [[a, x, y, z] for a, x, y, z in zip(accu, cx, cy, radii)]
                h, w = img.shape[:2]
                roi = RectangleRegion(left=0, right=w, top=0, bottom=h)
                roi_root = roi.point_at_position(
                    self.get_value_of("target_position"), True
                )
                min_dist = h * w
                min_idx = -1
                min_accu = -1
                i = 0
                colors = ipc.build_color_steps(step_count=len(candidates))
                max_dist_to_root = self.get_value_of(
                    "max_dist_to_root", scale_factor=wrapper.scale_factor
                )
                for c_accu, center_x, center_y, radius in candidates:
                    if draw_candidates:
                        cv2.circle(
                            img,
                            (center_x, center_y),
                            radius,
                            colors[i],
                            max(1, line_width // 2),
                        )
                    cur_dist = roi_root.distance_to(Point(center_x, center_y))
                    if (
                        (cur_dist < min_dist)
                        and (cur_dist < max_dist_to_root)
                        and (
                            (cur_dist / min_dist > min_accu / c_accu) or (min_accu == -1)
                        )
                    ):
                        min_dist = cur_dist
                        min_idx = i
                        min_accu = c_accu

                    i += 1
                if min_idx >= 0:
                    self.result = [
                        [
                            candidates[min_idx][1],
                            candidates[min_idx][2],
                            candidates[min_idx][3],
                        ]
                    ]
                    self.result[0][2] += self.get_value_of(
                        "expand_circle", scale_factor=wrapper.scale_factor
                    )
                    if self.get_value_of("draw_boundaries") == 1:
                        cv2.circle(
                            img,
                            (roi_root.x, roi_root.y),
                            min_radius,
                            ipc.C_RED,
                            line_width + 4,
                        )
                        cv2.circle(
                            img,
                            (roi_root.x, roi_root.y),
                            max_radius,
                            ipc.C_BLUE,
                            line_width + 4,
                        )
                else:
                    self.result = None
            else:
                self.result = [[x, y, r] for x, y, r in zip(cx, cy, radii)]

            if self.result is not None:
                colors = ipc.build_color_steps(step_count=len(self.result))
                i = 0
                annulus_size = self.get_value_of("annulus_size")
                for center_x, center_y, radius in self.result:
                    cv2.circle(img, (center_x, center_y), radius, colors[i], line_width)
                    if annulus_size > 0 and radius - annulus_size > 0:
                        cv2.circle(
                            img,
                            (center_x, center_y),
                            radius - annulus_size,
                            colors[i],
                            line_width,
                        )
                    i += 1
            wrapper.store_image(
                image=img,
                text="hough_circles",
                text_overlay=self.get_value_of("text_overlay") == 1,
            )
            self.demo_image = img
            res = True
        except Exception as e:
            logger.exception(f'Failed to process {self. name}: "{repr(e)}"')
            res = False
        else:
            pass
        finally:
            return res

    def generate_roi(self, **kwargs):
        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return None
        if self.process_wrapper(**kwargs):
            roi_shape = self.get_value_of("roi_shape")
            roi_type = self.get_value_of("roi_type")
            roi_name = self.get_value_of("roi_name")
            tool_target = self.get_value_of("tool_target")
            circles = sorted(self.result, key=lambda circle_: circle_[2])
            circle = circles[0]
            if roi_shape == "rectangle":
                r = CircleRegion(cx=circle[0], cy=circle[1], radius=circle[2]).as_rect()
                return RectangleRegion(
                    left=r.left,
                    width=r.width,
                    top=r.top,
                    height=r.height,
                    name=roi_name,
                    tag=roi_type,
                    target=tool_target,
                )
            elif roi_shape == "circle":
                annulus_size = self.get_value_of("annulus_size")
                if annulus_size == 0 or (circle[2] - annulus_size <= 0):
                    return CircleRegion(
                        cx=circle[0],
                        cy=circle[1],
                        radius=circle[2],
                        name=roi_name,
                        tag=roi_type,
                        target=tool_target,
                    )
                else:
                    return AnnulusRegion(
                        cx=circle[0],
                        cy=circle[1],
                        radius=circle[2],
                        in_radius=circle[2] - annulus_size,
                        name=roi_name,
                        tag=roi_type,
                        target=tool_target,
                    )
            else:
                return None
        else:
            return None

    def apply_roy(self, **kwargs):
        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return None
        if self.process_wrapper(**kwargs):
            circles = sorted(self.result, key=lambda circle_: circle_[2])
            circle = circles[0]
            roi_name = f"roi_keep_{len(wrapper.rois_list)}"
            wrapper.add_circle_roi(circle[0], circle[1], circle[2], roi_name, "keep")
            target = kwargs.get("target", "source")
            if target == "source":
                res = wrapper.apply_rois(wrapper.current_image)
            elif target == "mask":
                res = wrapper.apply_rois(wrapper.mask)
            else:
                res = None
                logger.error("Unknown ROI target")
            wrapper.store_image(res, roi_name, text_overlay=False)
            return res
        else:
            return wrapper.current_image

    @property
    def name(self):
        return "Hough circles detector"

    @property
    def real_time(self):
        return self.get_value_of("edge_only") == 1

    @property
    def result_name(self):
        return "circles"

    @property
    def output_kind(self):
        return "data"

    @property
    def use_case(self):
        return [ipc.ToolFamily.ROI]

    @property
    def description(self):
        return "Hough circles detector: Perform a circular Hough transform.\nCan generate ROIs"

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
            return ipc.IO_ROI

    def apply_test_values_overrides(self, use_cases: tuple = ()):
        self.set_value_of("enable_cache", 0)

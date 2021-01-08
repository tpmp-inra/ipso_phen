import cv2
import numpy as np
import math

import logging
import os

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))

from ipso_phen.ipapi.base.ipt_abstract import IptBase
from ipso_phen.ipapi.ipt.ipt_edge_detector import IptEdgeDetector
from ipso_phen.ipapi.base.ipt_abstract_analyzer import IptBaseAnalyzer
from ipso_phen.ipapi.base.ip_common import (
    ToolFamily,
    C_GREEN,
    C_LIME,
    C_RED,
    C_BLUE,
    C_LIGHT_STEEL_BLUE,
    all_colors_dict,
    build_color_steps,
)


class IptHoughLines(IptBaseAnalyzer):
    def build_params(self):
        self.add_source_selector(default_value="source")
        self.add_channel_selector(default_value="l")
        self.add_checkbox(
            name="is_apply_rois",
            desc="Apply ROIs to source image",
            default_value=0,
            hint="If true ROIs will be applied to source image",
        )
        self.add_combobox(
            name="method",
            desc="Method",
            default_value="probabilistic",
            values=dict(probabilistic="probabilistic", full="full"),
        )
        self.add_slider(
            name="votes_threshold",
            desc="Votes threshold (P only)",
            default_value=100,
            minimum=0,
            maximum=1000,
            hint="Probabilistic method only",
        )
        self.add_slider(
            name="max_line_gap",
            desc="Max line Gap (P only)",
            default_value=100,
            minimum=0,
            maximum=1000,
            hint="Probabilistic method only",
        )
        self.add_slider(
            name="min_line_size",
            desc="Min line size (P only)",
            default_value=100,
            minimum=0,
            maximum=1000,
            hint="Probabilistic method only",
        )
        self.add_spin_box(
            name="min_angle",
            desc="Minimum line angle",
            default_value=0,
            minimum=0,
            maximum=180,
            hint="0 and 180 both define an horizontal line",
        )
        self.add_spin_box(
            name="max_angle",
            desc="Maximum line angle",
            default_value=180,
            minimum=0,
            maximum=180,
            hint="0 and 180 both define an horizontal line",
        )
        self.add_color_selector(
            name="discarded_color",
            desc="Discarded lines display color",
            default_value="fuchsia",
            enable_none=True,
        )
        self.add_checkbox(name="edge_only", desc="Edge detection only", default_value=0)
        self.add_edge_detector()
        self.add_checkbox(
            name="build_mosaic",
            desc="Build mosaic",
            default_value=0,
            hint="If true edges and result will be displayed side by side",
        )
        self.add_checkbox(
            name="add_lines_detail",
            desc="Add line details to output data",
            default_value=0,
        )

    def add_line(
        self,
        src_img,
        index,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        kept_color,
        discarded_color,
    ) -> bool:

        # if y1 < y2:
        #     x1, y1, x2, y2 = x2, y2, x1, y1
        # elif y1 == y2 and x1 > x2:
        #     x1, y1, x2, y2 = x2, y2, x1, y1
        min_angle = self.get_value_of("min_angle")  # * math.pi / 180
        max_angle = self.get_value_of("max_angle")  # * math.pi / 180
        min_angle, max_angle = min(min_angle, max_angle), max(min_angle, max_angle)
        line_angle = math.atan2(y2 - y1, x2 - x1) * 180 / math.pi * -1
        line_width = max(2, self.wrapper.width // 400)
        dot_size = max(4, self.wrapper.width // 200)
        cv2.circle(src_img, (x1, y1), dot_size, C_GREEN)
        cv2.circle(src_img, (x2, y2), dot_size, C_RED)
        fnt = (cv2.FONT_HERSHEY_SIMPLEX, 0.6)
        cv2.putText(
            src_img,
            f"{index}|{line_angle:.2f}",
            (x1 - 5, y1 - 5),
            fnt[0],
            fnt[1],
            kept_color,
            2,
        )
        if min_angle <= line_angle <= max_angle:
            cv2.line(src_img, (x1, y1), (x2, y2), kept_color, line_width)
            if self.get_value_of("add_lines_detail"):
                self.add_value(f"line_{index}_x1", x1, True)
                self.add_value(f"line_{index}_y1", y1, True)
                self.add_value(f"line_{index}_x2", x2, True)
                self.add_value(f"line_{index}_y2", y2, True)
                self.add_value(f"line_{index}_angle", line_angle, True)
                self.add_value(
                    f"line_{index}_length",
                    math.sqrt(abs(x2 - x1) ** 2 + abs(y2 - y1) ** 2),
                    True,
                )
            return True
        elif discarded_color != "none":
            cv2.line(src_img, (x1, y1), (x2, y2), discarded_color, line_width)
            return False

    def process_wrapper(self, **kwargs):
        """
        Hough lines detector:
        Use the OpenCV functions HoughLines and HoughLinesP to detect lines in an image.
        Real time : False

        Keyword Arguments (in parentheses, argument name):
            * Select source file type (source_file): no clue
            * Channel (channel):
            * Apply ROIs to source image (is_apply_rois): If true ROIs will be applied to source image
            * Method (method):
            * Votes threshold (P only) (votes_threshold): Probabilistic method only
            * Max line Gap (P only) (max_line_gap): Probabilistic method only
            * Min line size (P only) (min_line_size): Probabilistic method only
            * Minimum line angle (min_angle): 0 and 180 both define an horizontal line
            * Maximum line angle (max_angle): 0 and 180 both define an horizontal line
            * Discarded lines display color (discarded_color):
            * Edge detection only (edge_only):
            * Select edge detection operator (operator):
            * Canny's sigma (canny_sigma): Sigma.
            * Canny's first Threshold (canny_first): First threshold for the hysteresis procedure.
            * Canny's second Threshold (canny_second): Second threshold for the hysteresis procedure.
            * Kernel size (kernel_size):
            * Threshold (threshold): Threshold for kernel based operators
            * Apply threshold (apply_threshold):
            * Build mosaic (build_mosaic): If true edges and result will be displayed side by side
            * Add line details to output data (add_lines_detail):
        """
        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return False
        res = False
        try:
            self.data_dict = {}
            votes_threshold = self.get_value_of("votes_threshold", 100)
            max_line_gap = self.get_value_of("max_line_gap", 100)
            min_line_size = self.get_value_of("min_line_size", 100)
            is_apply_rois = self.get_value_of("is_apply_rois", "yes") == "yes"
            is_probabilistic = (
                self.get_value_of("method", "probabilistic") == "probabilistic"
            )
            build_mosaic = self.get_value_of("build_mosaic") == 1
            discarded_color = self.get_value_of(key="discarded_color")
            if discarded_color != "none":
                discarded_color = all_colors_dict[discarded_color]

            # Get the edge
            with IptEdgeDetector(wrapper=wrapper, **self.params_to_dict()) as (res, ed):
                if not res:
                    return
                edges = ed.result
                if self.get_value_of("edge_only") == 1:
                    self.result = ed.result
                    return True
            edges = self.match_image_size_to_source(img=self.to_bit(edges))

            if is_apply_rois:
                wrapper.init_rois()
                edges = wrapper.apply_rois(edges, f"ROIs_{self.input_params_as_str()}")

            src_img = self.wrapper.current_image
            if (
                self.get_value_of("source_file", "source") == "mask"
                and src_img is not None
            ):
                src_img = wrapper.draw_image(
                    src_image=wrapper.current_image,
                    src_mask=src_img,
                    foreground="source",
                    background="bw",
                )
            elif len(src_img.shape) == 2 or (
                len(src_img.shape) == 3 and src_img.shape[2] == 1
            ):
                src_img = np.dstack((src_img, src_img, src_img))
            line_count = 0
            if is_probabilistic:
                self.add_value("line_mode", "probabilistic", True)
                lines = cv2.HoughLinesP(
                    image=edges,
                    rho=1,
                    theta=np.pi / 180,
                    threshold=votes_threshold,
                    minLineLength=min_line_size,
                    maxLineGap=max_line_gap,
                )
                colors = build_color_steps(step_count=len(lines))
                if lines is not None:
                    for i, line in enumerate(lines):
                        x1, y1, x2, y2 = line[0]
                        if self.add_line(
                            src_img,
                            line_count,
                            x1,
                            y1,
                            x2,
                            y2,
                            colors[i],
                            discarded_color,
                        ):
                            line_count += 1
            else:
                self.add_value("line_mode", "full", True)
                lines = cv2.HoughLines(
                    edges, rho=1, theta=np.pi / 180, threshold=votes_threshold
                )
                if lines is not None:
                    h, w = edges.shape[:2]
                    colors = build_color_steps(step_count=len(lines))
                    for i, line in enumerate(lines):
                        for rho, theta in line:
                            a = np.cos(theta)
                            b = np.sin(theta)
                            x0 = a * rho
                            y0 = b * rho
                            x1 = int(x0 + w * (-b))
                            y1 = int(y0 + h * a)
                            x2 = int(x0 - w * (-b))
                            y2 = int(y0 - h * a)
                            x1, y1 = wrapper.constraint_to_image(x1, y1, edges)
                            x2, y2 = wrapper.constraint_to_image(x2, y2, edges)
                            if self.add_line(
                                src_img,
                                line_count,
                                x1,
                                y1,
                                x2,
                                y2,
                                colors[i],
                                discarded_color,
                            ):
                                line_count += 1
            self.result = lines.copy() if lines is not None else None
            self.add_value("line_count", line_count, True)
            wrapper.store_image(src_img, "hough_lines")

            if build_mosaic:
                wrapper.store_image(self.to_uint8(edges), "edges")
                _mosaic_data = np.array(["edges", f"lines_{self.input_params_as_str()}"])
                h, w = wrapper.current_image.shape[:2]
                w *= _mosaic_data.shape[0]
                canvas = wrapper.build_mosaic((h, w, 3), _mosaic_data)
                wrapper.store_image(
                    canvas,
                    f"lines_mosaic__{self.input_params_as_str()}",
                    text_overlay=True,
                )

            res = True
        except Exception as e:
            wrapper.error_holder.add_error(
                new_error_text=f'Failed to process {self. name}: "{repr(e)}"',
                new_error_level=35,
                target_logger=logger,
            )
            res = False
        else:
            pass
        finally:
            return res

    @property
    def name(self):
        return "Hough lines detector"

    @property
    def real_time(self):
        return self.get_value_of("edge_only") == 1

    @property
    def result_name(self):
        return "lines"

    @property
    def output_kind(self):
        return "data"

    @property
    def use_case(self):
        return [ToolFamily.IMAGE_INFO, ToolFamily.FEATURE_EXTRACTION]

    @property
    def description(self):
        return "Use the OpenCV functions HoughLines and HoughLinesP to detect lines in an image."

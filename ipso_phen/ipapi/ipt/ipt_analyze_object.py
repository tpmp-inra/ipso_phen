import cv2
import numpy as np
import os

import logging

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))

from ipso_phen.ipapi.base.ip_common import MaskData
from ipso_phen.ipapi.base.ipt_abstract_analyzer import IptBaseAnalyzer
from ipso_phen.ipapi.base.ip_common import ToolFamily


class IptAnalyzeObject(IptBaseAnalyzer):
    def build_params(self):
        self.add_checkbox(desc="Area", name="area", default_value=1)
        self.add_checkbox(desc="Perimeter", name="perimeter", default_value=1)
        self.add_checkbox(desc="Centroid x", name="centroid_x", default_value=1)
        self.add_checkbox(desc="Centroid y", name="centroid_y", default_value=1)
        self.add_checkbox(desc="Convex hull area", name="hull_area", default_value=1)
        self.add_checkbox(desc="Shape solidity", name="shape_solidity", default_value=1)
        self.add_checkbox(desc="Shape extend", name="shape_extend", default_value=1)
        self.add_checkbox(
            desc="Straight bounding rectangle left",
            name="straight_bounding_rectangle_left",
            default_value=1,
        )
        self.add_checkbox(
            desc="Straight bounding rectangle width",
            name="straight_bounding_rectangle_width",
            default_value=1,
        )
        self.add_checkbox(
            desc="Straight bounding rectangle top",
            name="straight_bounding_rectangle_top",
            default_value=1,
        )
        self.add_checkbox(
            desc="Straight bounding rectangle height",
            name="straight_bounding_rectangle_height",
            default_value=1,
        )
        self.add_checkbox(
            desc="Rotated bounding rectangle cx",
            name="rotated_bounding_rectangle_cx",
            default_value=1,
        )
        self.add_checkbox(
            desc="Rotated bounding rectangle cy",
            name="rotated_bounding_rectangle_cy",
            default_value=1,
        )
        self.add_checkbox(
            desc="Rotated bounding rectangle width",
            name="rotated_bounding_rectangle_width",
            default_value=1,
        )
        self.add_checkbox(
            desc="Rotated bounding rectangle height",
            name="rotated_bounding_rectangle_height",
            default_value=1,
        )
        self.add_checkbox(
            desc="Rotated bounding rectangle rotation",
            name="rotated_bounding_rectangle_rotation",
            default_value=1,
        )
        self.add_checkbox(
            desc="Minimum enclosing circle cx",
            name="minimum_enclosing_circle_cx",
            default_value=1,
        )
        self.add_checkbox(
            desc="Minimum enclosing circle cy",
            name="minimum_enclosing_circle_cy",
            default_value=1,
        )
        self.add_checkbox(
            desc="Minimum enclosing circle radius",
            name="minimum_enclosing_circle_radius",
            default_value=1,
        )
        self.add_checkbox(
            desc="Shape height",
            name="shape_height",
            default_value=1,
        )
        self.add_checkbox(
            desc="Shape width",
            name="shape_width",
            default_value=1,
        )
        self.add_checkbox(
            desc="Shape minimum width",
            name="shape_width_min",
            default_value=1,
        )
        self.add_checkbox(
            desc="Shape maximum width",
            name="shape_width_max",
            default_value=1,
        )
        self.add_checkbox(
            desc="Shape average width",
            name="shape_width_avg",
            default_value=1,
        )
        self.add_checkbox(
            desc="Shape width standard deviation",
            name="shape_width_std",
            default_value=1,
        )
        self.add_separator(name="s1")
        self.add_spin_box(
            name="quantile_width",
            desc="Select amount of quantiles for width analysis",
            default_value=4,
            minimum=0,
            maximum=20,
        )
        self.add_spin_box(
            name="line_width",
            desc="Draw line width (debug images)",
            default_value=4,
            minimum=1,
            maximum=100,
        )
        self.add_spin_box(
            name="centroid_width",
            desc="Draw centroid width (debug images)",
            default_value=10,
            minimum=1,
            maximum=100,
        )

    def process_wrapper(self, **kwargs):
        """
        Analyze object:
        Analyses object and returns morphologic data.
        Needs a mask as an input.
        Normally used in a pipeline after a clean mask is created.
        Real time: False

        Keyword Arguments (in parentheses, argument name):
            * Area (area):
            * Centroid x (centroid_x):
            * Centroid y (centroid_y):
            * Convex hull area (hull_area):
            * Shape solidity (shape_solidity):
            * Shape extend (shape_extend):
            * Straight bounding rectangle left (straight_bounding_rectangle_left):
            * Straight bounding rectangle width (straight_bounding_rectangle_width):
            * Straight bounding rectangle top (straight_bounding_rectangle_top):
            * Straight bounding rectangle height (straight_bounding_rectangle_height):
            * Rotated bounding rectangle cx (rotated_bounding_rectangle_cx):
            * Rotated bounding rectangle cy (rotated_bounding_rectangle_cy):
            * Rotated bounding rectangle width (rotated_bounding_rectangle_width):
            * Rotated bounding rectangle height (rotated_bounding_rectangle_height):
            * Rotated bounding rectangle rotation (rotated_bounding_rectangle_rotation):
            * Minimum enclosing circle cx (minimum_enclosing_circle_cx):
            * Minimum enclosing circle cy (minimum_enclosing_circle_cy):
            * Minimum enclosing circle radius (minimum_enclosing_circle_radius):
            * Shape height (shape_height):
            * Shape width (shape_width):
            * Shape minimum width (shape_width_min):
            * Shape maximum width (shape_width_max):
            * Shape average width (shape_width_avg):
            * Shape width standard deviation (shape_width_std):
            * Select amount of quantiles for width analysis (quantile_width):
            * Draw line width (debug images) (line_width):
            * Draw centroid width (debug images) (centroid_width):
        """

        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return False

        res = False
        try:
            self.data_dict = {}
            img = wrapper.current_image
            mask = self.get_mask()
            if mask is None:
                logger.error(f"FAIL {self.name}: mask must be initialized")
                return

            obj, mask = wrapper.prepare_analysis(
                wrapper.draw_image(
                    src_mask=mask,
                    background="silver",
                    foreground="source",
                ),
                mask,
            )

            # Valid objects can only be analyzed if they have >= 5 vertices
            if len(obj) < 5:
                logger.error(f"Object has only {len(obj)} vertices, most probably noise")
                res = False
                return
            res = True

            ori_img = np.copy(img)
            hull = cv2.convexHull(obj)
            m = cv2.moments(mask, binaryImage=True)
            area = m["m00"]
            if area:
                # x and y position (bottom left?) and extent x (width) and extent y (height)
                x, y, width, height = cv2.boundingRect(obj)

                # Centroid (center of mass x, center of mass y)
                cmx, cmy = (m["m10"] / m["m00"], m["m01"] / m["m00"])

                # Store Shape Data
                self.add_value("area", area)
                self.add_value("centroid_x", cmx)
                self.add_value("centroid_y", cmy)
                self.add_value("perimeter", cv2.arcLength(obj, True))

                hull_area = cv2.contourArea(hull)
                self.add_value("hull_area", hull_area)
                self.add_value("shape_solidity", area / hull_area)

                x, y, w, h = cv2.boundingRect(obj)
                self.add_value("shape_extend", float(area) / (w * h))
                self.add_value("straight_bounding_rectangle_left", x)
                self.add_value("straight_bounding_rectangle_width", w)
                self.add_value("straight_bounding_rectangle_top", y)
                self.add_value("straight_bounding_rectangle_height", h)

                (x, y), (w, h), r = cv2.minAreaRect(obj)
                wl = max(w, h)
                hl = min(w, h)
                self.add_value(key="rotated_bounding_rectangle_cx", value=x)
                self.add_value(key="rotated_bounding_rectangle_cy", value=y)
                self.add_value(key="rotated_bounding_rectangle_width", value=wl)
                self.add_value(key="rotated_bounding_rectangle_height", value=hl)
                self.add_value(key="rotated_bounding_rectangle_rotation", value=r + 180)

                (x, y), radius = cv2.minEnclosingCircle(obj)
                self.add_value("minimum_enclosing_circle_cx", x)
                self.add_value("minimum_enclosing_circle_cy", y)
                self.add_value("minimum_enclosing_circle_radius", radius)

                self.add_value("shape_height", height)
                # Some new f(r)iends
                mask_data = MaskData(mask)
                _, _, _, min_, max_, avg_, std_ = mask_data.width_quantile_stats(
                    1, 0, tag=0
                )
                self.add_value("shape_width", width)
                self.add_value("shape_width_min", min_)
                self.add_value("shape_width_max", max_)
                self.add_value("shape_width_avg", avg_)
                self.add_value("shape_width_std", std_)

                line_width = self.get_value_of("line_width")
                centroid_width = self.get_value_of("centroid_width")

                # Start with the sure ones
                self.demo_image = wrapper.draw_image(
                    src_image=ori_img,
                    src_mask=mask,
                    objects=obj,
                    background="bw",
                    foreground="source",
                    contour_thickness=line_width,
                    hull_thickness=line_width if self.has_param("hull_area") else 0,
                    width_thickness=line_width if self.has_param("shape_width") else 0,
                    height_thickness=line_width if self.has_param("shape_height") else 0,
                    centroid_width=centroid_width if self.has_param("centroid_x") else 0,
                    centroid_line_width=line_width,
                )
                wrapper.store_image(
                    image=self.demo_image,
                    text="shapes",
                )
                wrapper.store_image(
                    image=wrapper.draw_image(
                        src_image=mask,
                        src_mask=mask,
                        objects=obj,
                        background="source",
                        foreground="source",
                        contour_thickness=line_width,
                        hull_thickness=line_width if self.has_param("hull_area") else 0,
                        width_thickness=line_width
                        if self.has_param("shape_width")
                        else 0,
                        height_thickness=line_width
                        if self.has_param("shape_height")
                        else 0,
                        centroid_width=centroid_width
                        if self.has_param("centroid_x")
                        else 0,
                        centroid_line_width=line_width,
                    ),
                    text="shapes_on_mask",
                )
                # Add new ones
                draw_circle = self.has_key_matching("minimum_enclosing_circle")
                draw_bd_rect = self.has_key_matching("rotated_bounding_rectangle")
                draw_st_rect = self.has_key_matching("straight_bounding_rectangle")
                if draw_circle or draw_bd_rect or draw_st_rect:
                    wrapper.store_image(
                        image=wrapper.draw_image(
                            src_image=ori_img,
                            src_mask=mask,
                            objects=obj,
                            background="bw",
                            foreground="source",
                            enclosing_circle_thickness=line_width if draw_circle else 0,
                            bounding_rec_thickness=line_width if draw_bd_rect else 0,
                            straight_bounding_rec_thickness=line_width
                            if draw_st_rect
                            else 0,
                        ),
                        text="more_shapes",
                    )
                    wrapper.store_image(
                        image=wrapper.draw_image(
                            src_image=mask,
                            src_mask=mask,
                            objects=obj,
                            background="source",
                            foreground="source",
                            enclosing_circle_thickness=line_width if draw_circle else 0,
                            bounding_rec_thickness=line_width if draw_bd_rect else 0,
                            straight_bounding_rec_thickness=line_width
                            if draw_st_rect
                            else 0,
                        ),
                        text="more_shapes_on_mask",
                    )

                # handle width quantiles
                n = self.get_value_of("quantile_width")
                if n > 0:
                    kind = "width"
                    msk_dt = MaskData(mask)
                    qtl_img = np.zeros_like(mask)
                    qtl_img = np.dstack((qtl_img, qtl_img, qtl_img))
                    for i in range(n):
                        (
                            total_,
                            hull_,
                            solidity_,
                            min_,
                            max_,
                            avg_,
                            std_,
                        ) = msk_dt.width_quantile_stats(n, i, tag=i)
                        self.add_value(f"quantile_width_{i + 1}_{n}_area", total_, True)
                        self.add_value(f"quantile_width_{i + 1}_{n}_hull", hull_, True)
                        self.add_value(
                            f"quantile_width_{i + 1}_{n}_solidity", solidity_, True
                        )
                        self.add_value(
                            f"quantile_width_{i + 1}_{n}_min_{kind}", min_, True
                        )
                        self.add_value(
                            f"quantile_width_{i + 1}_{n}_max_{kind}", max_, True
                        )
                        self.add_value(
                            f"quantile_width_{i + 1}_{n}_avg_{kind}", avg_, True
                        )
                        self.add_value(
                            f"quantile_width_{i + 1}_{n}_std_{kind}", std_, True
                        )
                        p_qt_msk = msk_dt.height_quantile_mask(
                            total=n, index=i, colour=int((i + 1) / (n + 1) * 255)
                        )
                        qtl_img = cv2.bitwise_or(
                            qtl_img,
                            np.dstack(
                                (np.zeros_like(mask), p_qt_msk, np.zeros_like(mask))
                            ),
                        )
                    wrapper.store_image(qtl_img, f"quantiles_width_{n}")
            else:
                res = False
        except Exception as e:
            logger.error(f'Failed to process {self. name}: "{repr(e)}"')
            res = False
        else:
            pass
        finally:
            self.result = len(self.data_dict) > 0
            return res

    @property
    def name(self):
        return "Analyze object"

    @property
    def real_time(self):
        return False

    @property
    def result_name(self):
        return "dictionary"

    @property
    def output_kind(self):
        return "dictionnary"

    @property
    def use_case(self):
        return [ToolFamily.FEATURE_EXTRACTION]

    @property
    def description(self):
        return "Analyses object and returns morphologic data.\nNeeds a mask as an input.\nNormally used in a pipeline after a clean mask is created."

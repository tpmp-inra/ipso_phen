import os
import logging
import random

import numpy as np
import cv2

from skimage.filters import sobel
from skimage.transform import hough_circle, hough_circle_peaks


from ipso_phen.ipapi.base.ipt_abstract_analyzer import IptBaseAnalyzer
from ipso_phen.ipapi.base import ip_common as ipc


logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))


class IptSplitOverlappedEllipses(IptBaseAnalyzer):
    def build_params(self):
        self.add_enabled_checkbox()
        self.add_checkbox(
            name="concave",
            desc="Use concave detection method",
            default_value=1,
        )
        self.add_checkbox(
            name="hough",
            desc="Use Hough detection method",
            default_value=1,
        )
        self.add_checkbox(
            name="median",
            desc="Use median area detection method",
            default_value=1,
        )
        self.add_separator()
        self.add_label(desc="Comman params")
        self.add_spin_box(
            name="approx_factor",
            desc="Approximation factor",
            default_value=100,
            minimum=0,
            maximum=100,
        )
        self.add_spin_box(
            name="dbg_font_scale",
            desc="Debug font scale",
            default_value=2,
            minimum=1,
            maximum=100,
        )
        self.add_spin_box(
            name="dbg_font_thickness",
            desc="Debug font thickness",
            default_value=4,
            minimum=1,
            maximum=100,
        )
        self.add_spin_box(
            name="min_size_to_split",
            desc="Split object if size is over",
            default_value=0,
            minimum=0,
            maximum=100000000,
        )
        self.add_separator()
        self.add_label(desc="Concave pointe detection method")
        self.add_spin_box(
            name="residue_size",
            desc="Residue size",
            default_value=10,
            minimum=0,
            maximum=10000000,
            hint="Consider all object below this size as noise when analysing objects",
        )
        self.add_separator()
        self.add_label(desc="Hough circle detection method")
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
            name="min_distance",
            desc="Minimum distance between two circles",
            default_value=20,
            minimum=1,
            maximum=2000,
            hint="Remove circles that are too close",
        )
        self.add_spin_box(
            name="step_radius",
            desc="Radius granularity",
            default_value=10,
            minimum=0,
            maximum=100,
            hint="Steps for scanning radius",
        )

    def handle_countour(self, contour, min_size_to_split):
        return (
            cv2.contourArea(contour) > min_size_to_split
            and cv2.isContourConvex(
                cv2.approxPolyDP(
                    contour,
                    (self.get_value_of("approx_factor") / 100)
                    * cv2.arcLength(contour, True),
                    True,
                )
            )
            is True
        )

    def write_result(self, image, method, value):
        cv2.putText(
            img=image,
            text=f"{method} - {value}",
            org=(image.shape[1] // 4, image.shape[0] // 4),
            fontFace=cv2.FONT_HERSHEY_SIMPLEX,
            fontScale=self.get_value_of("dbg_font_scale") * 4,
            color=(0, 255, 0),
            thickness=self.get_value_of("dbg_font_thickness") * 4,
        )
        return image

    def hough_detection(self, wrapper, mask, contours):
        min_size_to_split = self.get_value_of("min_size_to_split")
        min_radius = self.get_value_of("min_radius")
        max_radius = self.get_value_of("max_radius")
        step_radius = self.get_value_of("step_radius")
        min_distance = self.get_value_of(
            "min_distance",
            scale_factor=wrapper.scale_factor,
        )
        dbg_font_scale = self.get_value_of("dbg_font_scale")
        dbg_font_thickness = self.get_value_of("dbg_font_thickness")
        total_ellipses = 0
        dbg_img = np.dstack((mask, mask, mask))
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            handled_ = cv2.contourArea(cnt) > min_size_to_split
            if handled_ is True:
                local_edges = self.to_uint8(sobel(mask[y : y + h, x : x + w]))
                local_edges[local_edges < 60] = 0
                local_edges[local_edges >= 60] = 255

                # Detect circles
                hough_radii = np.arange(min_radius, max_radius, step_radius)
                hough_res = hough_circle(local_edges, hough_radii)

                # Select the most prominent n circles
                accu, cx, cy, radii = hough_circle_peaks(
                    hough_res,
                    hough_radii,
                    min_xdistance=min_distance,
                    min_ydistance=min_distance,
                )

                count_ = 0
                for x_, y_, r_ in [[x, y, r] for x, y, r in zip(cx, cy, radii)]:
                    if cv2.pointPolygonTest(cnt, (x_ + x, y_ + y), False) > -1:
                        cv2.circle(
                            dbg_img,
                            (x_ + x, y_ + y),
                            r_,
                            (
                                random.randint(50, 200),
                                random.randint(50, 200),
                                random.randint(50, 200),
                            ),
                            4,
                        )
                        count_ += 1
            else:
                count_ = 1

            total_ellipses += count_

            cx = x + w // 2 - 10
            cy = y + h // 2
            cv2.putText(
                img=dbg_img,
                text=str(count_),
                org=(cx, cy),
                fontFace=cv2.FONT_HERSHEY_SIMPLEX,
                fontScale=dbg_font_scale,
                color=(0, 255, 0),
                thickness=dbg_font_thickness,
            )
            if handled_ is True:
                cv2.putText(
                    img=dbg_img,
                    text=f"{x}, {y}",
                    org=(x + w, y + h),
                    fontFace=cv2.FONT_HERSHEY_SIMPLEX,
                    fontScale=dbg_font_scale / 2,
                    color=(0, 0, 255),
                    thickness=dbg_font_thickness // 2,
                )
                cv2.putText(
                    img=dbg_img,
                    text=f"{cv2.contourArea(cnt)}",
                    org=(x + w, y),
                    fontFace=cv2.FONT_HERSHEY_SIMPLEX,
                    fontScale=dbg_font_scale / 2,
                    color=(0, 0, 255),
                    thickness=dbg_font_thickness // 2,
                )

        return {
            "count": total_ellipses,
            "demo_image": self.write_result(
                image=dbg_img,
                method="Hough detection",
                value=total_ellipses,
            ),
        }

    def median_area_detection(self, wrapper, mask, contours):
        if len(contours) > 0:
            areas: np.array = np.array([cv2.contourArea(cnt) for cnt in contours])
            total_ellipses = round(np.sum(areas) / np.median(areas))
        else:
            total_ellipses = 0

        return {
            "count": total_ellipses,
            "demo_image": self.write_result(
                image=np.dstack((mask, mask, mask)),
                method="median area",
                value=total_ellipses,
            ),
        }

    def concave_detection(self, wrapper, mask, contours):

        min_size_to_split = self.get_value_of("min_size_to_split")
        dbg_font_scale = self.get_value_of("dbg_font_scale")
        dbg_font_thickness = self.get_value_of("dbg_font_thickness")
        residue_size = self.get_value_of("residue_size")
        total_ellipses = 0
        dbg_img = np.dstack(
            (
                np.zeros_like(mask),
                np.zeros_like(mask),
                np.zeros_like(mask),
            )
        )
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            clr = (
                random.randint(50, 200),
                random.randint(50, 200),
                random.randint(50, 200),
            )
            handled_ = cv2.contourArea(cnt) > min_size_to_split
            if handled_ is True:
                work_img = dbg_img.copy()
                cv2.drawContours(
                    image=work_img,
                    contours=[cv2.convexHull(cnt)],
                    contourIdx=0,
                    color=ipc.C_WHITE,
                    thickness=-1,
                )
                cv2.drawContours(
                    image=work_img,
                    contours=[cnt],
                    contourIdx=0,
                    color=ipc.C_BLACK,
                    thickness=-1,
                )
                work_img = work_img[y : y + h, x : x + w].copy()
                count_ = 0
                for c in ipc.get_contours(
                    mask=work_img[:, :, 0],
                    retrieve_mode=cv2.RETR_LIST,
                    method=cv2.CHAIN_APPROX_SIMPLE,
                ):
                    if (cv2.contourArea(c, True) < 0) and (
                        cv2.contourArea(c) >= residue_size
                    ):
                        cv2.drawContours(
                            image=work_img,
                            contours=[c],
                            contourIdx=0,
                            color=ipc.C_GREEN,
                            thickness=-1,
                        )
                        count_ += 1
                    else:
                        cv2.drawContours(
                            image=work_img,
                            contours=[c],
                            contourIdx=0,
                            color=ipc.C_RED,
                            thickness=-1,
                        )
                dbg_img[y : y + h, x : x + w] = work_img
                if count_ < 2:
                    count_ += 1
            else:
                count_ = 1
            cv2.drawContours(dbg_img, [cnt], 0, ipc.C_WHITE, -1)

            total_ellipses += count_

            cx = x + w // 2 - 10
            cy = y + h // 2
            cv2.putText(
                img=dbg_img,
                text=str(count_),
                org=(cx, cy),
                fontFace=cv2.FONT_HERSHEY_SIMPLEX,
                fontScale=dbg_font_scale,
                color=(0, 255, 0),
                thickness=dbg_font_thickness,
            )
            if handled_ is True:
                cv2.putText(
                    img=dbg_img,
                    text=f"{x}, {y}",
                    org=(x + w, y + h),
                    fontFace=cv2.FONT_HERSHEY_SIMPLEX,
                    fontScale=dbg_font_scale / 2,
                    color=(0, 0, 255),
                    thickness=dbg_font_thickness // 2,
                )
                cv2.putText(
                    img=dbg_img,
                    text=f"{cv2.contourArea(cnt)}",
                    org=(x + w, y),
                    fontFace=cv2.FONT_HERSHEY_SIMPLEX,
                    fontScale=dbg_font_scale / 2,
                    color=(0, 0, 255),
                    thickness=dbg_font_thickness // 2,
                )

        return {
            "count": total_ellipses,
            "demo_image": self.write_result(
                image=dbg_img,
                method="concave detection",
                value=total_ellipses,
            ),
        }

    def process_wrapper(self, **kwargs):
        """
        Split overlapped ellipses:
        Split overlapped ellipses.
                Three methods are available: Concave points detection, Hough circle detection and extrapolation from median area.
        Real time: True

        Keyword Arguments (in parentheses, argument name):
            * Activate tool (enabled): Toggle whether or not tool is active
            * Use concave detection method (concave):
            * Use Hough detection method (hough):
            * Use median area detection method (median):
            * Approximation factor (approx_factor):
            * Debug font scale (dbg_font_scale):
            * Debug font thickness (dbg_font_thickness):
            * Split object if size is over (min_size_to_split):
            * Residue size (residue_size): Consider all object below this size as noise when analysing objects
            * Minimal radius to consider (min_radius): All circles smaller than this will be ignored
            * Maximal radius to consider (max_radius): All circles bigger than this will be ignored
            * Minimum distance between two circles (min_distance): Remove circles that are too close
            * Radius granularity (step_radius): Steps for scanning radius
        --------------"""

        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return False

        res = False
        try:
            if self.get_value_of("enabled") == 1:
                method = self.get_value_of("method")

                mask = self.get_mask()
                if mask is None:
                    logger.error(
                        "Failure Split overlapped ellipses: mask must be initialized"
                    )
                    return

                # Get source contours
                contours = [
                    c
                    for c in ipc.get_contours(
                        mask=mask,
                        retrieve_mode=cv2.RETR_LIST,
                        method=cv2.CHAIN_APPROX_SIMPLE,
                    )
                    if (cv2.contourArea(c, True) < 0)
                ]
                contours.sort(key=lambda x: cv2.contourArea(x), reverse=True)

                demo_images = []
                if self.get_value_of("concave") == 1:
                    res = self.concave_detection(
                        wrapper=wrapper,
                        mask=mask,
                        contours=contours,
                    )
                    demo_images.append(res["demo_image"])
                    self.add_value(
                        key="ellipses_concave_method",
                        value=res["count"],
                        force_add=True,
                    )
                if self.get_value_of("hough") == 1:
                    res = self.hough_detection(
                        wrapper=wrapper,
                        mask=mask,
                        contours=contours,
                    )
                    demo_images.append(res["demo_image"])
                    self.add_value(
                        key="ellipses_hough_method",
                        value=res["count"],
                        force_add=True,
                    )
                if self.get_value_of("median") == 1:
                    res = self.median_area_detection(
                        wrapper=wrapper,
                        mask=mask,
                        contours=contours,
                    )
                    demo_images.append(res["demo_image"])
                    self.add_value(
                        key="ellipses_median_method",
                        value=res["count"],
                        force_add=True,
                    )

                if len(demo_images) == 3:
                    demo_images.append(wrapper.current_image)

                self.demo_image = wrapper.auto_mosaic(demo_images)

                res = True
            else:
                wrapper.store_image(wrapper.current_image, "current_image")
                res = True
        except Exception as e:
            res = False
            logger.error(f"Split overlapped ellipses FAILED, exception: {repr(e)}")
        else:
            pass
        finally:
            return res

    @property
    def name(self):
        return "Split overlapped ellipses"

    @property
    def package(self):
        return "Me"

    @property
    def is_wip(self):
        return False

    @property
    def real_time(self):
        return True

    @property
    def result_name(self):
        "dictionary"

    @property
    def output_kind(self):
        "dictionary"

    @property
    def use_case(self):
        return ["Feature extraction"]

    @property
    def description(self):
        return """Split overlapped ellipses.
        Three methods are available: Concave points detection, Hough circle detection and extrapolation from median area."""

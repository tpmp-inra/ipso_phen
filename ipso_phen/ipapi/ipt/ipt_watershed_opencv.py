import cv2
import numpy as np
from scipy import ndimage

import logging
import os

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))

from ipso_phen.ipapi.base.ip_common import (
    DEFAULT_COLOR_MAP,
    ToolFamily,
)
from ipso_phen.ipapi.base.ipt_abstract_merger import IptBaseMerger


class IptWatershedOpenCv(IptBaseMerger):
    def build_params(self):
        self.add_source_selector(default_value="source")
        self.add_slider(
            name="dilate_iter",
            desc="Dilation iterations count",
            default_value=5,
            minimum=0,
            maximum=31,
        )
        self.add_slider(
            name="min_area",
            desc="Min zone area ",
            default_value=1200,
            minimum=-1,
            maximum=50000,
        )
        self.add_slider(
            name="distance_threshold",
            desc="Distance threshold",
            default_value=100,
            minimum=0,
            maximum=255,
        )
        self.add_combobox(
            name="post_process",
            desc="Post process",
            default_value="none",
            values=dict(none="none", merge_labels="merge labels"),
        )
        self.add_hierarchy_threshold()

    def process_wrapper(self, **kwargs):
        """
        Watershed OpenCv: Performs watershed using OpenCV implementation

        Real time : No

        Keyword Arguments (in parentheses, argument name):
            * Select source file type (source_file): Selected source
            * Dilation iterations count (dilate_iter): Dilations with kernel size 3 to be performed before
            * Min zone area  (min_area): Minimum contour area allowed
            * Distance threshold (distance_threshold): Minimum distance for distance map
            * Post process (post_process): Merge labels or not
            * Label merger threshold {hierarchy_threshold}: Regions connected by an edge with weight smaller than thresh are merged
        """
        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return False

        dilate_iter = self.get_value_of("dilate_iter")
        distance_threshold = self.get_value_of("distance_threshold")
        source_type = self.get_value_of("source_file")
        min_area = self.get_value_of("min_area")
        post_process = self.get_value_of("post_process")

        res = True
        try:
            src_img = self.wrapper.current_image
            if src_img is None:
                return False

            thresh = wrapper.mask
            if thresh is None:
                wrapper.process_image(threshold_only=True)
                thresh = wrapper.mask
                if thresh is None:
                    logger.error("Watershed needs a calculated mask to start")
                    return False

            if source_type == "cropped_source":
                keep_roi = None
                for roi in wrapper.rois_list:
                    if roi.tag == "keep":
                        keep_roi = roi
                        break
                if keep_roi is not None:
                    keep_roi = keep_roi.as_rect()
                    thresh = thresh[
                        keep_roi.top : keep_roi.bottom, keep_roi.left : keep_roi.right
                    ]

            border = wrapper.dilate(thresh, 3, proc_times=dilate_iter)
            border = border - wrapper.erode(border, 3, proc_times=2)
            wrapper.store_image(
                border, f"border_{self.input_params_as_str()}", text_overlay=True
            )

            dt = cv2.distanceTransform(thresh, 2, 3)
            dt = ((dt - dt.min()) / (dt.max() - dt.min()) * 255).astype(np.uint8)
            wrapper.store_image(
                cv2.applyColorMap(dt, DEFAULT_COLOR_MAP),
                f"dist_transform_{self.input_params_as_str()}",
                text_overlay=True,
            )
            _, dt = cv2.threshold(dt, distance_threshold, 255, cv2.THRESH_BINARY)
            wrapper.store_image(
                dt,
                f"dist_transform_threshold_{self.input_params_as_str()}",
                text_overlay=True,
            )
            labels, ncc = ndimage.label(dt)
            labels = labels * (255 / (ncc + 1))
            # Completing the markers now.
            labels[border == 255] = 255

            labels = labels.astype(np.int32)
            cv2.watershed(src_img, labels)
            if post_process != "none":
                post_labels = labels.copy()
            else:
                post_labels = None

            self.result = labels.copy()
            labels[labels == -1] = 0
            labels = labels.astype(np.uint8)
            water_img = cv2.applyColorMap(255 - labels, DEFAULT_COLOR_MAP)
            wrapper.store_image(
                water_img,
                "watershed_vis_v2_{self._params_to_string(**kwargs)}",
                text_overlay=True,
            )

            self.print_segmentation_labels(
                water_img,
                labels,
                dbg_suffix="watershed_opencv",
                source_image=src_img.copy(),
                min_size=min_area,
            )

            if post_process == "merge_labels":
                res = self._merge_labels(src_img.copy(), labels=post_labels, **kwargs)
            else:
                res = True

        except Exception as e:
            res = False
            logger.error(f'Failed to process {self. name}: "{repr(e)}"')
        else:
            res = True
        finally:
            return res

    @property
    def name(self):
        return "Watershed OpenCV"

    @property
    def is_wip(self):
        return True

    @property
    def real_time(self):
        return False

    @property
    def result_name(self):
        return "labels"

    @property
    def output_kind(self):
        return "labels"

    @property
    def use_case(self):
        return [ToolFamily.CLUSTERING, ToolFamily.FEATURE_EXTRACTION]

    @property
    def description(self):
        return "Watershed OpenCv: Performs watershed using OpenCV implementation.\nNeeds an initialized mask to run."

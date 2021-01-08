import cv2
import numpy as np
from scipy import ndimage
from skimage.feature import peak_local_max
from skimage.morphology import watershed

import logging
import os

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))

from ipso_phen.ipapi.base.ip_common import (
    DEFAULT_COLOR_MAP,
    ToolFamily,
)
from ipso_phen.ipapi.base.ipt_abstract_merger import IptBaseMerger


class IptWatershedSkimage(IptBaseMerger):
    def build_params(self):
        self.add_slider(
            name="morph_op",
            desc="Close/Open, <0 Close, >0 Open",
            default_value=0,
            minimum=-31,
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
            name="compactness",
            desc="Compactness",
            default_value=0,
            minimum=0,
            maximum=1000,
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
        Watershed Skimage: Performs watershed with scikit-image implementation

        Real time : No

        Keyword Arguments (in parentheses, argument name):
            * Close/Open, <0 Close, >0 Open (morph_op): Starting morphology operator
            * Min zone area  (min_area): Minimum contour area allowed
            * Compactness (compactness): Use compact watershed with given compactness parameter. Higher values result in more regularly-shaped watershed basins.
            * Post process (post_process): Merge labels or not
            * Label merger threshold {hierarchy_threshold}: Regions connected by an edge with weight smaller than thresh are merged
        """
        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return False

        min_area = self.get_value_of("min_area")
        morph_op = self.get_value_of("morph_op")
        compactness = self.get_value_of("compactness") / 1000
        post_process = self.get_value_of("post_process")

        res = False
        try:
            thresh = wrapper.mask
            if thresh is None:
                wrapper.process_image(threshold_only=True)
                thresh = wrapper.mask
                if thresh is None:
                    logger.error("Watershed needs a calculated mask to start")
                    return False

            if morph_op > 0:
                if morph_op % 2 == 0:
                    morph_op += 1
                thresh = wrapper.open(thresh, morph_op)
            elif morph_op < 0:
                if morph_op % 2 == 0:
                    morph_op -= 1
                thresh = wrapper.close(thresh, abs(morph_op))

            dist_transform = ndimage.distance_transform_edt(thresh)
            wrapper.store_image(
                cv2.applyColorMap(np.uint8(dist_transform), DEFAULT_COLOR_MAP),
                f"dist_transform_{self.input_params_as_str()}",
                text_overlay=True,
            )
            local_max = peak_local_max(
                dist_transform, indices=False, min_distance=20, labels=thresh
            )

            # perform a connected component analysis on the local peaks,
            # using 8-connectivity, then appy the Watershed algorithm
            markers = ndimage.label(local_max, structure=np.ones((3, 3)))[0]
            labels = watershed(
                -dist_transform,
                markers,
                mask=wrapper.erode(thresh, 5),
                compactness=compactness,
            )
            if post_process != "none":
                post_labels = labels.copy()
            else:
                post_labels = None

            self.result = labels.copy()
            labels[labels == -1] = 0
            labels = (
                (labels - labels.min()) / (labels.max() - labels.min()) * 255
            ).astype(np.uint8)
            water_img = cv2.applyColorMap(255 - labels, DEFAULT_COLOR_MAP)
            wrapper.store_image(
                water_img,
                f"watershed_vis_{self.input_params_as_str()}",
                text_overlay=True,
            )

            self.print_segmentation_labels(
                water_img, labels, dbg_suffix="watershed_skimage", min_size=min_area
            )

            if post_process == "merge_labels":
                res = self._merge_labels(
                    wrapper.current_image, labels=post_labels, **kwargs
                )
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
        return "Watershed Skimage"

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
        return "Watershed Skimage: Performs watershed with scikit-image implementation\nNeeds an initialized mask to run."

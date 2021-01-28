import cv2
import numpy as np
from scipy import ndimage
from skimage.feature import peak_local_max
from skimage.segmentation import watershed

import logging
import os

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))

from ipso_phen.ipapi.base.ip_common import (
    DEFAULT_COLOR_MAP,
    ToolFamily,
)
from ipso_phen.ipapi.base.ipt_abstract_analyzer import IptBaseAnalyzer


class IptWatershedSkimage(IptBaseAnalyzer):
    def build_params(self):
        self.add_spin_box(
            name="morph_op",
            desc="Close/Open, <0 Close, >0 Open",
            default_value=0,
            minimum=-31,
            maximum=31,
        )
        self.add_spin_box(
            name="min_distance",
            desc="Minimum distance between 2 objects centers",
            default_value=20,
            maximum=10000,
            minimum=1,
        )
        self.add_spin_box(
            name="min_area",
            desc="Min zone area ",
            default_value=1200,
            minimum=-1,
            maximum=50000,
        )
        self.add_spin_box(
            name="compactness",
            desc="Compactness",
            default_value=0,
            minimum=0,
            maximum=1000,
        )
        self.add_text_input(
            name="objects_name",
            desc="CSV key",
            default_value="objects_positions",
        )

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

        res = False
        try:
            thresh = wrapper.mask
            if thresh is None:
                wrapper.process_image(threshold_only=True)
                thresh = self.get_mask()
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
                f"dist_transform",
            )
            local_max = peak_local_max(
                dist_transform,
                indices=False,
                min_distance=self.get_value_of("min_distance"),
                labels=thresh,
            )

            # perform a connected component analysis on the local peaks,
            # using 8-connectivity, then apply the Watershed algorithm
            markers = ndimage.label(local_max, structure=np.ones((3, 3)))[0]
            labels = watershed(
                image=-dist_transform,
                markers=markers,
                mask=wrapper.erode(thresh, 5),
                compactness=compactness,
                watershed_line=True,
            )

            self.result = labels.copy()
            labels[labels == -1] = 0
            labels = (
                (labels - labels.min()) / (labels.max() - labels.min()) * 255
            ).astype(np.uint8)
            water_img = cv2.applyColorMap(255 - labels, DEFAULT_COLOR_MAP)
            wrapper.store_image(water_img, f"watershed_vis")

            objects = self.get_labels_as_dict(
                watershed_image=water_img,
                labels=labels,
                min_size=min_area,
            )
            self.add_value(
                key=self.get_value_of("objects_name"),
                value=objects,
                force_add=True,
            )
            self.add_value(
                key=self.get_value_of("objects_name") + "_count",
                value=len(objects),
                force_add=True,
            )
            self.demo_image = self.print_segmentation_labels(
                water_img,
                labels,
                dbg_suffix="watershed_skimage",
                min_size=min_area,
            )
            self.result = self.demo_image

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

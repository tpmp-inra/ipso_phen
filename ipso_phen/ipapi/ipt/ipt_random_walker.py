import cv2
import numpy as np
from scipy import ndimage
from skimage.feature import peak_local_max
from skimage.segmentation import random_walker

import logging
import os

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))

from ipso_phen.ipapi.base.ip_common import DEFAULT_COLOR_MAP, ToolFamily
from ipso_phen.ipapi.base.ipt_abstract_merger import IptBaseMerger


class IptRandomWalker(IptBaseMerger):
    def build_params(self):
        self.add_slider(
            name="min_area",
            desc="Min zone area ",
            default_value=1200,
            minimum=-1,
            maximum=50000,
        )
        self.add_slider(
            name="min_distance",
            desc="Min distance",
            default_value=20,
            minimum=-1,
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
        From scikit-image: Random walker algorithm for segmentation from markers.
        Random walker algorithm is implemented for gray-level or multichannel images.

        Real time : No

        Keyword Arguments (in parentheses, argument name):
            * Min zone area  (min_area): Accepted contour minimal size
            * Min distance (min_distance): Minimum number of pixels separating peaks in a region of `2 * min_distance + 1` (i.e. peaks are separated by at least `min_distance`). To find the maximum number of peaks, use `min_distance=1`.
            * Post process (post_process): Merge labels if selected
            * Label merger threshold {hierarchy_threshold}: Regions connected by an edge with weight smaller than thresh are merged
        """
        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return False

        min_area = self.get_value_of("min_area")
        min_distance = self.get_value_of("min_distance")
        post_process = self.get_value_of("post_process")

        res = False
        try:
            mask = self.get_mask()
            if mask is None:
                logger.error(f"Random walker needs a calculated mask to start")
                res = False

            dist_transform = ndimage.distance_transform_edt(mask)
            wrapper.store_image(
                np.uint8(dist_transform),
                f"dist_transform_{self.input_params_as_str()}",
                text_overlay=True,
            )
            local_max = peak_local_max(
                dist_transform, indices=False, min_distance=min_distance, labels=mask
            )

            markers = ndimage.label(local_max, structure=np.ones((3, 3)))[0]
            labels = random_walker(-dist_transform, markers).astype(np.uint8)
            self.result = labels.copy()
            if post_process != "none":
                post_labels = labels.copy()
            else:
                post_labels = None

            walker_img = cv2.applyColorMap(255 - labels, DEFAULT_COLOR_MAP)
            wrapper.store_image(
                walker_img,
                f"walker_img_vis_{self.input_params_as_str()}",
                text_overlay=True,
            )
            self.print_segmentation_labels(
                walker_img, labels, dbg_suffix="random_walker", min_size=min_area
            )

            if post_process == "merge_labels":
                res = self._merge_labels(
                    wrapper.current_image, labels=post_labels, **kwargs
                )
            else:
                res = True

        except Exception as e:
            res = False
            wrapper.error_holder.add_error(
                new_error_text=f'Failed to process {self. name}: "{repr(e)}"',
                new_error_level=35,
                target_logger=logger,
            )
        else:
            res = True
        finally:
            return res

    @property
    def name(self):
        return "Random Walker"

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
        return [ToolFamily.CLUSTERING]

    @property
    def description(self):
        return "From scikit-image: Random walker algorithm for segmentation from markers.\nRandom walker algorithm is implemented for gray-level or multichannel images."

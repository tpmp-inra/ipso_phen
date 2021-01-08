import cv2
import numpy as np
from skimage.segmentation import felzenszwalb
from skimage.util import img_as_float

import logging
import os

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))

from ipso_phen.ipapi.base.ip_common import DEFAULT_COLOR_MAP, ToolFamily
from ipso_phen.ipapi.base.ipt_abstract_merger import IptBaseMerger


class IptFelzenswalb(IptBaseMerger):
    def build_params(self):
        self.add_source_selector(default_value="source")
        self.add_slider(
            name="scale", desc="Scale", default_value=100, minimum=1, maximum=500
        )
        self.add_slider(
            name="sigma", desc="Sigma", default_value=50, minimum=0, maximum=100
        )
        self.add_slider(
            name="min_size", desc="Min size", default_value=50, minimum=0, maximum=250
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
        From scikit-image: Computes Felsenszwalb’s efficient graph based image segmentation.

        Real time : Absolutely Not

        Keyword Arguments (in parentheses, argument name):
            * Select source file type (source_file): Select starting image from various choices
            * Scale (scale): Free parameter. Higher means larger clusters.
            * Sigma (sigma): Width (standard deviation) of Gaussian kernel used in preprocessing.
            * Min size (min_size): Minimum component size. Enforced using postprocessing.
            * Post process (post_process): Action to be taken afterwards
            * Label merger threshold {hierarchy_threshold}: Regions connected by an edge with weight smaller than thresh are merged
        """
        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return False

        scale = self.get_value_of("scale")
        sigma = self.get_value_of("sigma") / 100
        min_size = self.get_value_of("min_size")
        post_process = self.get_value_of("post_process")

        res = False
        try:
            img = self.wrapper.current_image

            img = img_as_float(img)
            labels = felzenszwalb(img, scale=scale, sigma=sigma, min_size=min_size)
            if post_process != "none":
                post_labels = labels.copy()
            else:
                post_labels = None

            labels[labels == -1] = 0
            labels = (
                (labels - labels.min()) / (labels.max() - labels.min()) * 255
            ).astype(np.uint8)
            self.result = cv2.applyColorMap(255 - labels, DEFAULT_COLOR_MAP)
            wrapper.store_image(self.result, "felsenszwalb", text_overlay=True)

            self.print_segmentation_labels(
                self.result,
                labels,
                dbg_suffix="felsenszwalb",
            )

            if post_process == "merge_labels":
                self.result = self._merge_labels(
                    img.copy(),
                    labels=post_labels,
                    **kwargs,
                )

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
        return "Felsenszwalb"

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
        return "From scikit-image: Computes Felsenszwalb’s efficient graph based image segmentation."

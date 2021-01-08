import cv2
import numpy as np
from skimage.segmentation import slic

import logging
import os

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))

from ipso_phen.ipapi.base.ip_common import DEFAULT_COLOR_MAP, ToolFamily
from ipso_phen.ipapi.base.ipt_abstract_merger import IptBaseMerger


class IptSlic(IptBaseMerger):
    def build_params(self):
        self.add_source_selector(default_value="source")
        self.add_slider(
            name="n_segments",
            desc="Segment count",
            default_value=3,
            minimum=1,
            maximum=250,
        )
        self.add_slider(
            name="compactness",
            desc="Compactness",
            default_value=10,
            minimum=0,
            maximum=100,
        )
        self.add_slider(
            name="sigma", desc="Sigma", default_value=100, minimum=0, maximum=100
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
        From scikit-image: Segments image using k-means clustering in Color-(x,y,z) space.

        Real time : No

        Keyword Arguments (in parentheses, argument name):
            * Select source file type (source_file): Selected source
            * Segment count (n_segments): The (approximate) number of labels in the segmented output image.
            * Compactness (compactness): Balances color proximity and space proximity. Higher values give more weight to space proximity, making superpixel shapes more square/cubic.
            * Sigma (sigma): Width of Gaussian smoothing kernel for pre-processing for each dimension of the image.
            * Post process (post_process): Merge labels or not
            * Label merger threshold {hierarchy_threshold}: Regions connected by an edge with weight smaller than thresh are merged
        """
        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return False

        n_segments = self.get_value_of("n_segments")
        compactness = self.get_value_of("compactness")
        sigma = self.get_value_of("sigma") / 100
        post_process = self.get_value_of("post_process")

        res = False
        try:
            img = self.wrapper.current_image
            labels = slic(
                img, n_segments=n_segments, compactness=compactness, sigma=sigma
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
            slick_img = cv2.applyColorMap(255 - labels, DEFAULT_COLOR_MAP)
            wrapper.store_image(
                slick_img,
                f"slic_vis_{self.input_params_as_str(exclude_defaults=True)}",
                text_overlay=True,
            )

            self.print_segmentation_labels(
                slick_img, labels, dbg_suffix="slic", source_image=img.copy()
            )

            if post_process == "merge_labels":
                res = self._merge_labels(img.copy(), labels=post_labels, **kwargs)
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
        return "Slic"

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
        return "From scikit-image: Segments image using k-means clustering in Color-(x,y,z) space."

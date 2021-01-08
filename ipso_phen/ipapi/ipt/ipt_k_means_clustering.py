import cv2
import numpy as np

import logging
import os

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))

from ipso_phen.ipapi.base.ipt_abstract import IptBase
from ipso_phen.ipapi.base.ip_common import ToolFamily


class IptKMeansClustering(IptBase):
    def build_params(self):
        self.add_color_space(default_value="HSV")
        self.add_spin_box(
            name="cluster_count",
            desc="Cluster count",
            default_value=3,
            minimum=2,
            maximum=100,
            hint="Number of clusters to split the set by.",
        )
        self.add_spin_box(
            name="max_iter_count",
            desc="Max iterations allowed",
            default_value=10,
            minimum=1,
            maximum=1000,
            hint="An integer specifying maximum number of iterations.",
        )
        self.add_spin_box(
            name="precision",
            desc="Minium precision (Epsilon)",
            default_value=1,
            minimum=1,
            maximum=100,
            hint="Required accuracy",
        )
        self.add_combobox(
            name="stop_crit",
            desc="Termination criteria - Stop when:",
            default_value="eps_max_iter",
            values=dict(
                precision="Precision reached",
                max_iter="Iteration count reached",
                eps_max_iter="Precision or iteration reached",
            ),
        )
        self.add_combobox(
            name="flags",
            desc="Centers initialization method",
            default_value="rnd",
            values=dict(rnd="Random centers", pp="Guess centers"),
        )
        self.add_spin_box(
            name="attempts",
            desc="Attempts",
            default_value=10,
            minimum=1,
            maximum=100,
            hint="""Flag to specify the number of times the algorithm is executed using different initial labellings.
            The algorithm returns the labels that yield the best compactness.
            This compactness is returned as output.""",
        )
        self.add_roi_selector()
        self.add_checkbox(name="normalize", desc="Normalize histograms", default_value=0)

    def process_wrapper(self, **kwargs):
        """
        K-means clustering:
        Performs k-means clustering, grouping object with a distance formula
        Real time: False

        Keyword Arguments (in parentheses, argument name):
            * Color space (color_space): no clue
            * Cluster count (cluster_count): Number of clusters to split the set by.
            * Max iterations allowed (max_iter_count): An integer specifying maximum number of iterations.
            * Minium precision (Epsilon) (precision): Required accuracy
            * Termination criteria - Stop when: (stop_crit):
            * Centers initialization method (flags):
            * Attempts (attempts): Flag to specify the number of times the algorithm is executed using different initial labellings.
                    The algorithm returns the labels that yield the best compactness.
                    This compactness is returned as output.
            * Name of ROI to be used (roi_names): Operation will only be applied inside of ROI
            * ROI selection mode (roi_selection_mode):
            * Normalize histograms (normalize):
        """

        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return False

        cluster_count = self.get_value_of("cluster_count")
        color_space = self.get_value_of("color_space")

        res = False
        try:
            img = wrapper.current_image

            # Apply ROIs
            rois = self.get_ipt_roi(
                wrapper=wrapper,
                roi_names=self.get_value_of("roi_names").replace(" ", "").split(","),
                selection_mode=self.get_value_of("roi_selection_mode"),
            )
            if rois:
                bck = wrapper.delete_rois(src_mask=img, tags=rois)
                img = wrapper.keep_rois(src_mask=img, tags=rois)
            else:
                bck = None

            # Normalize
            if self.get_value_of("normalize") == 1:
                img[:, :, 0] = cv2.equalizeHist(img[:, :, 0])
                img[:, :, 1] = cv2.equalizeHist(img[:, :, 1])
                img[:, :, 2] = cv2.equalizeHist(img[:, :, 2])

            if color_space == "HSV":
                img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            elif color_space == "LAB":
                img = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)

            flt_img = img.reshape((-1, 3))

            # convert to np.float32
            flt_img = np.float32(flt_img)

            # define criteria, number of clusters(K) and apply kmeans()
            stop_criteria = self.get_value_of("stop_crit")
            if stop_criteria == "precision":
                criteria = (
                    cv2.TERM_CRITERIA_EPS,
                    self.get_value_of("max_iter_count"),
                    self.get_value_of("precision"),
                )
            elif stop_criteria == "max_iter":
                criteria = (
                    cv2.TERM_CRITERIA_MAX_ITER,
                    self.get_value_of("max_iter_count"),
                    self.get_value_of("precision"),
                )
            elif stop_criteria == "eps_max_iter":
                criteria = (
                    cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER,
                    self.get_value_of("max_iter_count"),
                    self.get_value_of("precision"),
                )
            else:
                logger.error(
                    f"K-means clustering FAILED, unknown criteria '{stop_criteria}''"
                )
                return

            # Define centers initialization
            center_init = (
                cv2.KMEANS_RANDOM_CENTERS
                if self.get_value_of("flags") == "rnd"
                else cv2.KMEANS_PP_CENTERS
            )

            ret, label, center = cv2.kmeans(
                data=flt_img,
                K=cluster_count,
                bestLabels=None,
                criteria=criteria,
                attempts=self.get_value_of("attempts"),
                flags=center_init,
            )

            # Now convert back into uint8, and make original image
            center = np.uint8(center)
            res = center[label.flatten()]

            self.result = (
                cv2.bitwise_or(bck, res.reshape((img.shape)))
                if bck is not None
                else res.reshape((img.shape))
            )

            wrapper.store_image(self.result, "k_means_cluster")
        except Exception as e:
            logger.error(f'Failed to process {self. name}: "{repr(e)}"')
        else:
            res = True
        finally:
            return res

    @property
    def name(self):
        return "K-means clustering"

    @property
    def real_time(self):
        return False

    @property
    def result_name(self):
        return "ret, label, center"

    @property
    def output_kind(self):
        return "image"

    @property
    def use_case(self):
        return [ToolFamily.PRE_PROCESSING]

    @property
    def description(self):
        return "Performs k-means clustering, grouping object with a distance formula"

import os
import numpy as np
import cv2
from abc import ABC, abstractproperty
import logging

from skimage.future import graph

from ipso_phen.ipapi.base.ipt_abstract import IptBase
from ipso_phen.ipapi.base.ip_common import DEFAULT_COLOR_MAP

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))


class IptBaseMerger(IptBase, ABC):
    def _merge_labels(self, source_image, labels, **kwargs):
        def weight_boundary(graph, src, dst, n):
            """
            Handle merging of nodes of a region boundary region adjacency graph.

            This function computes the `"weight"` and the count `"count"`
            attributes of the edge between `n` and the node formed after
            merging `src` and `dst`.


            Parameters
            ----------
            graph : RAG
                The graph under consideration.
            src, dst : int
                The vertices in `graph` to be merged.
            n : int
                A neighbor of `src` or `dst` or both.

            Returns
            -------
            data : dict
                A dictionary with the "weight" and "count" attributes to be
                assigned for the merged node.

            """
            default = {"weight": 0.0, "count": 0}

            count_src = graph[src].get(n, default).get("count", 0)
            count_dst = graph[dst].get(n, default).get("count", 0)

            weight_src = graph[src].get(n, default).get("weight", 0)
            weight_dst = graph[dst].get(n, default).get("weight", 0)

            count = count_src + count_dst
            return {
                "count": count,
                "weight": (count_src * weight_src + count_dst * weight_dst) / count,
            }

        def merge_boundary(graph, src, dst):
            """Call back called before merging 2 nodes.

            In this case we don't need to do any computation here.
            """
            pass

        threshold = self.get_value_of("hierarchy_threshold", 35)
        res = None
        try:
            g = graph.rag_mean_color(source_image, labels)
            merged_labels = graph.merge_hierarchical(
                labels,
                g,
                thresh=threshold,
                rag_copy=False,
                in_place_merge=True,
                merge_func=merge_boundary,
                weight_func=weight_boundary,
            )

            merged_labels[merged_labels == -1] = 0
            labels2 = (
                (merged_labels - merged_labels.min())
                / (merged_labels.max() - merged_labels.min())
                * 255
            ).astype(np.uint8)
            res = cv2.applyColorMap(255 - labels2, DEFAULT_COLOR_MAP)
            self._wrapper.store_image(res, f"rag_vis", text_overlay=True)
            self.print_segmentation_labels(
                res, labels2, dbg_suffix="rag", source_image=source_image
            )

        except Exception as e:
            logger.exception(f'FAIL label merging, exception: "{repr(e)}"')
        finally:
            return res

    @abstractproperty
    def name(self):
        return "Abstract image label merger processing tool"

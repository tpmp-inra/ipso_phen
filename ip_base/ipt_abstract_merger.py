import numpy as np
import cv2
from abc import ABC, abstractproperty

from skimage.future import graph

from ip_base.ipt_abstract import IptBase
from ip_base.ip_common import DEFAULT_COLOR_MAP


class IptBaseMerger(IptBase, ABC):

    def _merge_labels(self, source_image, labels, **kwargs):

        def _weight_mean_color(graph_, src, dst, n):
            """Callback to handle merging nodes by recomputing mean color.

            The method expects that the mean color of `dst` is already computed.

            Parameters
            ----------
            graph_ : RAG
                The graph_ under consideration.
            src, dst : int
                The vertices in `graph_` to be merged.
            n : int
                A neighbor of `src` or `dst` or both.

            Returns
            -------
            data : dict
                A dictionary with the `"weight"` attribute set as the absolute
                difference of the mean color between node `dst` and `n`.
            """

            diff = graph_.node[dst]['mean color'] - graph_.node[n]['mean color']
            diff = np.linalg.norm(diff)
            return {'weight': diff}

        def merge_mean_color(graph_, src, dst):
            """Callback called before merging two nodes of a mean color distance graph_.

            This method computes the mean color of `dst`.

            Parameters
            ----------
            graph_ : RAG
                The graph_ under consideration.
            src, dst : int
                The vertices in `graph_` to be merged.
            """
            graph_.node[dst]['total color'] += graph_.node[src]['total color']
            graph_.node[dst]['pixel count'] += graph_.node[src]['pixel count']
            graph_.node[dst]['mean color'] = (graph_.node[dst]['total color'] / graph_.node[dst]['pixel count'])

        threshold = self.get_value_of('hierarchy_threshold', 35)
        res = False
        try:
            g = graph.rag_mean_color(source_image, labels)
            merged_labels = graph.merge_hierarchical(labels, g, thresh=threshold, rag_copy=False,
                                                     in_place_merge=True,
                                                     merge_func=merge_mean_color,
                                                     weight_func=_weight_mean_color)

            merged_labels[merged_labels == -1] = 0
            labels2 = ((merged_labels - merged_labels.min()) / (
                    merged_labels.max() - merged_labels.min()) * 255).astype(np.uint8)
            rag_img = cv2.applyColorMap(255 - labels2, DEFAULT_COLOR_MAP)
            self._wrapper.store_image(rag_img, f'rag_vis_{self.input_params_as_str()}', text_overlay=True)
            self.print_segmentation_labels(rag_img, labels2, dbg_suffix='rag', source_image=source_image)

        except Exception as e:
            res = False
            print(f'{repr(e)}')
        else:
            res = True
        finally:
            return res

    @abstractproperty
    def name(self):
        return 'Abstract image label merger processing tool'

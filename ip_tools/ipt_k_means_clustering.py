import cv2
import numpy as np

from ip_base.ipt_abstract import IptBase
from ip_base.ip_common import TOOL_GROUP_PRE_PROCESSING_STR


class IptKMeansClustering(IptBase):

    def build_params(self):
        self.add_color_space(default_value='HSV')
        self.add_slider(name='cluster_count', desc='Cluster count', default_value=3, minimum=2, maximum=100)

    def process_wrapper(self, **kwargs):
        """
        Performs k-means clustering, grouping object with a distance formula

        Real time : No

        Keyword Arguments (in parentheses, argument name):
            * Color space (color_space): Color space to which the image will be converted before starting
            * Cluster count (cluster_count): -
        """
        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return False

        cluster_count = self.get_value_of('cluster_count')
        color_space = self.get_value_of('color_space')

        res = False
        try:
            img = wrapper.current_image

            if color_space == 'HSV':
                img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            elif color_space == 'LAB':
                img = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)

            flt_img = img.reshape((-1, 3))

            # convert to np.float32
            flt_img = np.float32(flt_img)

            # define criteria, number of clusters(K) and apply kmeans()
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
            ret, label, center = cv2.kmeans(
                flt_img, cluster_count, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS
            )

            # Now convert back into uint8, and make original image
            center = np.uint8(center)
            res = center[label.flatten()]
            self.result = res.reshape((img.shape))

            wrapper.store_image(
                self.result, f'k_means_cluster_{self.input_params_as_str()}', text_overlay=True
            )
        except Exception as e:
            print(f'{repr(e)}')
        else:
            res = True
        finally:
            return res

    @property
    def name(self):
        return 'K-means clustering'

    @property
    def real_time(self):
        return False

    @property
    def result_name(self):
        return 'ret, label, center'

    @property
    def output_kind(self):
        return 'image'

    @property
    def use_case(self):
        return [TOOL_GROUP_PRE_PROCESSING_STR]

    @property
    def description(self):
        return "Performs k-means clustering, grouping object with a distance formula"

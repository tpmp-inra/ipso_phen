import numpy as np
from skimage.segmentation import chan_vese

import logging
import os

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))

from ipso_phen.ipapi.base.ipt_abstract import IptBase
from ipso_phen.ipapi.base.ip_common import ToolFamily


class IptChanVese(IptBase):
    def build_params(self):
        self.add_channel_selector(default_value="h")
        self.add_slider(
            name="max_iter",
            desc="Max iterations",
            default_value=100,
            minimum=0,
            maximum=500,
        )
        self.add_slider(name="mu", desc="mu", default_value=25, minimum=0, maximum=100)
        self.add_slider(
            name="lambda1", desc="Lambda1", default_value=1, minimum=0, maximum=10
        )
        self.add_slider(
            name="lambda2", desc="Lambda2", default_value=1, minimum=0, maximum=10
        )
        self.add_slider(name="dt", desc="dt", default_value=25, minimum=0, maximum=200)

    def process_wrapper(self, **kwargs):
        """
        From scikit-image: Chan-Vese segmentation algorithm.\n
        Active contour model by evolving a level set.\n
        Can be used to segment objects without clearly defined boundaries.\n

        Real time : Absolutely Not

        Keyword Arguments (in parentheses, argument name):
            * Channel (channel): Channel to be used, in parameter must be grayscale
            * Max iterations (max_iter): Maximum number of iterations allowed before the algorithm interrupts itself.
            * mu (mu): ‘edge length’ weight parameter. Higher mu values will produce a ‘round’ edge, while values closer to zero will detect smaller objects.
            * Lambda1 (lambda1): ‘difference from average’ weight parameter for the output region with value ‘True’. If it is lower than lambda2, this region will have a larger range of values than the other.
            * Lambda2 (lambda2): ‘difference from average’ weight parameter for the output region with value ‘False’. If it is lower than lambda1, this region will have a larger range of values than the other.
            * dt (dt): A multiplication factor applied at calculations for each step, serves to accelerate the algorithm. While higher values may speed up the algorithm, they may also lead to convergence problems.
        """
        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return False

        max_iter = self.get_value_of("max_iter")
        mu = self.get_value_of("mu") / 100
        dt = self.get_value_of("dt") / 100
        lambda1 = self.get_value_of("lambda1")
        lambda2 = self.get_value_of("lambda2")
        channel = self.get_value_of("channel")

        res = False
        try:
            image = wrapper.get_channel(
                wrapper.current_image, channel, median_filter_size=3
            )
            cv = chan_vese(
                image,
                mu=mu,
                lambda1=lambda1,
                lambda2=lambda2,
                tol=1e-3,
                max_iter=max_iter,
                dt=dt,
                init_level_set="checkerboard",
                extended_output=True,
            )
            cv_0 = cv[0] + 1
            cv_0 = ((cv_0 - cv_0.min()) / (cv_0.max() - cv_0.min()) * 255).astype(
                np.uint8
            )
            cv_1 = ((cv[1] - cv[1].min()) / (cv[1].max() - cv[1].min()) * 255).astype(
                np.uint8
            )

            wrapper.store_image(cv_1, f"Chan_Vese_final_level_set", text_overlay=False)
            wrapper.store_image(cv_0, f"Chan-Vese_segmentation", text_overlay=True)
            self.result = cv_0

        except Exception as e:
            res = False
            logger.error(f'Failed to process {self. name}: "{repr(e)}"')
        else:
            res = True
        finally:
            return res

    @property
    def name(self):
        return "Chan Vese"

    @property
    def real_time(self):
        return False

    @property
    def result_name(self):
        return "channel"

    @property
    def output_kind(self):
        return "channel"

    @property
    def use_case(self):
        return [ToolFamily.THRESHOLD]

    @property
    def description(self):
        return "From scikit-image: Chan-Vese segmentation algorithm.\nActive contour model by evolving a level set.\nCan be used to segment objects without clearly defined boundaries.\n"

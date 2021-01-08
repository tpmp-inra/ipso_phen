import numpy as np
import cv2

from ipso_phen.ipapi.base.ipt_abstract import IptBase
from ipso_phen.ipapi.tools import regions
from ipso_phen.ipapi.base import ip_common as ipc

import logging
import os

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))


class IptMorphology(IptBase):
    def build_params(self):
        self.add_morphology_operator(default_operator="none")
        self.add_roi_selector()

    def process_wrapper(self, **kwargs):
        """
        Morphology:
        Morphology: Applies the selected morphology operator.
        Needs to be part of a pipeline where a mask has already been generated
        Real time : False

        Keyword Arguments (in parentheses, argument name):
            * Morphology operator (morph_op):
            * Kernel size (kernel_size):
            * Kernel shape (kernel_shape):
            * Iterations (proc_times):
        """

        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return False

        res = False
        try:
            mask = self.get_mask()
            if mask is None:
                logger.error(f"FAIL {self.name}: mask must be initialized")
                return
            self.result = self.apply_morphology_from_params(mask.copy())
            rois = self.get_ipt_roi(
                wrapper=wrapper,
                roi_names=self.get_value_of("roi_names").replace(" ", "").split(","),
                selection_mode=self.get_value_of("roi_selection_mode"),
            )
            if rois:
                self.result = cv2.bitwise_or(
                    regions.delete_rois(rois=rois, image=mask),
                    regions.keep_rois(rois=rois, image=self.result),
                )

                self.demo_image = cv2.bitwise_or(
                    np.dstack((self.result, self.result, self.result)),
                    regions.draw_rois(
                        rois=rois,
                        image=np.dstack(
                            (
                                np.zeros_like(self.result),
                                np.zeros_like(self.result),
                                np.zeros_like(self.result),
                            )
                        ),
                        line_width=wrapper.width // 200,
                        color=ipc.C_BLUE,
                    ),
                )
            else:
                self.demo_image = self.result
            wrapper.store_image(
                self.demo_image,
                f'morphology_{self.get_value_of("morph_op")}',
                text_overlay=True,
            )

        except Exception as e:
            res = False
            logger.error(f'Failed to process {self. name}: "{repr(e)}"')
        else:
            res = True
        finally:
            return res

    @property
    def name(self):
        return "Morphology"

    @property
    def real_time(self):
        return (self.wrapper is not None) and (self.wrapper.mask is not None)

    @property
    def result_name(self):
        return "mask"

    @property
    def output_kind(self):
        return "mask"

    @property
    def use_case(self):
        return [ipc.ToolFamily.MASK_CLEANUP]

    @property
    def description(self):
        return "Morphology: Applies the selected morphology operator.\nNeeds to be part of a pipeline where a mask has already been generated"

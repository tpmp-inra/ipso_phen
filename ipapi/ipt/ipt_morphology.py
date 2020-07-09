from base.ipt_abstract import IptBase
from base.ip_common import TOOL_GROUP_MASK_CLEANUP_STR

import logging

logger = logging.getLogger(__name__)


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
            mask = wrapper.current_image
            if not (len(mask.shape) == 2 or (len(mask.shape) == 3 and mask.shape[2] == 1)):
                mask = self.get_mask()
                if mask is None:
                    wrapper.error_holder.add_error(
                        f"FAIL {self.name}: mask must be initialized", target_logger=logger
                    )
                    return
            self.result = self.apply_morphology_from_params(mask.copy())
            rois = self.get_ipt_roi(
                wrapper=wrapper,
                roi_names=self.get_value_of("roi_names").replace(" ", "").split(","),
                selection_mode=self.get_value_of("roi_selection_mode"),
            )
            if rois:
                self.result = wrapper.multi_or(
                    (wrapper.keep_rois(self.result, rois), wrapper.delete_rois(mask, rois))
                )
            wrapper.store_image(
                self.result, f'morphology_{self.get_value_of("morph_op")}', text_overlay=True
            )

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
        return [TOOL_GROUP_MASK_CLEANUP_STR]

    @property
    def description(self):
        return "Morphology: Applies the selected morphology operator.\nNeeds to be part of a pipeline where a mask has already been generated"

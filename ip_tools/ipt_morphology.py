from ip_base.ipt_abstract import IptBase
from ip_base.ip_common import TOOL_GROUP_MASK_CLEANUP_STR


class IptMorphology(IptBase):

    def build_params(self):
        self.add_morphology_operator(default_operator='none')

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
                mask = wrapper.mask
                if mask is None:
                    wrapper.process_image(threshold_only=True)
                    mask = wrapper.mask
                    if mask is None:
                        wrapper.error_holder.add_error(f'Watershed needs a calculated mask to start')
                        return False
            self.result = self.apply_morphology_from_params(mask)
            wrapper.store_image(self.result, f'Morphology_{self.input_params_as_str()}', text_overlay=True)

        except Exception as e:
            res = False
            wrapper.error_holder.add_error(f'Morphology FAILED, exception: "{repr(e)}"')
        else:
            res = True
        finally:
            return res

    @property
    def name(self):
        return 'Morphology'

    @property
    def real_time(self):
        return (self.wrapper is not None) and (self.wrapper.mask is not None)

    @property
    def result_name(self):
        return 'mask'

    @property
    def output_kind(self):
        return 'mask'

    @property
    def use_case(self):
        return [TOOL_GROUP_MASK_CLEANUP_STR]

    @property
    def description(self):
        return 'Morphology: Applies the selected morphology operator.\nNeeds to be part of a pipeline where a mask has already been generated'

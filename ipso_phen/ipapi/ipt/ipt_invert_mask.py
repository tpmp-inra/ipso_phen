from ipso_phen.ipapi.base.ipt_abstract import IptBase


import os
import logging

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))


class IptInvertMask(IptBase):
    def build_params(self):
        self.add_enabled_checkbox()

    def process_wrapper(self, **kwargs):
        """
        Invert mask:
        'Invert mask
        Real time: True

        Keyword Arguments (in parentheses, argument name):
            * Activate tool (enabled): Toggle whether or not tool is active
        """
        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return False

        res = False
        try:
            if self.get_value_of("enabled") == 1:
                mask = self.get_mask()
                if mask is None:
                    logger.error("Failure Invert mask: mask must be initialized")
                    return
                self.result = 255 - mask

                # Write your code here
                wrapper.store_image(self.result, "inverted_mask")
                res = True
            else:
                wrapper.store_image(wrapper.current_image, "current_image")
                res = True
        except Exception as e:
            res = False
            logger.error(f"Invert mask FAILED, exception: {repr(e)}")
        else:
            pass
        finally:
            return res

    @property
    def name(self):
        return "Invert mask"

    @property
    def package(self):
        return "TPMP"

    @property
    def is_wip(self):
        return False

    @property
    def real_time(self):
        return True

    @property
    def result_name(self):
        return "mask"

    @property
    def output_kind(self):
        return "mask"

    @property
    def use_case(self):
        return ["Mask cleanup"]

    @property
    def description(self):
        return """'Invert mask"""

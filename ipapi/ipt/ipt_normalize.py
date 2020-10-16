import cv2

from ipapi.base.ipt_abstract import IptBase


import logging

logger = logging.getLogger(__name__)


class IptNormalize(IptBase):
    def build_params(self):
        self.add_enabled_checkbox()

    def process_wrapper(self, **kwargs):
        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return False

        res = False
        try:
            if self.get_value_of("enabled") == 1:
                self.result = cv2.equalizeHist(wrapper.current_image)
                wrapper.store_image(self.result, "current_image")
                res = True
            else:
                wrapper.store_image(wrapper.current_image, "current_image")
                res = True
        except Exception as e:
            res = False
            logger.error(f"Normalize FAILED, exception: {repr(e)}")
        else:
            pass
        finally:
            return res

    @property
    def name(self):
        return "Normalize Image"

    @property
    def package(self):
        return "TPMP"

    @property
    def real_time(self):
        return True

    @property
    def result_name(self):
        return "image"

    @property
    def output_kind(self):
        return "image"

    @property
    def use_case(self):
        return ["Exposure fixing", "Pre processing"]

    @property
    def description(self):
        return """'Normalize image"""

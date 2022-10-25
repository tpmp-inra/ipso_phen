import logging
import os

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))

from ipso_phen.ipapi.base.ipt_abstract import IptBase
import ipso_phen.ipapi.base.ip_common as ipc


class IptCheckSource(IptBase):
    def build_params(self):
        self.add_checkbox(name="show_images", desc="Show images", default_value=0)
        self.add_checkbox(name="thorough_test", desc="Thorough test", default_value=0)
        self.add_checkbox(name="print_rois", desc="Print ROIs", default_value=0)

    def process_wrapper(self, **kwargs):
        """
        Checks source file.
        Detects physically corrupted files or files tagged as bad.

        Real time : Yes

        Keyword Arguments (in parentheses, argument name):
            * Show images (show_images): Show images once checked if not damaged
            * Thorough test (thorough_test): If true will try to load image, if not only tags will be parsed
            * Print ROIs (print_rois): If True ROIs will be drawn on top of displayed image
        """
        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return False

        show_images = bool(self.get_value_of("show_images"))
        thorough_test = bool(self.get_value_of("thorough_test"))
        print_rois = bool(self.get_value_of("print_rois"))

        res = False
        try:
            res = wrapper.check_source()
            if res and thorough_test:
                _ = wrapper.current_image
                res = wrapper.good_image
            if show_images or print_rois:
                if print_rois:
                    wrapper.init_rois()
                wrapper.store_image(wrapper.current_image, "source", print_rois)
        except Exception as e:
            logger.error(f'Failed to process {self. name}: "{repr(e)}"')
            res = False
        else:
            pass
        finally:
            self.result = res
            return res

    @property
    def name(self):
        return "Check source image"

    @property
    def real_time(self):
        return True

    @property
    def result_name(self):
        return "image_check"

    @property
    def output_kind(self):
        return "boolean"

    @property
    def use_case(self):
        return [ipc.ToolFamily.ASSERT]

    @property
    def description(self):
        return "Checks image and returns error if something is wrong."

    @property
    def input_type(self):
        return ipc.IO_IMAGE

    @property
    def output_type(self):
        return ipc.IO_NONE

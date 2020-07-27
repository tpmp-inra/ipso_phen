import logging

logger = logging.getLogger(__name__)
from ipapi.base.ipt_abstract import IptBase
from ipapi.base.ip_common import ToolFamily, ensure_odd


class IptPrintChannels(IptBase):
    def build_params(self):
        self.add_channel_selector(default_value="h")
        self.add_checkbox(name="normalize", desc="Normalize channel", default_value=0)
        self.add_slider(
            name="median_filter_size",
            desc="Median filter size (odd values only)",
            default_value=0,
            minimum=1,
            maximum=51,
        )
        self.add_text_overlay()

    def process_wrapper(self, **kwargs):
        """
        Print channels:


        Real time : True

        Keyword Arguments (in parentheses, argument name):
            * Channel (channel):
            * Normalize channel (normalize):
            * Median filter size (odd values only) (median_filter_size):
            * Overlay text on top of images (text_overlay): Draw description text on top of images
        """

        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return False

        res = False
        try:
            median_filter_size = self.get_value_of("median_filter_size")
            channel = self.get_value_of("channel")
            text_overlay = self.get_value_of("text_overlay") == 1
            normalize = self.get_value_of("normalize") == 1

            median_filter_size = (
                0 if median_filter_size == 1 else ensure_odd(median_filter_size)
            )

            c = wrapper.get_channel(
                channel=channel, median_filter_size=median_filter_size, normalize=normalize
            )

            wrapper.store_image(
                c, f"channel_{self.input_params_as_str()}", text_overlay=text_overlay
            )

            self.result = c
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
        return "Print channels"

    @property
    def real_time(self):
        return True

    @property
    def result_name(self):
        return "none"

    @property
    def output_kind(self):
        return "none"

    @property
    def use_case(self):
        return [ToolFamily.VISUALIZATION, ToolFamily.PRE_PROCESSING]

    @property
    def description(self):
        return "Print channels"

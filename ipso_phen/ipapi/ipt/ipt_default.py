import logging
import os

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))

from ipso_phen.ipapi.base.ipt_abstract_analyzer import IptBaseAnalyzer
from ipso_phen.ipapi.base.ip_common import ToolFamily


class IptDefault(IptBaseAnalyzer):
    def build_params(self):
        self.add_checkbox(
            name="threshold_only",
            desc="Threshold only",
            default_value=0,
            hint="Do not extract data, just build the mask",
        )
        self.add_slider(
            name="boundary_position",
            desc="Horizontal boundary position",
            default_value=-1,
            minimum=-1,
            maximum=4000,
            hint="Bondary position, used to calculate above and underground data",
        )
        self.add_combobox(
            name="build_mosaic",
            desc="Build mosaic",
            default_value="none",
            values=dict(none="none", debug="debug", result="result"),
            hint="Build mosaic showing the process steps",
        )
        self.add_channel_selector(
            default_value="h", hint="Select channel for pseudo color image"
        )

    def process_wrapper(self, **kwargs):
        """
        Default process:
        Performs the default process associated with the experiment.
        If no default process is available, all channels will be printed.

        Real time : False

        Keyword Arguments (in parentheses, argument name):
            * Threshold only (threshold_only): Do not extract data, just build the mask
            * Horizontal boundary position (boundary_position): Bondary position, used to calculate above and underground data
            * Build mosaic (build_mosaic): Build mosaic showing the process steps
            * Channel (channel): Select channel for pseudo color image
        """
        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return False
        res = False
        try:
            self.data_dict = {}
            threshold_only = self.get_value_of("threshold_only")
            build_mosaic = self.get_value_of("build_mosaic")
            boundary_position = self.get_value_of("boundary_position")

            wrapper.store_mosaic = build_mosaic
            res = wrapper.process_image(
                threshold_only=threshold_only,
                pseudo_color_channel=self.get_value_of("channel"),
                boundary_position=boundary_position,
                horizontal_cleaning_method=self.get_value_of(
                    "horizontal_cleaning_method", "mask_data"
                ),
            )

            self.data_dict = dict(wrapper.csv_data_holder.data_list)
            self.result = wrapper.mask
            res = True
        except Exception as e:
            logger.error(f'Failed to process {self. name}: "{repr(e)}"')
            res = False
        else:
            pass
        finally:
            return res

    @property
    def name(self):
        return "Default process"

    @property
    def description(self):
        return (
            "Performs the default process associated with the experiment.\n"
            "If no default process is available, all channels will be printed."
        )

    @property
    def real_time(self):
        return False

    @property
    def order(self):
        return 2

    @property
    def result_name(self):
        return "mask"

    @property
    def output_kind(self):
        return "data"

    @property
    def use_case(self):
        return [ToolFamily.DEFAULT_PROCESS]

    @property
    def short_test_script(self):
        return True

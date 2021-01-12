import logging
import os

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))

from ipso_phen.ipapi.base.ipt_abstract_analyzer import IptBaseAnalyzer
from ipso_phen.ipapi.base.ip_common import ToolFamily


class IptAnalyseObservation(IptBaseAnalyzer):
    def build_params(self):
        self.add_checkbox(name="experiment", desc="Experiment", default_value=1)
        self.add_checkbox(name="plant", desc="Plant", default_value=1)
        self.add_checkbox(name="date_time", desc="Date and time", default_value=1)
        self.add_checkbox(name="camera", desc="Camera", default_value=1)
        self.add_checkbox(name="view_option", desc="View Option", default_value=1)
        self.add_checkbox(
            name="luid", desc="Add Local Unique IDentifier (LUID)", default_value=0
        )
        self.add_checkbox(
            name="source_path", desc="Add path to source file", default_value=0
        )
        self.add_separator(name="sep_1")
        self.add_checkbox(
            name="split_plant_name",
            desc="Split plant name into multiple variables",
            default_value=0,
        )
        self.add_text_input(
            name="separator", desc="Character to use as separator", default_value="_"
        )
        self.add_text_input(
            name="new_column_names",
            desc="Names of new variables",
            default_value="",
            hint='names separate by "," with no spaces',
        )
        self.add_text_input(
            name="add_columns",
            desc="Add as empty columns",
            default_value="",
        )

    def process_wrapper(self, **kwargs):
        """
        Observation data:
        Returns observation data retrieved from the image file
        Real time: False

        Keyword Arguments (in parentheses, argument name):
            * Experiment (experiment):
            * Plant (plant):
            * Date and time (date_time):
            * Camera (camera):
            * View Option (view_option):
            * Add Local Unique IDentifier (LUID) (luid):
            * Add path to source file (source_path):
            * Split plant name into multiple variables (split_plant_name):
            * Character to use as separator (separator):
            * Names of new variables (new_column_names): names separate by "," with no spaces
        """
        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return False

        res = False
        try:
            self.data_dict = {}

            self.add_value("experiment", wrapper.experiment)
            self.add_value("plant", wrapper.plant)
            self.add_value("date_time", wrapper.date_time)
            self.add_value("camera", wrapper.camera)
            self.add_value("view_option", wrapper.view_option)
            self.add_value("luid", wrapper.luid)
            self.add_value("source_path", wrapper.file_path)

            if self.get_value_of("split_plant_name") == 1:
                sep = self.get_value_of("separator")
                if sep:
                    name_splits = wrapper.plant.split(sep)
                    vars = (
                        self.get_value_of("new_column_names").replace(" ", "").split(",")
                    )
                    for i, value in enumerate(name_splits):
                        if len(vars) > i:
                            key = vars[i]
                        else:
                            key = f"key_{i}"
                        self.add_value(key=key, value=value, force_add=True)

            new_columns = [
                col
                for col in self.get_value_of("add_columns").replace(" ", "").split(",")
                if col
            ]
            if new_columns:
                for new_column in new_columns:
                    self.add_value(new_column, None, force_add=True)

            wrapper.store_image(
                image=wrapper.current_image, text="observation_data", force_store=True
            )

            res = True
        except Exception as e:
            logger.error(f'Failed to process {self. name}: "{repr(e)}"')
            res = False
        else:
            pass
        finally:
            self.result = len(self.data_dict) > 0
            return res

    @property
    def name(self):
        return "Observation data"

    @property
    def real_time(self):
        return False

    @property
    def result_name(self):
        return "dictionary"

    @property
    def output_kind(self):
        return "dictionnary"

    @property
    def use_case(self):
        return [ToolFamily.FEATURE_EXTRACTION]

    @property
    def description(self):
        return "Returns observation data retrieved from the image file"

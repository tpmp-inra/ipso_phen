from ip_base.ipt_abstract_analyzer import IptBaseAnalyzer
from ip_base.ip_common import TOOL_GROUP_FEATURE_EXTRACTION_STR


class IptAnalyseObservation(IptBaseAnalyzer):

    def build_params(self):
        self.add_checkbox(name='experiment', desc='experiment', default_value=1)
        self.add_checkbox(name='plant', desc='plant', default_value=1)
        self.add_checkbox(name='date_time', desc='date_time', default_value=1)
        self.add_checkbox(name='camera', desc='camera', default_value=1)
        self.add_checkbox(name='view_option', desc='view_option', default_value=1)
        self.add_separator(name='sep_1')
        self.add_checkbox(name='split_plant_name', desc='Split plant name into multiple variables', default_value=0)
        self.add_text_input(name='separator', desc='Character to use as separator', default_value='_')
        self.add_text_input(
            name='new_column_names',
            desc='Names of new variables',
            default_value='',
            hint='names separate by "," with no spaces'
        )

    def process_wrapper(self, **kwargs):
        """
        Observation data:
        Returns observation data retrieved from the image file
        Real time : False

        Keyword Arguments (in parentheses, argument name):
            * experiment (experiment): 
            * plant (plant): 
            * date_time (date_time): 
            * camera (camera): 
            * view_option (view_option): 
            * Split plant name into multiple variables (split_plant_name): 
            * Character to use as separator (separator): 
            * Names of new variables (new_column_names): names separate by "," with no spaces
        --------------
        """

        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return False

        res = False
        try:
            self.add_value('experiment', wrapper.experiment)
            self.add_value('plant', wrapper.plant)
            self.add_value('date_time', wrapper.date_time)
            self.add_value('camera', wrapper.camera)
            self.add_value('view_option', wrapper.view_option)

            if self.get_value_of('split_plant_name') == 1:
                sep = self.get_value_of('separator')
                if sep:
                    name_splits = wrapper.plant.split(sep)
                    vars = self.get_value_of('new_column_names').replace(' ', '').split(',')
                    for i, value in enumerate(name_splits):
                        if len(vars) > i:
                            key = vars[i]
                        else:
                            key = f'key_{i}'
                        self.add_value(key=key, value=value, force_add=True)

            res = True
        except Exception as e:
            wrapper.error_holder.add_error(f'Failed : "{repr(e)}"')
            res = False
        else:
            pass
        finally:
            self.result = len(self.data_dict) > 0
            return res

    @property
    def name(self):
        return 'Observation data'

    @property
    def real_time(self):
        return False

    @property
    def result_name(self):
        return 'dictionary'

    @property
    def output_kind(self):
        return 'dictionnary'

    @property
    def use_case(self):
        return [TOOL_GROUP_FEATURE_EXTRACTION_STR]

    @property
    def description(self):
        return 'Returns observation data retrieved from the image file'

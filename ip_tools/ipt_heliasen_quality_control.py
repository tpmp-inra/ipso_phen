from ip_base.ip_common import C_LIME, C_RED, C_ORANGE
from ip_base.ipt_abstract import IptBase
from ip_tools.ipt_default import IptDefault
from ip_base.ipt_abstract_analyzer import IptBaseAnalyzer
from tools import shapes
from ip_base.ip_common import TOOL_GROUP_FEATURE_EXTRACTION_STR


class IptHeliasenQualityControl(IptBaseAnalyzer):

    def build_params(self):
        self.add_checkbox(name='threshold_only', desc='Threshold only', default_value=1)
        self.add_combobox(
            name='build_mosaic',
            desc='Build mosaic',
            default_value='debug',
            values=dict(none='none', debug='debug', result='result')
        )
        self.add_channel_selector(default_value='l')
        self.add_combobox(
            name='horizontal_cleaning_method',
            desc='Horizontal noise handling method',
            default_value='mask_data',
            values=dict(mask_data='Mask data analysis', hough='Hough transformation'),
            hint='Selects how horizontal noisy lines will be removed'
        )

        self.add_separator('sep_1')
        self.add_text_output(is_single_line=True, name='error_level', desc='Error level:')
        self.add_text_output(is_single_line=False, name='report', desc='Quality control:')
        self.add_table_output(name='csv_output', desc=('variable', 'value'))

    def process_wrapper(self, **kwargs):
        """
        Heliasen Quality Control:
        Checks light barrier image quality
        Outputs main error and partial errors

        Real time : False

        Keyword Arguments (in parentheses, argument name):
            * Threshold only (threshold_only): 
            * Build mosaic (build_mosaic): 
            * Channel (channel): 
            * Horizontal noise handling method (horizontal_cleaning_method): Selects how horizontal noisy lines will be removed
        --------------
            * output  (error_level): Error level:
            * output  (report): Quality control:
            * output  (csv_output): ('variable', 'value')
        """
        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return False

        res = False
        try:
            # Build the plant mask
            with IptDefault(wrapper=wrapper, **self.params_to_dict()) as (res, ed):
                if not res:
                    return
                output_data = ed.wrapper.data_output

            for k, v in output_data.items():
                self.add_value(k, v, True)

            # Display the result
            p = self.find_by_name('csv_output')
            p.update_output(output_value=output_data, ignore_list=('error_level', 'report'), invert=True)

            self.update_output_from_dict(output_data)
            mosaic = wrapper.build_mosaic()

            err_lvl = output_data.get('error_level', 0)
            if err_lvl >= 3:
                colour = C_RED
            elif err_lvl >= 2:
                colour = C_ORANGE
            elif err_lvl >= 1:
                colour = C_LIME
            else:
                colour = None
            if colour is not None:
                r = shapes.RectangleOfInterest.from_lwth(
                    0, wrapper.width, 0, wrapper.height, 'warning', 'none', colour
                )
                r.draw_to(mosaic, 4)
            text_overlay = [f'{k}: {v}' for k, v in output_data.items()]
            wrapper.store_image(mosaic, 'mosaic_out', text_overlay='\n'.join(text_overlay))

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
        return 'Heliasen Quality Control'

    @property
    def real_time(self):
        return False

    @property
    def result_name(self):
        return 'dic'

    @property
    def description(self):
        return 'Checks light barrier image quality\n' \
               'Outputs main error and partial errors\n'

    @property
    def output_kind(self):
        return 'data'

    @property
    def use_case(self):
        return [TOOL_GROUP_FEATURE_EXTRACTION_STR]

    @property
    def description(self):
        return 'Heliasen Quality Control.\nChecks light barrier image quality.\nOutputs main error and partial errors.'

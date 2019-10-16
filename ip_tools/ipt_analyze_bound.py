import cv2
import numpy as np

from ip_base.ip_common import MaskData, C_RED
from ip_base.ipt_abstract_analyzer import IptBaseAnalyzer
from tools import shapes
from ip_base.ip_common import TOOL_GROUP_FEATURE_EXTRACTION_STR


class IptAnalyzeBound(IptBaseAnalyzer):

    def build_params(self):
        self.add_checkbox(name='above_bound_height', desc='Height above bound level', default_value=1)
        self.add_checkbox(name='above_bound_area', desc='Area above bound level', default_value=1)
        self.add_checkbox(
            name='above_bound_percent_area', desc='Percentage area above bound level', default_value=1
        )
        self.add_checkbox(name='below_bound_height', desc='Height below bound level', default_value=1)
        self.add_checkbox(name='below_bound_area', desc='Area below bound level', default_value=1)
        self.add_checkbox(
            name='below_bound_percent_area', desc='Percentage area below bound level', default_value=1
        )
        self.add_checkbox(
            name='override_shape_height',
            desc='Override shape height',
            default_value=1,
            hint='If true "shape_height" from "Analyse object" will be overridden.'
        )

        self.add_spin_box(
            name='line_position',
            desc='Horizontal bound position',
            default_value=-1,
            minimum=-1,
            maximum=4000,
            hint='Horizontal bound normally used to separate above from below ground'
        )
        self.add_separator(name='sep_1')
        self.add_channel_selector(default_value='l')

    def process_wrapper(self, **kwargs):
        """
        Analyze bound:
        Analyses object bound
        Real time : False

        Keyword Arguments (in parentheses, argument name):
            * Height above bound level (above_bound_height): 
            * Area above bound level (above_bound_area): 
            * Percentage area above bound level (above_bound_percent_area): 
            * Height below bound level (below_bound_height): 
            * Area below bound level (below_bound_area): 
            * Percentage area below bound level (below_bound_percent_area): 
            * Horizontal bound position (line_position): Horizontal bound normally used to separate above from below ground
            * Channel (channel): 
        --------------
        """
        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return False

        res = False
        try:
            img = self.extract_source_from_args()
            mask = wrapper.mask
            if mask is None:
                return

            res = True
            line_position = self.get_value_of('line_position')
            if line_position < 0:
                return

            roi_top = shapes.RectangleOfInterest.from_lwth(
                left=0, width=wrapper.width, top=0, height=line_position, name='roi_top'
            )
            roi_bottom = shapes.RectangleOfInterest.from_lwth(
                left=0,
                width=wrapper.width,
                top=line_position,
                height=wrapper.height - line_position,
                name='roi_bottom'
            )

            mask_top = wrapper.crop_to_roi(img=mask, roi=roi_top)
            mask_bottom = wrapper.crop_to_roi(img=mask, roi=roi_bottom)

            mask_data_top = MaskData(mask_top)
            mask_data_bottom = MaskData(mask_bottom)

            area_ = np.count_nonzero(mask)
            if area_:
                t_height = mask_data_top.mask.shape[0] - mask_data_top.top_index
                b_height = mask_data_bottom.height

                self.add_value('above_bound_height', t_height)
                self.add_value('above_bound_area', mask_data_top.area)
                self.add_value('above_bound_percent_area', mask_data_top.area / area_ * 100)

                self.add_value('below_bound_height', b_height)
                self.add_value('below_bound_area', mask_data_bottom.area)
                self.add_value('below_bound_percent_area', mask_data_bottom.area / area_ * 100)

                self.add_value(
                    'shape_height', t_height + b_height, force_add=self.get_value_of('override_shape_height')
                )

                if wrapper.store_images:
                    pseudo_color_channel = self.get_value_of('channel')
                    c = wrapper.get_channel(src_img=img, channel=pseudo_color_channel)
                    background_img = np.dstack((c, c, c))
                    p_img = wrapper.draw_image(
                        src_image=background_img,
                        channel=pseudo_color_channel,
                        src_mask=mask,
                        foreground='false_colour',
                        background='source',
                        normalize_before=True,
                        color_map=cv2.COLORMAP_SUMMER,
                        roi=roi_top,
                        centroid_width=10,
                        height_thickness=4,
                        width_thickness=4
                    )
                    p_img = wrapper.draw_image(
                        src_image=p_img,
                        channel=pseudo_color_channel,
                        src_mask=mask,
                        foreground='false_colour',
                        background='source',
                        normalize_before=False,
                        color_map=cv2.COLORMAP_HOT,
                        roi=roi_bottom,
                        centroid_width=10,
                        height_thickness=4,
                        width_thickness=4
                    )
                    cv2.line(p_img, (0, line_position), (wrapper.width, line_position), C_RED, 3)
                    wrapper.store_image(p_img, 'bounds')
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
        return 'Analyze bound'

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
        return 'Analyses object bound.\nNeeds a mask as an input.\nNormally used in a pipeline after a clean mask is created.'

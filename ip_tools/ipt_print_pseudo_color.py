from ip_base.ipt_abstract import IptBase
from tools import shapes
from ip_base.ip_common import TOOL_GROUP_VISUALIZATION_STR


class IptPseudoColorOnImage(IptBase):

    def build_params(self):
        self.add_source_selector(default_value='source')
        self.add_channel_selector('l')
        self.add_color_map_selector(name='color_map', default_value='c_2')
        self.add_checkbox(name='normalize', desc='Normalize channel', default_value=0)
        self.add_text_overlay(1)

    def process_wrapper(self, **kwargs):
        """
        Draw plant mask region with selected pseudo color.
        Requires class pipeline to work.

        Real time : Only if mask has already been calculated

        Keyword Arguments (in parentheses, argument name):
            * Select source file type (source_file): Select starting image from various choices
            * Channel (channel): Pseudo color image channel
            * Select pseudo color map (color_map): Color map to be used for pseudo color
            * Normalize channel (normalize): -
        """
        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return False

        source_type = self.get_value_of('source_file')
        channel = self.get_value_of('channel')
        normalize = self.get_value_of('normalize')
        color_map = self.get_value_of('color_map')
        text_overlay = self.get_value_of('text_overlay') == 1
        _, color_map = color_map.split('_')
        color_map = int(color_map)
        res = True
        try:
            src_img = self.extract_source_from_args()
            if src_img is None:
                wrapper.error_holder.add_error('Unable to fetch source target image')
                res = False

            mask = wrapper.mask
            if mask is None:
                wrapper.process_image(threshold_only=True)
                mask = wrapper.mask
                if mask is None:
                    wrapper.error_holder.add_error('Watershed needs a calculated mask to start')
                    res = False

            if source_type == 'cropped_source':
                keep_roi = None
                for roi in wrapper.rois_list:
                    if roi.tag == 'keep':
                        keep_roi = roi
                        break
                if keep_roi is not None:
                    if isinstance(keep_roi, shapes.CircleOfInterest):
                        keep_roi = keep_roi.as_rect()
                    mask = mask[keep_roi.top:keep_roi.bottom, keep_roi.left:keep_roi.right]

            res_img = wrapper.draw_image(
                channel=channel, background='source', normalize_before=normalize, color_map=color_map
            )
            wrapper.store_image(
                res_img, f'PCI_{channel}_{self.input_params_as_str()}', text_overlay=text_overlay
            )
            self.result = res_img.copy()

            res = wrapper.ensure_mask_zone()
            if not res:
                wrapper.error_holder.add_error('HANDLED FAILURE Mask not where expected to be')

        except Exception as e:
            res = False
            wrapper.error_holder.add_error(f'Failed to print pseudo color image, exception: "{repr(e)}"')
        else:
            res = True
        finally:
            return res

    @property
    def name(self):
        return 'Draw mask region with pseudo color'

    @property
    def real_time(self):
        return (self._wrapper is not None) and (self._wrapper.mask is not None)

    @property
    def result_name(self):
        return 'image'

    @property
    def output_kind(self):
        return 'image'

    @property
    def use_case(self):
        return [TOOL_GROUP_VISUALIZATION_STR]

    @property
    def description(self):
        return "Draw plant mask region with selected pseudo color.\nRequires class pipeline to work."

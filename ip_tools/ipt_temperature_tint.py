import numpy as np
import cv2

from ip_base.ipt_abstract import IptBase
from ip_base.ip_common import TOOL_GROUP_EXPOSURE_FIXING_STR, TOOL_GROUP_PRE_PROCESSING_STR


class IptStub(IptBase):

    def build_params(self):
        self.add_checkbox(
            name='enabled',
            desc='Activate tool',
            default_value=1,
            hint='Toggle whether or not tool is active'
        )
        self.add_combobox(
            name='clip_method',
            desc='Clip method',
            default_value='clip',
            values=dict(
                clip='Set to 0 if lower 255 if upper',
                rescale='Allow overflow and the rescale',
                percentage_clip='Use adjustment values as percentage and then clip',
                percentage_rescale='Use adjustment values as percentage and then rescale'
            )
        )
        self.add_slider(
            name='temperature_adjustment',
            desc='Temperature adjustment',
            default_value=0,
            minimum=-100,
            maximum=100,
            hint='Adjust image temperature'
        )
        self.add_slider(
            name='tint_adjustment',
            desc='Tint adjustment',
            default_value=0,
            minimum=-100,
            maximum=100,
            hint='Adjust image tint'
        )
        self.add_checkbox(name='build_mosaic', desc='Build mosaic', default_value=0)

    def process_wrapper(self, **kwargs):
        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return False

        res = False
        try:
            img = wrapper.current_image
            if self.get_value_of('enabled') == 1:
                b, g, r = cv2.split(img)

                temperature_adjustment = self.get_value_of('temperature_adjustment')
                tint_adjustment = self.get_value_of('tint_adjustment')
                build_mosaic = self.get_value_of('build_mosaic') == 1

                b = (b - temperature_adjustment).astype(np.float)
                g = (g + tint_adjustment).astype(np.float)
                r = (r + temperature_adjustment).astype(np.float)
                if build_mosaic:
                    wrapper.store_image(b, 'b')
                    wrapper.store_image(g, 'g')
                    wrapper.store_image(r, 'g')

                clip_method = self.get_value_of('clip_method')

                if clip_method == 'clip':
                    b[b < 0] = 0
                    g[g < 0] = 0
                    r[r < 0] = 0
                    b[b > 255] = 255
                    g[g > 255] = 255
                    r[r > 255] = 255
                    self.result = cv2.merge([b.astype(np.uint8), g.astype(np.uint8), r.astype(np.uint8)])
                elif clip_method == 'rescale':
                    self.result = self.to_uint8(cv2.merge([b, g, r]))
                elif clip_method == 'percentage_clip':
                    pass
                elif clip_method == 'percentage_rescale':
                    pass
                else:
                    wrapper.error_holder.add_error(f'Failed : unknown clip_method "{clip_method}"')
                    return

                wrapper.store_image(self.result, 'temp_tint')

                if build_mosaic:
                    canvas = wrapper.build_mosaic(image_names=np.array([['b', 'g'], ['r', '', 'temp_tint']]))
                    wrapper.store_image(canvas, 'mosaic')

                res = True
            else:
                self.result = img
                wrapper.store_image(self.result, 'source')
            res = True

        except Exception as e:
            wrapper.error_holder.add_error(f'Failed : "{repr(e)}"')
            res = False
        else:
            pass
        finally:
            return res

    @property
    def name(self):
        return 'Temperature and tint'

    @property
    def real_time(self):
        return True

    @property
    def result_name(self):
        return 'image'

    @property
    def output_kind(self):
        return 'image'

    @property
    def use_case(self):
        return [TOOL_GROUP_EXPOSURE_FIXING_STR, TOOL_GROUP_PRE_PROCESSING_STR]

    @property
    def description(self):
        return "Simple method to alter an image temperature and tint\nhttp://www.tannerhelland.com/5675/simple-algorithms-adjusting-image-temperature-tint/"

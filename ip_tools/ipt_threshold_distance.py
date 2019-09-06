import numpy as np
import cv2
from scipy.special import expit, logit
from scipy import stats

from ip_base.ipt_abstract import IptBase
from ip_base.ip_common import TOOL_GROUP_PRE_PROCESSING_STR
from ip_base.ip_common import TOOL_GROUP_THRESHOLD_STR

CHANNEL_COUNT = 3


class IptThresholdDistance(IptBase):

    def build_params(self):
        self.add_enabled_checkbox()
        for i, dc in zip(range(1, CHANNEL_COUNT + 1), ('h', 'none', 'none', 'none')):
            self.add_channel_selector(name=f'channel_{i}', default_value=dc, enable_none=i != 1)
            self.add_combobox(
                name=f'transformation_{i}',
                desc=f'Transformation applied to channel {i}',
                default_value='none',
                values=dict(
                    none='None',
                    sigmoid='Sigmoid',
                    logit='Inverse sigmoid',
                    arcsin='Arc sinus',
                    sqrt='Square root',
                    normalize='Normalize'
                )
            )
        self.add_combobox(
            name='origin',
            desc='Distance origin',
            default_value='zero',
            values=dict(zero='Space origin', mean='Components means', median='Components medians')
        )
        self.add_combobox(
            name='distance',
            desc='Distance',
            default_value='l1',
            values=dict(
                l1='L1 - Manhattan',
                l2='L2 - Euclidean',
                chebyshev='Chebyshev',
                inv_chebyshev='Inverse Chebyshev',
                canberra='Canberra',
                delta_plus='\u03A3 \u0394, keep positive values',
                delta_minus='\u03A3 \u0394, keep negative values'
            )
        )
        self.add_tool_target()
        self.add_separator('s2')
        self.add_combobox(
            name='post_processing',
            desc='Postprocessing option',
            default_value='none',
            values=dict(none='None', threshold='Threshold', false_color='Use false color')
        )
        self.add_color_map_selector()
        self.add_binary_threshold()
        self.add_separator('s5')
        self.add_text_overlay(0)
        self.add_combobox(
            name='build_mosaic',
            desc='Displayed output',
            default_value='no',
            values=dict(
                no='Default',
                steps='Process steps',
                transformed_channels='Transformed channels',
                sbs='Source and result side by side',
                source_and_masked='Kept in color over B&W background'
            ),
            hint='Choose mosaic type to display'
        )

    def process_wrapper(self, **kwargs):
        """
        Distance threshold:
        Build a mask from distance calculation
        Real time : True

        Keyword Arguments (in parentheses, argument name):
            * Activate tool (enabled): Toggle whether or not tool is active
            * Channel (channel_1): 
            * Transformation applied to channel 1 (transformation_1): 
            * Channel (channel_2): 
            * Transformation applied to channel 2 (transformation_2): 
            * Channel (channel_3): 
            * Transformation applied to channel 3 (transformation_3): 
            * Distance origin (origin): 
            * Distance (distance): 
            * Target IPT (tool_target): no clue
            * Postprocessing option (post_processing): 
            * Select pseudo color map (color_map): 
            * Threshold min value (min_t): 
            * Threshold max value (max_t): 
            * Median filter size (odd values only) (median_filter_size): 
            * Morphology operator (morph_op): 
            * Kernel size (kernel_size): 
            * Kernel shape (kernel_shape): 
            * Iterations (proc_times): 
            * Overlay text on top of images (text_overlay): Draw description text on top of images
            * Displayed output (build_mosaic): Choose mosaic type to display
        --------------
        """
        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return False

        res = False
        np.seterr(divide='ignore')
        try:
            img = self.extract_source_from_args()
            rois = self.get_ipt_roi(wrapper=wrapper)
            if len(rois) > 0:
                roi = rois[0]
            else:
                roi = None
            if roi is not None:
                bck = np.zeros_like(img[:, :, 0])
            else:
                bck = None
            channels = []
            channels_ids = []
            for i in range(1, CHANNEL_COUNT + 1):
                channel_id = self.get_value_of(f'channel_{i}')
                c = wrapper.get_channel(src_img=img, channel=channel_id)
                if c is None:
                    continue
                if roi is not None:
                    c = wrapper.crop_to_roi(c, roi=roi, erase_outside_if_circle=True)
                wrapper.store_image(c, f'source_{channel_id}')
                ct = self.get_value_of(f'transformation_{i}')
                if ct == 'sigmoid':
                    c = np.interp(c, (c.min(), c.max()), (0, 5))
                    c = expit(c)
                    c = np.interp(c, (c.min(), c.max()), (0, 255)).astype(np.uint8)
                elif ct == 'normalize':
                    c = cv2.equalizeHist(c)
                elif ct == 'logit':
                    c = np.interp(c, (c.min(), c.max()), (0.5, 0.99))
                    c = logit(c)
                    c = np.interp(c, (c.min(), c.max()), (0, 255)).astype(np.uint8)
                elif ct == 'arcsin':
                    c = np.interp(c, (c.min(), c.max()), (0, 1))
                    c = np.arcsin(c)
                    c = np.interp(c, (c.min(), c.max()), (0, 255)).astype(np.uint8)
                elif ct == 'sqrt':
                    c = np.interp(c, (c.min(), c.max()), (0, 1))
                    c = np.sqrt(c)
                    c = np.interp(c, (c.min(), c.max()), (0, 255)).astype(np.uint8)
                wrapper.store_image(c, f'transformed_{channel_id}')
                channels.append(c)
                channels_ids.append(f'transformed_{channel_id}')

            origin = self.get_value_of('origin')
            if origin == 'zero':
                p0 = [0.0 for _ in channels]
            elif origin == 'mean':
                p0 = [np.median(c, axis=None) for c in channels]
            elif origin == 'median':
                p0 = [np.median(c, axis=None) for c in channels]
            else:
                wrapper.error_holder.add_error('Unknown origin')
                res = False
                return

            distance_method = self.get_value_of('distance')
            if distance_method == 'l2' and len(channels) <= 1:
                distance_method = 'l1'

            if distance_method == 'l1':
                dist_map = np.zeros_like(channels[0])
                for c, p in zip(channels, p0):
                    dist_map = np.add(dist_map, np.abs(np.subtract(c.astype(np.float), p)))
            elif distance_method == 'l2':
                dist_map = np.zeros_like(channels[0])
                for c, p in zip(channels, p0):
                    dist_map = np.add(dist_map, np.power(np.subtract(c.astype(np.float), p), 2))
                dist_map = np.sqrt(dist_map)
            elif distance_method == 'chebyshev':
                dist_map = np.abs(np.subtract(channels[0].astype(np.float), p0[0]))
                if len(channels) > 1:
                    for c, p in zip(channels[1:], p0[1:]):
                        dist_map = np.maximum(dist_map, np.abs(np.subtract(c.astype(np.float), p)))
            elif distance_method == 'inv_chebyshev':
                dist_map = np.abs(np.subtract(channels[0].astype(np.float), p0[0]))
                if len(channels) > 1:
                    for c, p in zip(channels[1:], p0[1:]):
                        dist_map = np.minimum(dist_map, np.abs(np.subtract(c.astype(np.float), p)))
            elif distance_method == 'canberra':
                dist_map = np.zeros_like(channels[0])
                for c, p in zip(channels, p0):
                    dist_map = np.add(
                        dist_map, np.divide(np.abs(np.subtract(c.astype(np.float), p)), np.add(c.astype(np.float), p))
                    )
            elif distance_method == 'delta_plus':
                dist_map = np.zeros_like(channels[0])
                for c, p in zip(channels, p0):
                    dist_map = np.add(dist_map, np.subtract(c.astype(np.float), p))
                dist_map[dist_map < 0] = 0
            elif distance_method == 'delta_minus':
                dist_map = np.zeros_like(channels[0])
                for c, p in zip(channels, p0):
                    dist_map = np.add(dist_map, np.subtract(c.astype(np.float), p))
                dist_map[dist_map > 0] = 0
            else:
                wrapper.error_holder.add_error('Unknown distance calculation method')
                res = False
                return
            dist_map = self.to_uint8(dist_map)

            if roi is not None and bck is not None:
                r = roi.as_rect()
                bck[r.top:r.bottom, r.left:r.right] = dist_map
                dist_map = bck

            wrapper.store_image(dist_map, 'raw_distance_map')

            pp = self.get_value_of('post_processing')
            if pp == 'threshold':
                self.result = self.apply_binary_threshold(wrapper=wrapper, img=dist_map, channel=None)
            elif pp == 'false_color':
                color_map = self.get_value_of('color_map')
                _, color_map = color_map.split('_')
                self.result = cv2.applyColorMap(dist_map, int(color_map))
            else:
                self.result = dist_map

            res = True

            if self.get_value_of('text_overlay') == 1:
                text_overlay = self.input_params_as_str(exclude_defaults=True,
                                                        excluded_params=('progress_callback',)).replace(', ', '\n')
            else:
                text_overlay = False

            build_mosaic = self.get_value_of('build_mosaic')
            if build_mosaic == 'steps':
                wrapper.store_image(image=self.result, text='threshold_distance', text_overlay=False)
                line_1 = channels_ids
                line_2 = ['raw_distance_map', 'threshold_distance']
                if len(line_1) > len(line_2):
                    line_2 = line_2 + ['nope' for _ in range(len(line_2), len(line_1))]
                elif len(line_2) > len(line_1):
                    line_1 = line_1 + ['nope' for _ in range(len(line_1), len(line_2))]
                canvas = wrapper.build_mosaic(
                    shape=(img.shape[0], img.shape[1], 3), image_names=np.array([line_1, line_2])
                )
                wrapper.store_image(canvas, 'mosaic', text_overlay=text_overlay)
            elif build_mosaic == 'sbs':
                wrapper.store_image(image=self.result, text='threshold_distance', text_overlay=False)
                canvas = wrapper.build_mosaic(image_names=np.array(['current_image', 'threshold_distance']))
                wrapper.store_image(canvas, 'mosaic', text_overlay=text_overlay)
            elif (build_mosaic == 'source_and_masked') and (pp == 'threshold'):
                masked_image = self.apply_mask(img, mask=self.result)
                wrapper.store_image(masked_image, 'masked_image')
                canvas = wrapper.build_mosaic(image_names=np.array(['current_image', 'masked_image']))
                wrapper.store_image(
                    self.wrapper.draw_image(src_image=img, src_mask=self.result, background='bw', foreground='source'),
                    'selection_on_bw',
                    text_overlay=text_overlay
                )
            elif build_mosaic == 'transformed_channels':
                canvas = wrapper.build_mosaic(image_names=np.array(channels_ids))
                wrapper.store_image(canvas, 'mosaic', text_overlay=text_overlay)
            else:
                wrapper.store_image(image=self.result, text='threshold_distance', text_overlay=text_overlay)
        except Exception as e:
            wrapper.error_holder.add_error(f'Failed : "{repr(e)}"')
            res = False
        else:
            pass
        finally:
            np.seterr(divide='warn')
            return res

    @property
    def name(self):
        return 'Distance threshold'

    @property
    def real_time(self):
        return True

    @property
    def result_name(self):
        return 'mask'

    @property
    def output_kind(self):
        return 'mask'

    @property
    def use_case(self):
        return [TOOL_GROUP_THRESHOLD_STR, TOOL_GROUP_PRE_PROCESSING_STR]

    @property
    def description(self):
        return 'Build a mask from distance calculation'

import inspect
import json
import os
import pickle
import sys
from copy import copy
from uuid import uuid4

import cv2
import numpy as np

from ip_base.ip_abstract import AbstractImageProcessor
from ip_base.ip_common import (
    AVAILABLE_FEATURES, C_RED, TOOL_GROUP_MASK_CLEANUP_STR, TOOL_GROUP_EXPOSURE_FIXING_STR,
    TOOL_GROUP_UNKNOWN_STR, TOOL_GROUP_PRE_PROCESSING_STR, TOOL_GROUP_THRESHOLD_STR,
    TOOL_GROUP_ROI_DYNAMIC_STR, TOOL_GROUP_ROI_STATIC_STR, TOOL_GROUP_FEATURE_EXTRACTION_STR
)
from ip_base.ipt_abstract import IptParam, IptBase, IptParamHolder
from ip_base.ipt_functional import call_ipt_code, call_ipt_func_code
from tools.csv_writer import AbstractCsvWriter

ALLOW_RESULT_CACHE = True


def encode_ipt(o):
    if isinstance(o, IptScriptGenerator):
        return {**dict(__class_name__=type(o).__name__), **dict(o.__dict__)}
    elif isinstance(o, IptParam):
        return {**dict(__class_name__=type(o).__name__), **dict(o.__dict__), **dict(_wrapper=None)}
    elif isinstance(o, IptParamHolder):
        return {**dict(__class_name__=type(o).__name__), **dict(o.__dict__), **dict(_wrapper=None)}
    elif issubclass(type(o), AbstractImageProcessor):
        return None
    else:
        print(f"Object of type '{o.__class__.__name__}' is not JSON serializable, bummer")
        return None


def decode_ipt(dct):
    if '__class_name__' in dct:
        tmp = dict(dct)
        class_name = tmp.pop('__class_name__')
        for _, obj in inspect.getmembers(sys.modules['ip_tools']):
            if inspect.isclass(obj) and (obj.__name__ == class_name):
                try:
                    ret = obj(**tmp)
                except:
                    ret = None
                finally:
                    return ret

        ret = globals()[class_name](**tmp)
        return ret
    else:
        return dct


last_script_version = '0.3.0.0'


class SettingsHolder(IptParamHolder):

    def __init__(self, **kwargs):
        self.update_feedback_items = []
        super(SettingsHolder, self).__init__(**kwargs)

    def build_params(self):
        self.add_checkbox(name='threshold_only', desc='Find mask only', default_value=0)
        self.add_combobox(
            name='merge_method',
            desc='Select merge method',
            values=dict(multi_and='Logical AND', multi_or='Logical OR'),
            default_value='multi_and'
        )
        self.add_checkbox(name='display_images', desc='Display step by step images', default_value=1)
        self.add_checkbox(name='build_mosaic', desc='Display mosaic', default_value=0)
        self.add_spin_box(
            name='bound_level',
            desc='Horizontal bound position',
            default_value=-1,
            minimum=-1,
            maximum=4000,
            hint='Horizontal bound normally used to separate above from below ground'
        )
        self.add_channel_selector(
            name='pseudo_channel',
            desc='Channel used for pseudo color images',
            default_value='l',
            hint='Select channel for pseudo color image'
        )
        self.add_color_map_selector(name='color_map', default_value='c_2')
        self.add_combobox(
            name='pseudo_background_type',
            desc='Background type for pseudo color images',
            default_value='bw',
            values=dict(
                bw='Black & white source',
                source='Source image',
                black='Black backround',
                white='White background',
                silver='Silver background'
            )
        )
        self.add_checkbox(name='use_default_script', desc='Use default script if present', default_value=0)

        self.update_feedback_items = ['bound_level', 'pseudo_channel', 'color_map', 'pseudo_background_type']

    def reset(self, is_update_widgets: bool = True):
        for p in self._param_list:
            p.value = p.default_value
            p.clear_widgets()


class IptScriptGenerator(object):

    def __init__(self, **kwargs):
        self._ip_operators = []
        self._feature_list = self._init_features()
        self._target_data_base = None
        self._settings = SettingsHolder()
        self._last_wrapper_luid = ''

    @staticmethod
    def _init_features():
        return sorted([dict(feature=f, enabled=True) for f in AVAILABLE_FEATURES], key=lambda x: x['feature'])

    @classmethod
    def load(cls, path: str) -> [object, Exception]:
        res = None
        try:
            _, ext = os.path.splitext(os.path.basename(path))
            if ext == '.tipp':
                with open(path, 'rb') as f:
                    res = pickle.load(f)
            elif ext.lower() == '.json':
                with open(path, 'r') as f:
                    res = json.load(f, object_hook=decode_ipt)
            else:
                raise ValueError(f'Unknown file extension: "{ext}"')

            # Check that we have all settings
            if not hasattr(res, '_settings'):
                res._settings = SettingsHolder()

            settings_checker = SettingsHolder()
            override_updates = False
            for setting_ in settings_checker.gizmos:
                s = res._settings.find_by_name(name=setting_.name)
                if s is None:
                    res._settings.add(copy(setting_))
                    override_updates = True
            if override_updates:
                res._settings.update_feedback_items = settings_checker.update_feedback_items

            # Check attributes
            if not hasattr(res, '_last_wrapper_luid'):
                res._last_wrapper_luid = ''

            # Fix ROI tagging
            for tool_dict in res.get_operators(constraints=dict(kind='roi_post_merge')):
                tool_dict['kind'
                         ] = 'roi_dynamic' if 'roi_dynamic' in tool_dict['tool'].use_case else 'roi_static'

            # Fix all taggins
            for tool_dict in res.get_operators():
                current_kind = tool_dict['kind']
                if current_kind == 'exp_fixer':
                    tool_dict['kind'] = TOOL_GROUP_EXPOSURE_FIXING_STR
                elif current_kind == 'pre_processor':
                    tool_dict['kind'] = TOOL_GROUP_PRE_PROCESSING_STR
                elif current_kind == 'mask_generator':
                    tool_dict['kind'] = TOOL_GROUP_THRESHOLD_STR
                elif current_kind == 'mask_cleaner':
                    tool_dict['kind'] = TOOL_GROUP_MASK_CLEANUP_STR
                elif current_kind == 'roi_dynamic':
                    tool_dict['kind'] = TOOL_GROUP_PRE_PROCESSING_STR
                elif current_kind == 'roi_static':
                    tool_dict['kind'] = TOOL_GROUP_ROI_STATIC_STR
                elif current_kind == 'feature_extractor':
                    tool_dict['kind'] = TOOL_GROUP_FEATURE_EXTRACTION_STR
                else:
                    tool_dict['kind'] = tool_dict['kind']

        except Exception as e:
            print(f'Failed to load script generator "{repr(e)}"')
            res = e
        finally:
            return res

    def save(self, path: str) -> [None, Exception]:
        try:
            dump_obj = self.copy()
            _, ext = os.path.splitext(os.path.basename(path))
            if ext == '.tipp':
                with open(path, 'wb') as f:
                    pickle.dump(dump_obj, f)
            elif ext.lower() == '.json':
                with open(path, 'w') as f:
                    json.dump(dump_obj, f, indent=2, default=encode_ipt)
            elif ext.lower() == '.py':
                with open(path, 'w', newline='') as f:
                    f.write(self.code())
            else:
                raise ValueError(f'Unknown file extension: "{ext}"')
        except Exception as e:
            print(f'Failed to save script generator "{repr(e)}"')
            return e
        else:
            return None

    def save_as_script(self, path: str) -> [None, Exception]:
        try:
            with open(path, 'w') as f:
                f.write(self.code())
        except Exception as e:
            print(f'Failed to save script "{repr(e)}"')
            return e
        else:
            return None

    def copy(self, keep_last_res=False):
        ret = IptScriptGenerator()
        ret.feature_list = self.feature_list[:]
        ret._target_data_base = self._target_data_base
        ret._settings = self._settings.copy()
        for tool_dic in self.ip_operators:
            tmp_tool_dict = {}
            for k, v in tool_dic.items():
                if k == 'tool':  # Remove wrapper data
                    tmp_tool_dict[k] = v.copy(copy_wrapper=False)
                elif k == 'last_res':  # Legacy removal
                    pass
                elif k == 'last_result':  # Rome stored steps, may be activated later
                    pass
                else:
                    tmp_tool_dict[k] = v
            ret.ip_operators.append(tmp_tool_dict)
        return ret

    def group_tools(
        self,
        tool_only: bool = False,
        kinds: tuple = (
            TOOL_GROUP_EXPOSURE_FIXING_STR, TOOL_GROUP_PRE_PROCESSING_STR, TOOL_GROUP_THRESHOLD_STR,
            TOOL_GROUP_ROI_DYNAMIC_STR, TOOL_GROUP_ROI_STATIC_STR, TOOL_GROUP_MASK_CLEANUP_STR,
            TOOL_GROUP_FEATURE_EXTRACTION_STR
        ),
        conditions: dict = None
    ) -> dict:
        ret = {}
        for tag_ in kinds:
            ret[tag_] = [
                op['tool'] if tool_only else op
                for op in self.get_operators(dict(**dict(kind=tag_), **conditions))
            ]
        return ret

    def update_settings_feedback(self, src_wrapper, param: IptParam, call_back):
        if (param is None) or ((param.name == 'bound_level') and (param.value >= 0)):
            img = src_wrapper.current_image
            cv2.line(img, (0, param.value), (src_wrapper.width, self.bound_position), C_RED, 3)
        elif (param is None) or (param.name == 'color_map') or (param.name == 'pseudo_channel'):
            img = src_wrapper.draw_image(
                src_mask=None,
                foreground='false_colour',
                channel=self.pseudo_color_channel,
                color_map=self.pseudo_color_map
            )
        elif (param is None) or (param.name == 'pseudo_background_type'):
            img = src_wrapper.draw_image(src_mask=None, foreground=self.pseudo_background_type)
        else:
            img = None

        if img is not None:
            call_back(img)

    def is_use_last_result(
        self, tool_dict: dict, wrapper: AbstractImageProcessor, previous_state: bool
    ) -> bool:
        if ALLOW_RESULT_CACHE:
            return previous_state and \
                (wrapper is not None) and \
                (wrapper.luid == self._last_wrapper_luid) and \
                (tool_dict.get('changed', True) is False)
        else:
            return False

    def pre_process_image(
        self,
        wrapper,
        use_last_result: bool,
        progress_callback=None,
        current_step: int = -1,
        total_steps: int = -1
    ):
        """Fixes exposition and preprocesses image

        Arguments:
            wrapper {AbstractImageProcessor} -- Current wrapper
            use_last_result {bool} -- Wether or not result can be retrieved from the cache

        Keyword Arguments:
            progress_callback {function} -- Progress call back function (default: {None})
            current_step {int} -- current global progress step (default: {-1})
            total_steps {int} -- Global steps count (default: {-1})

        Returns:
            tuple -- use_last_result, current_step
        """
        tools_ = self.get_operators(constraints=dict(enabled=True, kind=TOOL_GROUP_EXPOSURE_FIXING_STR))
        for tool in tools_:
            wrapper.current_image, use_last_result = self.process_tool(
                tool_dict=tool, wrapper=wrapper, use_last_result=use_last_result
            )
            if progress_callback is not None and total_steps > 0:
                current_step = self.add_progress(
                    progress_callback, current_step, total_steps, 'Fixing exposure', wrapper
                )
        wrapper.store_image(wrapper.current_image, 'exposure_fixed', force_store=True)
        use_last_result = self.build_rois(
            wrapper=wrapper,
            tools=None,
            use_last_result=use_last_result,
            progress_callback=progress_callback,
            current_step=current_step,
            total_steps=total_steps
        )
        wrapper.store_image(
            image=wrapper.draw_rois(
                img=wrapper.draw_image(
                    src_image=wrapper.retrieve_stored_image('exposure_fixed'),
                    src_mask=wrapper.mask,
                    foreground='source',
                    background='bw'
                ),
                rois=wrapper.rois_list
            ),
            text='rois'
        )
        use_last_result = self.build_target_tools(
            wrapper=wrapper, tools=None, use_last_result=use_last_result
        )
        tools_ = self.get_operators(constraints=dict(enabled=True, kind=TOOL_GROUP_PRE_PROCESSING_STR))
        for tool in tools_:
            wrapper.current_image, use_last_result = self.process_tool(
                tool_dict=tool, wrapper=wrapper, use_last_result=use_last_result
            )
            if progress_callback is not None and total_steps > 0:
                current_step = self.add_progress(
                    progress_callback, current_step, total_steps, 'Pre-processing image', wrapper
                )
        wrapper.store_image(wrapper.current_image, 'pre_processed_image', force_store=True)
        self._last_wrapper_luid = wrapper.luid

        return use_last_result, current_step

    def build_target_tools(self, tools: [None, list], wrapper, use_last_result: bool):
        if tools is None:
            tools = self.get_operators(
                constraints=dict(
                    kind=(
                        TOOL_GROUP_PRE_PROCESSING_STR, TOOL_GROUP_THRESHOLD_STR, TOOL_GROUP_MASK_CLEANUP_STR
                    ),
                    enabled=True
                )
            )
        for tool in tools:
            if tool['tool'].get_value_of('tool_target') not in [None, '', 'none']:
                ret, use_last_result = self.process_tool(
                    tool_dict=tool, wrapper=wrapper, use_last_result=use_last_result
                )
                if ret is not None:
                    wrapper.data_output[tool['tool'].result_name] = ret
        return use_last_result

    def build_rois(
        self,
        wrapper,
        tools: [None, list],
        use_last_result: bool,
        progress_callback=None,
        current_step: int = -1,
        total_steps: int = -1
    ):
        if tools is None:
            tools = [
                op for op in self.get_operators(
                    dict(kind=(TOOL_GROUP_ROI_DYNAMIC_STR, TOOL_GROUP_ROI_STATIC_STR), enabled=True)
                )
            ]
        for tool in tools:
            use_last_result = self.is_use_last_result(
                tool_dict=tool, wrapper=wrapper, previous_state=use_last_result
            )
            if use_last_result:
                last_result = tool.get('last_result', None)
            else:
                last_result = None
            if use_last_result and last_result is not None:
                wrapper.add_roi(new_roi=last_result)
            else:
                func = getattr(tool['tool'], 'generate_roi', None)
                if callable(func):
                    roi = func(wrapper=wrapper)
                    if roi is not None:
                        wrapper.add_roi(new_roi=roi)
                        tool['changed'] = False
                        tool['last_result'] = roi
                else:
                    wrapper.error_list.add_error(f'Unable to extract ROI from "{tool.name}"')
            if progress_callback is not None and total_steps > 0:
                current_step = self.add_progress(
                    progress_callback, current_step, total_steps, 'Building ROIs', None
                )
        return use_last_result

    def process_tool(self, tool_dict: dict, wrapper: AbstractImageProcessor, use_last_result):
        use_last_result = self.is_use_last_result(
            tool_dict=tool_dict, wrapper=wrapper, previous_state=use_last_result
        )
        if use_last_result:
            last_result = tool_dict.get('last_result', None)
        else:
            last_result = None
        self._last_wrapper_luid = wrapper.luid
        tool_kind = tool_dict['kind']
        if use_last_result and (last_result is not None):
            if isinstance(tool_dict['last_result'], np.ndarray):
                try:
                    wrapper.store_image(
                        image=tool_dict['last_result'], text=f'cached_image_from_{tool_dict["tool"].name}'
                    )
                except Exception as e:
                    wrapper.error_list.add_error(f'Unable to store cached image because: {repr(e)}')
            ret = tool_dict['last_result']
        else:
            tool = tool_dict['tool'].copy()
            if tool.process_wrapper(wrapper=wrapper):
                ret = tool.result
                tool_dict['changed'] = False
                tool_dict['last_result'] = ret
            else:
                self._last_wrapper_luid = ''
                return None, False

        if tool_kind == TOOL_GROUP_EXPOSURE_FIXING_STR:
            return ret, use_last_result
        if tool_kind == TOOL_GROUP_PRE_PROCESSING_STR:
            return ret, use_last_result
        elif tool_kind == TOOL_GROUP_THRESHOLD_STR:
            return ret, use_last_result
        elif tool_kind in [TOOL_GROUP_ROI_DYNAMIC_STR, TOOL_GROUP_ROI_STATIC_STR]:
            raise AttributeError('ROI tools should never be fed to process_tool')
        elif tool_kind == TOOL_GROUP_MASK_CLEANUP_STR:
            return ret, use_last_result
        elif tool_kind == TOOL_GROUP_FEATURE_EXTRACTION_STR:
            return ret, use_last_result
        else:
            self._last_wrapper_luid = ''
            raise AttributeError('Unknown tool kind')

    def add_progress(self, progress_callback, current_step, total_steps, msg, wrapper):
        if progress_callback is not None:
            progress_callback(current_step, total_steps, msg, wrapper)
        return current_step + 1

    def process_image(self, progress_callback=None, **kwargs):
        res = False
        wrapper = None
        try:
            tools_ = self.group_tools(tool_only=False, conditions=dict(enabled=True))
            total_steps = self.get_operators_count(
                constraints=dict(
                    kind=(
                        TOOL_GROUP_EXPOSURE_FIXING_STR, TOOL_GROUP_PRE_PROCESSING_STR,
                        TOOL_GROUP_THRESHOLD_STR, TOOL_GROUP_ROI_DYNAMIC_STR, TOOL_GROUP_ROI_STATIC_STR,
                        TOOL_GROUP_MASK_CLEANUP_STR, TOOL_GROUP_FEATURE_EXTRACTION_STR
                    ),
                    enabled=True
                )
            )
            total_steps += 4
            current_step = 0

            # Build wrapper
            current_step = self.add_progress(
                progress_callback, current_step, total_steps, 'Building wrapper', None
            )
            wrapper = kwargs.get('wrapper', None)
            if wrapper is None:
                file_path = kwargs.get('file_path', None)
                if not file_path:
                    # Leave if no source
                    res = False
                    wrapper.error_holder.add_error('Missing source image')
                    return False
                wrapper = AbstractImageProcessor(file_path)
            wrapper.lock = True
            if self._target_data_base:
                wrapper.target_database = self._target_data_base

            wrapper.store_image(image=wrapper.current_image, text='true_source_image', force_store=True)

            # Pre process image
            use_last_result, current_step = self.pre_process_image(
                wrapper=wrapper,
                use_last_result=True,
                progress_callback=progress_callback,
                current_step=current_step,
                total_steps=total_steps
            )

            # Build coarse mask
            if len(tools_[TOOL_GROUP_THRESHOLD_STR]) > 0:
                mask_list = []
                mask_names = []
                for i, tool in enumerate(tools_[TOOL_GROUP_THRESHOLD_STR]):
                    target = tool['tool'].get_value_of('tool_target')
                    if target not in [None, '', 'none']:
                        continue
                    mask, use_last_result = self.process_tool(
                        tool_dict=tool, wrapper=wrapper, use_last_result=use_last_result
                    )
                    if mask is not None:
                        mask_list.append(mask)
                        mask_names.append(tool['tool'].short_desc())
                    current_step = self.add_progress(
                        progress_callback, current_step, total_steps, 'Building coarse masks',
                        wrapper if mask is not None else None
                    )

                for img_data, img_name in zip(mask_list, mask_names):
                    wrapper.store_image(img_data, img_name)

                func = getattr(wrapper, self.merge_method, None)
                if func:
                    wrapper.mask = func([mask for mask in mask_list if mask is not None])
                    wrapper.store_image(image=wrapper.mask, text='coarse_mask')
                else:
                    wrapper.error_holder.add_error('Unable to merge coarse masks')
                    res = False
                    return
                current_step = self.add_progress(
                    progress_callback, current_step, total_steps, 'Merged coarse masks',
                    wrapper if func is not None else None
                )

                # ROIs to be applied after mask merging
                handled_rois = ['keep', 'delete', 'erode', 'dilate', 'open', 'close']
                rois_list = [
                    roi for roi in wrapper.rois_list
                    if roi.tag in handled_rois and not (roi.target and roi.target != 'none')
                ]
                wrapper.store_image(
                    image=wrapper.draw_rois(
                        img=wrapper.draw_image(
                            src_image=wrapper.retrieve_stored_image('exposure_fixed'),
                            src_mask=wrapper.mask,
                            foreground='source',
                            background='bw'
                        ),
                        rois=rois_list
                    ),
                    text='used_rois'
                )
                wrapper.mask = wrapper.apply_roi_list(
                    img=wrapper.mask, rois=rois_list, print_dbg=self.display_images
                )
                current_step = self.add_progress(
                    progress_callback, current_step, total_steps, 'Applied ROIs', wrapper
                )

                # Clean mask
                if len(tools_[TOOL_GROUP_MASK_CLEANUP_STR]) > 0:
                    res = True
                    for tool in tools_[TOOL_GROUP_MASK_CLEANUP_STR]:
                        tmp_mask, use_last_result = self.process_tool(
                            tool_dict=tool, wrapper=wrapper, use_last_result=use_last_result
                        )
                        if tmp_mask is None:
                            res = False
                        else:
                            wrapper.mask = tmp_mask
                            res = res and True
                        current_step = self.add_progress(
                            progress_callback, current_step, total_steps, 'Cleaning mask', wrapper
                        )
                else:
                    res = True
                wrapper.store_image(image=wrapper.mask, text='clean_mask')

                # Check that the mask is where it belongs
                if res:
                    enforcers_list = wrapper.get_rois({'enforce'})
                    if len(enforcers_list) > 0:
                        for i, enforcer in enumerate(enforcers_list):
                            mask = wrapper.mask.copy()
                            mask = wrapper.keep_roi(mask, enforcer)
                            partial_ok = np.count_nonzero(mask) > 0
                            res = partial_ok and res
                            if partial_ok:
                                roi_img = np.dstack((np.zeros_like(mask), mask, np.zeros_like(mask)))
                            else:
                                roi_img = np.dstack((np.zeros_like(mask), np.zeros_like(mask), mask))
                            background_img = cv2.bitwise_and(wrapper.mask, wrapper.mask, mask=255 - mask)
                            img = cv2.bitwise_or(
                                roi_img, np.dstack((background_img, background_img, background_img))
                            )
                            enforcer.draw_to(img, line_width=4)
                            wrapper.store_image(img, f'enforcer_{i}_{enforcer.name}')
                        wrapper.store_image(
                            image=wrapper.draw_rois(
                                img=wrapper.draw_image(
                                    src_image=wrapper.retrieve_stored_image('exposure_fixed'),
                                    src_mask=wrapper.mask,
                                    foreground='source',
                                    background='bw'
                                ),
                                rois=enforcers_list
                            ),
                            text='enforcer_rois'
                        )
                        fifth_image = 'enforcer_rois'
                    else:
                        wrapper.store_image(
                            image=wrapper.draw_image(
                                src_image=wrapper.retrieve_stored_image('exposure_fixed'),
                                channel='l',
                                src_mask=wrapper.mask,
                                foreground='false_colour',
                                background='bw',
                                normalize_before=True
                            ),
                            text='pseudo_on_bw'
                        )
                        fifth_image = 'pseudo_on_bw'

                if res and wrapper.mask is not None:
                    wrapper.store_image(
                        wrapper.draw_image(
                            src_image=wrapper.retrieve_stored_image('exposure_fixed'),
                            src_mask=wrapper.mask,
                            foreground='source',
                            background='bw'
                        ),
                        text='mask_on_bw'
                    )
                    self.add_progress(
                        progress_callback, current_step, total_steps, 'Checked mask enforcers', wrapper
                    )

                # Extract features
                if res and not self.threshold_only and len(tools_[TOOL_GROUP_FEATURE_EXTRACTION_STR]) > 0:
                    wrapper.current_image = wrapper.retrieve_stored_image('exposure_fixed')
                    wrapper.csv_data_holder = AbstractCsvWriter()
                    for tool in tools_[TOOL_GROUP_FEATURE_EXTRACTION_STR]:
                        current_data, use_last_result = self.process_tool(
                            tool_dict=tool, wrapper=wrapper, use_last_result=use_last_result
                        )
                        if isinstance(current_data, dict):
                            wrapper.csv_data_holder.data_list.update(current_data)
                        self.add_progress(
                            progress_callback, current_step, total_steps, 'Extracting features', wrapper
                        )
                    res = len(wrapper.csv_data_holder.data_list) > 0

                if self.build_mosaic:
                    old_mosaic = wrapper.store_mosaic
                    wrapper.store_mosaic = 'result'
                    # wrapper.mosaic_data = np.array([['', 'source', ''], ['', 'exposure_fixed', ''],
                    #                                 ['', 'rois', ''], ['', 'pre_processed_image', ''],
                    #                                 [mask_names[0], mask_names[1], mask_names[2]],
                    #                                 ['', 'coarse_mask', ''], ['', 'used_rois', ''],
                    #                                 ['', 'src_img_with_cnt_after_agg_iter_last', ''],
                    #                                 ['clean_mask', 'pseudo_on', 'shapes']])
                    # wrapper.mosaic_data = np.array([['exposure_fixed', 'coarse_mask', 'used_rois'],
                    #                                 ['clean_mask', fifth_image, 'mask_on_bw']])
                    wrapper.mosaic_data = np.array([
                        ['source', 'exposure_fixed', 'pre_processed_image'],
                        [
                            'coarse_mask',
                            'clean_mask',
                            wrapper.draw_image(
                                src_image=wrapper.current_image,
                                src_mask=wrapper.mask,
                                background='bw',
                                foreground='source',
                                bck_grd_luma=120,
                                contour_thickness=6,
                                hull_thickness=6,
                                width_thickness=6,
                                height_thickness=6,
                                centroid_width=20,
                                centroid_line_width=8
                            )
                        ]
                    ])
                    wrapper.print_mosaic(padding=(-4, -4, -4, -4))
                    wrapper.store_mosaic = old_mosaic
            else:
                res = True

            self.add_progress(progress_callback, total_steps, total_steps, 'Done', wrapper)
        except Exception as e:
            if wrapper is not None:
                wrapper.error_holder.add_error(f'Failed : "{repr(e)}"')
            else:
                print(f'Unexpected failure: "{repr(e)}"')
            res = False
        else:
            pass
        finally:
            wrapper.lock = False
            return res

    @staticmethod
    def code_imports():
        # External libraries
        import_lst = list(
            map(lambda x: f'import {x}', ['argparse', 'csv', 'cv2', 'numpy as np', 'os', 'sys'])
        )
        # Add paths
        import_lst.extend([
            '', 'abspath = os.path.abspath(__file__)', 'fld_name = os.path.dirname(abspath)',
            'sys.path.insert(0, fld_name)', 'sys.path.insert(0, os.path.dirname(fld_name))', ''
        ])
        # IPSO Phen libraries
        import_lst.extend([
            'from ip_base.ip_abstract import AbstractImageProcessor',
            'from ip_base.ipt_functional import call_ipt, call_ipt_func',
            'from tools.csv_writer import AbstractCsvWriter'
        ])

        return import_lst

    def code_body(self, root_white_spaces: str = '    '):

        def add_tab(tab_str):
            return tab_str + '    '

        def remove_tab(tab_str):
            return tab_str[:len(tab_str) - 4]

        tools_ = self.group_tools(tool_only=True, conditions=dict(enabled=True))

        code_ = 'def main():\n'
        ws_ct = root_white_spaces

        # Get file name
        # _____________
        code_ += ws_ct + '# Get the file\n' + \
                 ws_ct + '# ____________\n'
        # Set working folder
        code_ += ws_ct + '# Set working folder\n'
        code_ += ws_ct + 'old_wd = os.getcwd()\n'
        code_ += ws_ct + 'abspath = os.path.abspath(__file__)\n'
        code_ += ws_ct + 'fld_name = os.path.dirname(abspath)\n'
        code_ += ws_ct + 'os.chdir(fld_name)\n\n'
        code_ += f'{ws_ct}# Construct the argument parser and parse the arguments\n'
        code_ += f'{ws_ct}ap = argparse.ArgumentParser()\n'
        code_ += f'{ws_ct}ap.add_argument("-i", "--image", required=True, help="Path to the image")\n'
        code_ += f'{ws_ct}ap.add_argument("-d", "--destination", required=False, help="Destination folder")\n'
        code_ += f'{ws_ct}ap.add_argument("-p", "--print_images", required=False, help="Print images, y or n")\n'
        code_ += f'{ws_ct}ap.add_argument("-m", "--print_mosaic", required=False, help="Print mosaic, y or n")\n'
        code_ += f'{ws_ct}args = vars(ap.parse_args())\n'
        code_ += f'{ws_ct}file_name = args["image"]\n'
        code_ += f'{ws_ct}print_images = args.get("print_images", "n") == "y"\n'
        code_ += f'{ws_ct}print_mosaic = args.get("print_mosaic", "n") == "y"\n'
        code_ += f'{ws_ct}dst_folder = args.get("destination", "")\n\n'
        code_ += ws_ct + '# Restore working folder\n'
        code_ += ws_ct + 'os.chdir(old_wd)\n\n'

        code_ += f'{ws_ct}# Build wrapper\n'
        code_ += f'{ws_ct}# _____________\n'
        code_ += ws_ct + "wrapper = AbstractImageProcessor(file_name)\n"
        code_ += ws_ct + "wrapper.lock = True\n"
        code_ += ws_ct + "wrapper.store_image(wrapper.current_image, 'true_source_image')\n"
        code_ += ws_ct + "if print_images or print_mosaic:\n"
        ws_ct = add_tab(ws_ct)
        code_ += ws_ct + "wrapper.store_images = True\n"
        ws_ct = remove_tab(ws_ct)
        code_ += ws_ct + "if print_images:\n"
        ws_ct = add_tab(ws_ct)
        code_ += ws_ct + "wrapper.write_images = 'plot'\n"
        ws_ct = remove_tab(ws_ct)        
        code_ += ws_ct + "if print_mosaic:\n"
        ws_ct = add_tab(ws_ct)
        code_ += ws_ct + "wrapper.write_mosaic = 'plot'\n"
        ws_ct = remove_tab(ws_ct)
        code_ += '\n'

        # Fix image exposition
        # ____________________
        if len(tools_[TOOL_GROUP_EXPOSURE_FIXING_STR]) > 0:
            code_ += ws_ct + '# Fix exposure\n' + \
                     ws_ct + '# ____________________\n'
            for ef_tool in tools_[TOOL_GROUP_EXPOSURE_FIXING_STR]:
                code_ += call_ipt_code(
                    ipt=ef_tool,
                    white_spaces=ws_ct,
                    result_name='wrapper.current_image',
                    generate_imports=False
                )
                code_ += '\n'
            code_ += f'{ws_ct}# Store image name for analysis\n'
            code_ += ws_ct + 'wrapper.store_image(wrapper.current_image, "exposure_fixed")\n'
            code_ += ws_ct + 'analysis_image = "exposure_fixed"\n'
            code_ += '\n'            
        else:
            code_ += f'{ws_ct}# Set default name for image analysis'
            code_ += ws_ct + '# No exposure fix needed\n'
            code_ += ws_ct + 'analysis_image = NONE\n'
            code_ += '\n'
        code_ += ws_ct + "if print_mosaic:\n"
        ws_ct = add_tab(ws_ct)
        code_ += ws_ct + 'wrapper.store_image(wrapper.current_image, "fixed_source")\n'
        ws_ct = remove_tab(ws_ct)

        # Build static ROIs
        # _________________
        if len(tools_[TOOL_GROUP_ROI_STATIC_STR]) > 0:
            code_ += ws_ct + '# Build static ROIs\n' + \
                     ws_ct + '# _________________\n'
            for ef_tool in tools_[TOOL_GROUP_ROI_STATIC_STR]:
                code_ += call_ipt_func_code(
                    ipt=ef_tool,
                    function_name='generate_roi',
                    white_spaces=ws_ct,
                    result_name='roi',
                    generate_imports=False
                )
                code_ += ws_ct + 'if roi is not None:\n'
                ws_ct = add_tab(ws_ct)
                code_ += ws_ct + 'wrapper.add_roi(new_roi=roi)\n'
                ws_ct = remove_tab(ws_ct)
                code_ += '\n'

        # Build dynamic ROIs
        # __________________
        if len(tools_[TOOL_GROUP_ROI_DYNAMIC_STR]) > 0:
            code_ += ws_ct + '# Build dynamic ROIs\n' + \
                     ws_ct + '# __________________\n'
            for ef_tool in tools_[TOOL_GROUP_ROI_DYNAMIC_STR]:
                code_ += call_ipt_func_code(
                    ipt=ef_tool,
                    function_name='generate_roi',
                    white_spaces=ws_ct,
                    result_name='roi',
                    generate_imports=False
                )
                code_ += ws_ct + 'if roi is not None:\n'
                ws_ct = add_tab(ws_ct)
                code_ += ws_ct + 'wrapper.add_roi(new_roi=roi)\n'
                ws_ct = remove_tab(ws_ct)
                code_ += '\n'

        # Pre process image (make segmentation easier)
        # ____________________________________________
        if len(tools_[TOOL_GROUP_PRE_PROCESSING_STR]) > 0:
            code_ += ws_ct + '# Pre process image (make segmentation easier)\n' + \
                     ws_ct + '# ____________________________________________\n'
            for ef_tool in tools_[TOOL_GROUP_PRE_PROCESSING_STR]:
                code_ += call_ipt_code(
                    ipt=ef_tool,
                    white_spaces=ws_ct,
                    result_name='wrapper.current_image',
                    generate_imports=False
                )
                code_ += '\n'
            code_ += ws_ct + "if print_mosaic:\n"       
            ws_ct = add_tab(ws_ct)
            code_ += ws_ct + 'wrapper.store_image(wrapper.current_image, "pre_processed_image")\n'
            ws_ct = remove_tab(ws_ct)

        # Build coarse masks
        # __________________
        if len(tools_[TOOL_GROUP_THRESHOLD_STR]) > 0:
            code_ += ws_ct + '# Build coarse masks\n' + \
                     ws_ct + '# __________________\n'
            code_ += ws_ct + 'mask_list = []\n'
            for mask_tool in tools_[TOOL_GROUP_THRESHOLD_STR]:
                code_ += call_ipt_code(
                    ipt=mask_tool, white_spaces=ws_ct, result_name='current_mask_', generate_imports=False
                )
                code_ += ws_ct + 'mask_list.append(current_mask_)\n'
                code_ += '\n'
            code_ += ws_ct + '# Merge masks\n'
            code_ += f'{ws_ct}func = getattr(wrapper, "{self.merge_method}", None)\n'
            code_ += f'{ws_ct}if func:\n'
            ws_ct = add_tab(ws_ct)
            code_ += ws_ct + 'wrapper.mask = func([mask for mask in mask_list if mask is not None])\n'
            code_ += ws_ct + f'wrapper.store_image(wrapper.mask, f"mask_{self.merge_method}")\n'            
            code_ += ws_ct + "if print_mosaic:\n"       
            ws_ct = add_tab(ws_ct)
            code_ += ws_ct + 'wrapper.store_image(wrapper.mask, "coarse_mask")\n'
            ws_ct = remove_tab(ws_ct)
            ws_ct = remove_tab(ws_ct)
            code_ += ws_ct + 'else:\n'
            ws_ct = add_tab(ws_ct)
            code_ += ws_ct + 'wrapper.error_holder.add_error("Unable to merge coarse masks")\n'
            code_ += ws_ct + 'return\n'
            ws_ct = remove_tab(ws_ct)
            code_ += '\n'

        # ROIs to be applied after mask merging
        # _____________________________________
        code_ += ws_ct + '# ROIs to be applied after mask merging\n' + \
                 ws_ct + '# _____________________________________\n'
        code_ += ws_ct + "handled_rois = ['keep', 'delete', 'erode', 'dilate', 'open', 'close']\n"
        code_ += ws_ct + "rois_list = [roi for roi in wrapper.rois_list if roi.tag in handled_rois and not (roi.target and roi.target != 'none')]\n"
        code_ += ws_ct + f"wrapper.mask = wrapper.apply_roi_list(img=wrapper.mask, rois=rois_list, print_dbg={self.display_images})\n"        
        code_ += ws_ct + "if print_mosaic:\n"       
        ws_ct = add_tab(ws_ct)
        code_ += ws_ct + 'wrapper.store_image(wrapper.mask, "mask_after_roi")\n'
        ws_ct = remove_tab(ws_ct)
        code_ += '\n'

        # Clean mask
        # __________
        if len(tools_[TOOL_GROUP_MASK_CLEANUP_STR]) > 0:
            code_ += ws_ct + '# Clean merged mask\n' + \
                     ws_ct + '# _________________\n'
            for mc_tool in tools_[TOOL_GROUP_MASK_CLEANUP_STR]:
                code_ += call_ipt_code(
                    ipt=mc_tool, white_spaces=ws_ct, result_name='wrapper.mask', generate_imports=False
                )
                code_ += f'{ws_ct}if wrapper.mask is None:\n'
                ws_ct = add_tab(ws_ct)
                code_ += ws_ct + 'return\n'
                ws_ct = remove_tab(ws_ct)
                code_ += '\n'
            code_ += ws_ct + "if print_mosaic:\n"
            ws_ct = add_tab(ws_ct)
            code_ += ws_ct + 'wrapper.store_image(wrapper.mask, "clean_mask")\n'
            ws_ct = remove_tab(ws_ct)
            code_ += '\n'

        # Check that the mask is where it belongs
        # _______________________________________
        code_ += ws_ct + '# Check that the mask is where it belongs\n' + \
                 ws_ct + '# _______________________________________\n'
        code_ += ws_ct + "if print_images:\n"
        ws_ct = add_tab(ws_ct)
        code_ += ws_ct + 'res = True\n'
        code_ += ws_ct + 'enforcers_list = wrapper.get_rois({"enforce"})\n'
        code_ += ws_ct + 'for i, enforcer in enumerate(enforcers_list):\n'
        ws_ct = add_tab(ws_ct)
        code_ += ws_ct + 'mask = wrapper.mask.copy()\n'
        code_ += ws_ct + 'mask = wrapper.keep_roi(mask, enforcer)\n'
        code_ += ws_ct + 'partial_ok = np.count_nonzero(mask) > 0\n'
        code_ += ws_ct + 'res = partial_ok and res\n'
        code_ += ws_ct + 'if partial_ok:\n'
        ws_ct = add_tab(ws_ct)
        code_ += ws_ct + 'roi_img = np.dstack((np.zeros_like(mask), mask, np.zeros_like(mask)))\n'
        ws_ct = remove_tab(ws_ct)
        code_ += ws_ct + 'else:\n'
        ws_ct = add_tab(ws_ct)
        code_ += ws_ct + 'roi_img = np.dstack((np.zeros_like(mask), np.zeros_like(mask), mask))\n'
        ws_ct = remove_tab(ws_ct)
        code_ += ws_ct + 'background_img = cv2.bitwise_and(wrapper.mask, wrapper.mask, mask=255 - mask)\n'
        code_ += ws_ct + 'img = cv2.bitwise_or(roi_img, np.dstack((background_img, background_img, background_img)))\n'
        code_ += ws_ct + 'enforcer.draw_to(img, line_width=4)\n'
        code_ += ws_ct + "wrapper.store_image(img, f'enforcer_{i}_{enforcer.name}')\n"
        ws_ct = remove_tab(ws_ct)
        code_ += ws_ct + 'if not res:\n'
        ws_ct = add_tab(ws_ct)
        code_ += ws_ct + 'return\n'
        ws_ct = remove_tab(ws_ct)
        ws_ct = remove_tab(ws_ct)
        code_ += ws_ct + 'else:\n'
        ws_ct = add_tab(ws_ct)
        code_ += ws_ct + 'enforcers_list = wrapper.get_rois({"enforce"})\n'
        code_ += ws_ct + 'for i, enforcer in enumerate(enforcers_list):\n'
        ws_ct = add_tab(ws_ct)
        code_ += ws_ct + 'mask = wrapper.mask.copy()\n'
        code_ += ws_ct + 'mask = wrapper.keep_roi(mask, enforcer)\n'
        code_ += ws_ct + 'if np.count_nonzero(mask) == 0:\n'
        ws_ct = add_tab(ws_ct)
        code_ += ws_ct + 'return\n'
        ws_ct = remove_tab(ws_ct)
        ws_ct = remove_tab(ws_ct)
        ws_ct = remove_tab(ws_ct)
        code_ += '\n'

        # Extract features
        # ________________
        if not self.threshold_only and (len(tools_[TOOL_GROUP_FEATURE_EXTRACTION_STR]) > 0):
            code_ += ws_ct + "# Extract features\n"
            code_ += ws_ct + "# ________________\n"
            code_ += ws_ct + "wrapper.current_image = wrapper.retrieve_stored_image('exposure_fixed')\n"
            code_ += ws_ct + "wrapper.csv_data_holder = AbstractCsvWriter()\n"
            for fe_tool in tools_[TOOL_GROUP_FEATURE_EXTRACTION_STR]:
                code_ += call_ipt_code(
                    ipt=fe_tool, white_spaces=ws_ct, result_name='current_data', generate_imports=False, return_type='data'
                )
                code_ += f'{ws_ct}if isinstance(current_data, dict):\n'
                ws_ct = add_tab(ws_ct)
                code_ += ws_ct + 'wrapper.csv_data_holder.data_list.update(current_data)\n'
                ws_ct = remove_tab(ws_ct)
                code_ += ws_ct + "else:\n"
                ws_ct = add_tab(ws_ct)
                code_ += ws_ct + 'wrapper.error_holder.add_error("Failed to add extracted data")\n'
                ws_ct = remove_tab(ws_ct)
                code_ += '\n'
            code_ += ws_ct + "# Save CSV\n"
            code_ += ws_ct + 'if dst_folder and (len(wrapper.csv_data_holder.data_list) > 0):\n'
            ws_ct = add_tab(ws_ct)
            code_ += ws_ct + "with open(os.path.join(dst_folder, '', wrapper.file_handler.file_name_no_ext + '.csv'), 'w', newline='') as csv_file_:\n"
            ws_ct = add_tab(ws_ct)
            code_ += ws_ct + "wr = csv.writer(csv_file_, quoting=csv.QUOTE_NONE)\n"
            code_ += ws_ct + "wr.writerow(wrapper.csv_data_holder.header_to_list())\n"
            code_ += ws_ct + "wr.writerow(wrapper.csv_data_holder.data_to_list())\n"
            ws_ct = remove_tab(ws_ct)
            ws_ct = remove_tab(ws_ct)
        else:
            code_ += ws_ct + "# Print selection as color on bw background\n"
            code_ += ws_ct + "# ____________________________________________\n"
            code_ += ws_ct + "id_objects, obj_hierarchy = cv2.findContours(wrapper.mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)[-2:]\n"
            code_ += ws_ct + "wrapper.object_composition(wrapper.current_image, id_objects, obj_hierarchy)\n"
        code_ += '\n'

        # Build mosaic
        # ____________
        code_ += ws_ct + "# Build mosaic\n"
        code_ += ws_ct + "# ____________\n"
        code_ += ws_ct + "if print_mosaic:\n"
        ws_ct = add_tab(ws_ct)
        code_ += ws_ct + "wrapper.store_mosaic = 'result'\n"
        code_ += ws_ct + "wrapper.mosaic_data = np.array([\n"
        ws_ct = add_tab(ws_ct)
        code_ += ws_ct + "['fixed_source', 'pre_processed_image', 'coarse_mask'],\n"
        code_ += ws_ct + "[\n"
        ws_ct = add_tab(ws_ct)
        code_ += ws_ct + "'mask_after_roi',\n"
        code_ += ws_ct + "'clean_mask',\n"
        code_ += ws_ct + "wrapper.draw_image(\n"
        ws_ct = add_tab(ws_ct)
        code_ += ws_ct + "src_image=wrapper.current_image,\n"
        code_ += ws_ct + "src_mask=wrapper.mask,\n"
        code_ += ws_ct + "background='bw',\n"
        code_ += ws_ct + "foreground='source',\n"
        code_ += ws_ct + "bck_grd_luma=120,\n"
        code_ += ws_ct + "contour_thickness=6,\n"
        code_ += ws_ct + "hull_thickness=6,\n"
        code_ += ws_ct + "width_thickness=6,\n"
        code_ += ws_ct + "height_thickness=6,\n"
        code_ += ws_ct + "centroid_width=20,\n"
        code_ += ws_ct + "centroid_line_width=8\n"
        ws_ct = remove_tab(ws_ct)
        code_ += ws_ct + ")\n"
        ws_ct = remove_tab(ws_ct)
        code_ += ws_ct + "]\n"
        ws_ct = remove_tab(ws_ct)
        code_ += ws_ct + "])\n"
        code_ += ws_ct + "wrapper.print_mosaic(padding=(-4, -4, -4, -4))\n"
        ws_ct = remove_tab(ws_ct)
        code_ += '\n'

        code_ += f'{ws_ct}print("Done.")'

        return code_

    def __str__(self):
        tools_ = self.group_tools(tool_only=True, conditions=dict(enabled=True))

        res = 'Pipeline:\n'
        # Exposure fixing
        if len(tools_[TOOL_GROUP_EXPOSURE_FIXING_STR]) > 0:
            for wbf in tools_[TOOL_GROUP_EXPOSURE_FIXING_STR]:
                res += f'Exposure fixer: {str(wbf)}\n'
        else:
            res += 'No exposure fixer\n'

        # Pre-processing
        if len(tools_[TOOL_GROUP_PRE_PROCESSING_STR]) > 0:
            for wbf in tools_[TOOL_GROUP_PRE_PROCESSING_STR]:
                res += f'WB fixer: {str(wbf)}\n'
        else:
            res += 'No pre-processor\n'

        # Coarse mask generation
        if len(tools_[TOOL_GROUP_THRESHOLD_STR]) > 0:
            for cmg in tools_[TOOL_GROUP_THRESHOLD_STR]:
                res += f'Partial channel mask: : {str(cmg)}\n'
        else:
            res += 'No coarse mask generation\n'

        # Post merging ROIs
        if len(tools_[TOOL_GROUP_ROI_DYNAMIC_STR]) > 0:
            for wbf in tools_[TOOL_GROUP_ROI_DYNAMIC_STR]:
                res += f'ROI: {str(wbf)}\n'
        else:
            res += 'No pre-processing ROIs\n'

        # Mask cleaning
        if len(tools_[TOOL_GROUP_MASK_CLEANUP_STR]) > 0:
            for cm in tools_[TOOL_GROUP_MASK_CLEANUP_STR]:
                res += f'Partial channel mask: : {str(cm)}\n'
        else:
            res += 'No mask cleaner selected\n'

        # Extracted features
        if len(tools_[TOOL_GROUP_FEATURE_EXTRACTION_STR]) > 0:
            for cm in tools_[TOOL_GROUP_FEATURE_EXTRACTION_STR]:
                res += f'Feature extraction: : {str(cm)}\n'
        else:
            res += 'No feature extraction\n'

        res += 'Extracted features: ' + ', '.join([
            f['feature'] for f in self.feature_list if f['enabled'] is True
        ]) + '\n'
        res += '\n'
        # Options
        res += 'Options:\n'
        res += self.desc_merge_method + '\n'
        res += self.desc_display_images + '\n'

        return res

    @staticmethod
    def code_footer():
        code_ = 'if __name__ == "__main__":\n'
        code_ += '    main()\n'
        return code_

    def reset(self):
        self.ip_operators = []
        self._feature_list = self._init_features()
        self._settings.reset(is_update_widgets=True)

    def code(self):
        return '\n'.join(self.code_imports()) + '\n\n\n' + self.code_body() + '\n\n\n' + self.code_footer()

    def add_operator(self, operator, kind: str, enabled_state: bool = True):
        self.ip_operators.append(
            dict(tool=operator, enabled=enabled_state, kind=kind, uuid=str(uuid4()), last_result=None)
        )

    def delete_operators(self, constraints: dict):
        i = 0
        while i < len(self.ip_operators):
            current_op = self.ip_operators[i]
            if self.op_matches(current_op, constraints=constraints):
                op_to_delete = self.ip_operators.pop(self.ip_operators.index(current_op))
                for p in op_to_delete['tool'].gizmos:
                    p.clear_widgets()
            else:
                i += 1

    @staticmethod
    def op_matches(operator: dict, constraints: dict):
        for k, v in constraints.items():
            op_val = operator.get(k, None)
            if op_val is None:
                return False
            elif isinstance(v, list) or isinstance(v, tuple):
                if op_val not in v:
                    return False
            elif op_val != v:
                return False
        return True

    def get_operators(self, constraints: dict = {}) -> list:
        res = []
        for op in self.ip_operators:
            if not constraints:
                res.append(op)
            else:
                if self.op_matches(operator=op, constraints=constraints):
                    res.append(op)
        return res

    def get_operators_count(self, constraints: dict) -> int:
        return len(self.get_operators(constraints=constraints))

    def swap_operators(self, indexes: list):
        for i, j in indexes:
            self.ip_operators[i], self.ip_operators[j] = self.ip_operators[j], self.ip_operators[i]

    def get_something(self, key: str):
        """
        Return either an operator or a feature, priority is given to operators
        :param key: uuid of operator or name of feature
        """
        tool = self.get_operators(constraints=dict(uuid=key))
        if len(tool) > 0:
            return tool[0]
        for feature in self.feature_list:
            if feature['feature'] == key:
                return feature
        return None

    def toggle_enabled_state(self, key: str) -> None:
        """
        Toggles enabled of matching key
        :param key: uuid for tools, name for settings
        """
        tool = self.get_operators(constraints=dict(uuid=key))
        if len(tool) > 0:
            tool[0]['enabled'] = not tool[0]['enabled']
            if tool[0]['kind'] in [TOOL_GROUP_EXPOSURE_FIXING_STR]:
                to_reset = [
                    TOOL_GROUP_ROI_DYNAMIC_STR, TOOL_GROUP_ROI_STATIC_STR, TOOL_GROUP_PRE_PROCESSING_STR,
                    TOOL_GROUP_THRESHOLD_STR, TOOL_GROUP_MASK_CLEANUP_STR
                ]
            if tool[0]['kind'] in [TOOL_GROUP_ROI_DYNAMIC_STR, TOOL_GROUP_ROI_STATIC_STR]:
                to_reset = [
                    TOOL_GROUP_PRE_PROCESSING_STR, TOOL_GROUP_THRESHOLD_STR, TOOL_GROUP_MASK_CLEANUP_STR
                ]
            elif tool[0]['kind'] == TOOL_GROUP_PRE_PROCESSING_STR:
                to_reset = [
                    TOOL_GROUP_PRE_PROCESSING_STR, TOOL_GROUP_THRESHOLD_STR, TOOL_GROUP_MASK_CLEANUP_STR
                ]
            elif tool[0]['kind'] == TOOL_GROUP_THRESHOLD_STR:
                to_reset = [TOOL_GROUP_THRESHOLD_STR, TOOL_GROUP_MASK_CLEANUP_STR]
            elif tool[0]['kind'] == TOOL_GROUP_MASK_CLEANUP_STR:
                to_reset = [TOOL_GROUP_MASK_CLEANUP_STR]
            elif tool[0]['kind'] == TOOL_GROUP_FEATURE_EXTRACTION_STR:
                to_reset = [TOOL_GROUP_FEATURE_EXTRACTION_STR]
            else:
                to_reset = []
            tools_to_reset = self.get_operators(constraints=dict(kind=to_reset))
            for tool_dict in tools_to_reset:
                tool_dict['last_result'] = None
            return
        for feature in self.feature_list:
            if feature['feature'] == key:
                feature['enabled'] = not feature['enabled']
                return

    @property
    def is_empty(self):
        return len(self.get_operators(dict(enabled=True))) == 0

    @property
    def is_functional(self):
        return len(self.get_operators(dict(kind=TOOL_GROUP_THRESHOLD_STR, enabled=True))) > 0

    @property
    def target_data_base(self):
        return self._target_data_base

    @target_data_base.setter
    def target_data_base(self, value):
        self._target_data_base = value

    @property
    def feature_list(self):
        if (len(self._feature_list) <= 0) or isinstance(self._feature_list[0], str):
            self._feature_list = sorted([
                dict(feature=f, enabled=True if f in self._feature_list else False)
                for f in AVAILABLE_FEATURES
            ],
                                        key=lambda x: x['feature'])
        return self._feature_list

    @feature_list.setter
    def feature_list(self, value):
        if (len(value) > 0) and isinstance(self._feature_list[0], dict):
            self._feature_list = value
        else:
            self._feature_list = sorted([
                dict(feature=f, enabled=True if f in value else False) for f in AVAILABLE_FEATURES
            ],
                                        key=lambda x: x['feature'])

    @property
    def desc_merge_method(self):
        if self.merge_method == 'multi_and':
            return 'Partial masks will be merged with a logical AND'
        elif self.merge_method == 'multi_or':
            return 'Partial masks will be merged with a logical OR'
        else:
            return 'Unknown mask merge method'

    @property
    def desc_display_images(self):
        return f'Display step images at the end: {self.display_images}'

    @property
    def settings(self):
        return self._settings

    @settings.setter
    def settings(self, value):
        self._settings = value

    @property
    def merge_method(self):
        tmp = self._settings.get_value_of('merge_method')
        if tmp == 'l_and':
            self._settings.set_value_of('merge_method', 'multi_and')
        elif tmp == 'l_or':
            self._settings.set_value_of('merge_method', 'multi_or')
        return self._settings.get_value_of('merge_method')

    @property
    def display_images(self):
        return self._settings.get_value_of('display_images') == 1

    @property
    def threshold_only(self):
        return self._settings.get_value_of('threshold_only') == 1

    @property
    def build_mosaic(self):
        return self._settings.get_value_of('build_mosaic') == 1

    @property
    def bound_position(self):
        return self._settings.get_value_of('bound_level')

    @property
    def pseudo_color_map(self):
        color_map = self._settings.get_value_of('color_map')
        _, color_map = color_map.split('_')
        return int(color_map)

    @property
    def pseudo_color_channel(self):
        return self._settings.get_value_of('pseudo_channel')

    @property
    def pseudo_background_type(self):
        return self._settings.get_value_of('pseudo_background_type')

    @property
    def use_default_script(self):
        return self._settings.get_value_of('use_default_script')

    @property
    def ip_operators(self):
        return self._ip_operators

    @ip_operators.setter
    def ip_operators(self, value):
        self._ip_operators = value

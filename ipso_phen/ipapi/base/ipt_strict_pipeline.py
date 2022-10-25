import json
import os
import pickle
from copy import copy
from uuid import uuid4
from datetime import datetime as dt
from typing import Union

import cv2
import numpy as np

import logging

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))

from ipso_phen.ipapi.base.ip_abstract import BaseImageProcessor
from ipso_phen.ipapi.base.ip_common import AVAILABLE_FEATURES, C_RED, ToolFamily
from ipso_phen.ipapi.base.ipt_abstract import (
    IptParam,
    IptBase,
    IptParamHolder,
    CLASS_NAME_KEY,
    MODULE_NAME_KEY,
    PARAMS_NAME_KEY,
)
from ipso_phen.ipapi.base.ipt_functional import call_ipt_code, call_ipt_func_code
from ipso_phen.ipapi.tools.csv_writer import AbstractCsvWriter
from ipso_phen.ipapi.tools.common_functions import get_module_classes, force_directories
from ipso_phen.ipapi.tools.error_holder import ErrorHolder


last_script_version = "0.6.0.0"


class SettingsHolder(IptParamHolder):
    def __init__(self, **kwargs):
        self.update_feedback_items = []
        super(SettingsHolder, self).__init__(**kwargs)

    def build_params(self):
        self.add_checkbox(name="threshold_only", desc="Find mask only", default_value=0)
        self.add_combobox(
            name="merge_method",
            desc="Select merge method",
            values=dict(multi_and="Logical AND", multi_or="Logical OR"),
            default_value="multi_and",
        )
        self.add_checkbox(
            name="display_images", desc="Display step by step images", default_value=1
        )
        self.add_checkbox(name="build_mosaic", desc="Display mosaic", default_value=0)
        self.add_text_input(
            name="mosaic_items",
            desc="Mosaic items",
            default_value="""source,exposure_fixed,pre_processed_image\ncoarse_mask,clean_mask, mask_on_exp_fixed_bw_with_morph""",
            hint="""Names of the images to be included in the mosaic""",
            is_single_line=False,
        )
        self.add_spin_box(
            name="bound_level",
            desc="Horizontal bound position",
            default_value=-1,
            minimum=-1,
            maximum=4000,
            hint="Horizontal bound normally used to separate above from below ground",
        )
        self.add_channel_selector(
            name="pseudo_channel",
            desc="Channel used for pseudo color images",
            default_value="l",
            hint="Select channel for pseudo color image",
        )
        self.add_color_map_selector(name="color_map", default_value="c_2")
        self.add_combobox(
            name="pseudo_background_type",
            desc="Background type for pseudo color images",
            default_value="bw",
            values=dict(
                bw="Black & white source",
                source="Source image",
                black="Black backround",
                white="White background",
                silver="Silver background",
            ),
        )
        self.add_checkbox(
            name="use_default_script",
            desc="Use default script if present",
            default_value=0,
        )
        self.add_text_output(
            is_single_line=True,
            name="image_output_path",
            desc="Images output folder",
            default_value="",
            hint="Path where images will be copied, if not absolute, will be relative to output CSV data file",
        )
        self.add_text_input(
            name="last_image",
            desc="Last image to be displayed",
            default_value="",
            hint="""Image to be displayed once the pipeline has finished.
            If empty last image will be displayed.
            Overridden by mosaic setting""",
        )
        self.update_feedback_items = [
            "bound_level",
            "pseudo_channel",
            "color_map",
            "pseudo_background_type",
        ]

    def reset(self, is_update_widgets: bool = True):
        for p in self._param_list:
            if p.is_input:
                p.value = p.default_value
                p.clear_widgets()


class IptStrictPipeline(object):
    def __init__(self, **kwargs):
        self._ip_operators = kwargs.get("_ip_operators", [])
        self._target_data_base = kwargs.get("_target_data_base", None)
        self._settings = kwargs.get("_settings", SettingsHolder())
        self._last_wrapper_luid = ""
        self.use_cache = kwargs.get("use_cache", True)
        self.image_output_path = kwargs.get("image_output_path", "")
        self.name = kwargs.get("name", "")
        self.last_error: ErrorHolder = ErrorHolder(self)

    def __repr__(self):
        return json.dumps(self.to_json(self.name), indent=2, sort_keys=False)

    def __str__(self):
        return f"Pipeline {self.name}"

    @staticmethod
    def _init_features():
        return sorted(
            [dict(feature=f, enabled=True) for f in AVAILABLE_FEATURES],
            key=lambda x: x["feature"],
        )

    def to_json(self, name: str) -> dict:
        save_dict = {
            "title": "IPSO Phen pipeline",
            "name": name,
            "date": dt.now().strftime("%Y_%b_%d_%H-%M-%S"),
            "version": last_script_version,
        }
        # Add settings
        save_dict["settings"] = self._settings.params_to_dict()
        save_dict["ip_modules"] = [
            {
                "module": tool_dict["tool"].to_json(),
                "enabled": tool_dict["enabled"],
                "kind": tool_dict["kind"],
                "uuid": tool_dict["uuid"],
            }
            for tool_dict in self.get_operators()
        ]
        return save_dict

    @classmethod
    def from_json(cls, json_data: Union[str, dict]):
        if isinstance(json_data, str):
            with open(json_data, "r") as f:
                saved_dict = json.load(f)
        else:
            saved_dict = json_data
        res = cls()
        res._settings = SettingsHolder(**saved_dict["settings"])
        res.name = saved_dict["name"]
        for module in saved_dict["ip_modules"]:
            tool = IptBase.from_json(module["module"])
            if isinstance(tool, Exception):
                res.last_error.add_error(
                    new_error_text=f"Failed to load {module['name']}: {repr(tool)}",
                    new_error_kind="pipeline_load_error",
                    target_logger=logger,
                )
            elif isinstance(tool, IptBase):
                res.ip_operators.append(
                    dict(
                        tool=tool,
                        enabled=module["enabled"],
                        kind=module["kind"],
                        uuid=module["uuid"],
                        last_result=None,
                    )
                )

        return res

    @classmethod
    def load(cls, path: str) -> Union[object, Exception]:
        res = None
        try:
            _, ext = os.path.splitext(os.path.basename(path))
            if ext == ".tipp":
                with open(path, "rb") as f:
                    res = pickle.load(f)

                # Check that we have all settings
                if not hasattr(res, "_settings"):
                    res._settings = SettingsHolder()

                settings_checker = SettingsHolder()
                override_updates = False
                for setting_ in settings_checker.gizmos:
                    s = res._settings.find_by_name(name=setting_.name)
                    if s is None:
                        res._settings.add(copy(setting_))
                        override_updates = True
                if override_updates:
                    res._settings.update_feedback_items = (
                        settings_checker.update_feedback_items
                    )

                # Check attributes
                if not hasattr(res, "_last_wrapper_luid"):
                    res._last_wrapper_luid = ""
                if not hasattr(res, "last_error"):
                    res.last_error = ErrorHolder(res)
            elif ext.lower() == ".json":
                res = cls.from_json(json_data=path)
            else:
                raise ValueError(f'Unknown file extension: "{ext}"')

            # Fix all taggins
            for tool_dict in res.get_operators():
                current_kind = tool_dict["kind"]
                if current_kind == "exp_fixer":
                    tool_dict["kind"] = ToolFamily.EXPOSURE_FIXING
                elif current_kind == "pre_processor":
                    tool_dict["kind"] = ToolFamily.PRE_PROCESSING
                elif current_kind == "mask_generator":
                    tool_dict["kind"] = ToolFamily.THRESHOLD
                elif current_kind == "mask_cleaner":
                    tool_dict["kind"] = ToolFamily.MASK_CLEANUP
                elif current_kind == "roi_post_merge":
                    tool_dict["kind"] = ToolFamily.ROI_PP_IMAGE_STR
                elif current_kind == "roi_dynamic":
                    tool_dict["kind"] = ToolFamily.ROI_PP_IMAGE_STR
                elif current_kind == "roi_static":
                    tool_dict["kind"] = ToolFamily.ROI_PP_IMAGE_STR
                elif current_kind == "ROI (dynamic)":
                    tool_dict["kind"] = ToolFamily.ROI_PP_IMAGE_STR
                elif current_kind == "ROI (static)":
                    tool_dict["kind"] = ToolFamily.ROI_PP_IMAGE_STR
                elif current_kind == "feature_extractor":
                    tool_dict["kind"] = ToolFamily.FEATURE_EXTRACTION
                elif current_kind == "Image generator":
                    tool_dict["kind"] = ToolFamily.IMAGE_GENERATOR
                else:
                    tool_dict["kind"] = tool_dict["kind"]
                tool_dict.pop("changed", None)

        except Exception as e:
            if res is None:
                logger.error(f'Failed to load script generator "{repr(e)}"')
            else:
                res.last_error.add_error(
                    new_error_text=f'Failed to load script generator "{repr(e)}"',
                    new_error_kind="pipeline_load_error",
                    target_logger=logger,
                )
            res = e
        finally:
            return res

    def save(self, path: str) -> Union[None, Exception]:
        self.last_error.clear()
        try:
            dump_obj = self.copy()
            pipeline_name, ext = os.path.splitext(os.path.basename(path))
            if ext == ".tipp":
                with open(path, "wb") as f:
                    pickle.dump(dump_obj, f)
            elif ext.lower() == ".json":
                with open(path, "w") as f:
                    json.dump(
                        self.to_json(
                            name=self.name
                            if hasattr(self, "name") and self.name
                            else pipeline_name
                        ),
                        f,
                        indent=2,
                    )
            elif ext.lower() == ".py":
                with open(path, "w", newline="") as f:
                    f.write(self.code())
            else:
                raise ValueError(f'Unknown file extension: "{ext}"')
        except Exception as e:
            self.last_error.add_error(
                new_error_text=f'Failed to save script generator "{repr(e)}"',
                new_error_kind="pipeline_save_error",
                target_logger=logger,
            )
            return e
        else:
            return None

    def save_as_script(self, path: str) -> Union[None, Exception]:
        self.last_error.clear()
        try:
            with open(path, "w") as f:
                f.write(self.code())
        except Exception as e:
            self.last_error.add_error(
                new_error_text=f'Failed to save script generator "{repr(e)}"',
                new_error_kind="pipeline_save_error",
                target_logger=logger,
            )
            return e
        else:
            return None

    def copy(self, keep_last_res=False):
        ret = IptStrictPipeline(use_cache=self.use_cache)
        ret._target_data_base = self._target_data_base
        ret._settings = self._settings.copy()
        ret.image_output_path = self.image_output_path
        for tool_dic in self.ip_operators:
            tmp_tool_dict = {}
            for k, v in tool_dic.items():
                if k == "tool":  # Remove wrapper data
                    tmp_tool_dict[k] = v.copy(copy_wrapper=False)
                elif k == "last_res":  # Legacy removal
                    pass
                elif k == "last_result":  # Rome stored steps, may be activated later
                    pass
                else:
                    tmp_tool_dict[k] = v
            ret.ip_operators.append(tmp_tool_dict)
        return ret

    def group_tools(
        self,
        tool_only: bool = False,
        kinds: tuple = (
            ToolFamily.EXPOSURE_FIXING,
            ToolFamily.PRE_PROCESSING,
            ToolFamily.THRESHOLD,
            ToolFamily.ROI_RAW_IMAGE,
            ToolFamily.ROI_PP_IMAGE,
            ToolFamily.MASK_CLEANUP,
            ToolFamily.FEATURE_EXTRACTION,
            ToolFamily.IMAGE_GENERATOR,
        ),
        conditions: dict = {},
    ) -> dict:
        ret = {}
        for tag_ in kinds:
            ret[tag_] = [
                op["tool"] if tool_only else op
                for op in self.get_operators(dict(**dict(kind=tag_), **conditions))
            ]
        return ret

    def update_settings_feedback(self, src_wrapper, param: IptParam, call_back):
        if (param is None) or ((param.name == "bound_level") and (param.value >= 0)):
            img = src_wrapper.current_image
            cv2.line(
                img,
                (0, param.value),
                (src_wrapper.width, self.bound_position),
                C_RED,
                3,
            )
        elif (
            (param is None)
            or (param.name == "color_map")
            or (param.name == "pseudo_channel")
        ):
            img = src_wrapper.draw_image(
                src_mask=None,
                foreground="false_colour",
                channel=self.pseudo_color_channel,
                color_map=self.pseudo_color_map,
            )
        elif (param is None) or (param.name == "pseudo_background_type"):
            img = src_wrapper.draw_image(
                src_mask=None, foreground=self.pseudo_background_type
            )
        else:
            img = None

        if img is not None:
            call_back(img)

    def is_use_last_result(
        self, tool_dict: dict, wrapper: BaseImageProcessor, previous_state: bool
    ) -> bool:
        if self.use_cache:
            return (
                previous_state
                and (wrapper is not None)
                and (wrapper.luid == self._last_wrapper_luid)
                and (tool_dict.get("last_result", None) is not None)
            )
        else:
            return False

    def fix_exposure(
        self,
        wrapper,
        use_last_result: bool,
        progress_callback=None,
        current_step: int = -1,
        total_steps: int = -1,
    ):
        """Applies exposure fixing modules

        Arguments:
            wrapper {BaseImageProcessor} -- Current wrapper
            use_last_result {bool} -- Wether or not result can be retrieved from the cache

        Keyword Arguments:
            progress_callback {function} -- Progress call back function (default: {None})
            current_step {int} -- current global progress step (default: {-1})
            total_steps {int} -- Global steps count (default: {-1})

        Returns:
            tuple -- use_last_result, current_step
        """
        tools_ = self.get_operators(
            constraints=dict(
                enabled=True,
                kind=[ToolFamily.EXPOSURE_FIXING, ToolFamily.WHITE_BALANCE],
            )
        )
        for tool in tools_:
            wrapper.current_image, use_last_result = self.process_tool(
                tool_dict=tool, wrapper=wrapper, use_last_result=use_last_result
            )
            if progress_callback is not None and total_steps > 0:
                current_step = self.add_progress(
                    progress_callback,
                    current_step,
                    total_steps,
                    "Fixing exposure",
                    wrapper,
                )
        wrapper.store_image(wrapper.current_image, "exposure_fixed", force_store=True)

        return use_last_result, current_step

    def pre_process_image(
        self,
        wrapper,
        use_last_result: bool,
        progress_callback=None,
        current_step: int = -1,
        total_steps: int = -1,
    ):
        """Fixes exposition and preprocesses image

        Arguments:
            wrapper {BaseImageProcessor} -- Current wrapper
            use_last_result {bool} -- Wether or not result can be retrieved from the cache

        Keyword Arguments:
            progress_callback {function} -- Progress call back function (default: {None})
            current_step {int} -- current global progress step (default: {-1})
            total_steps {int} -- Global steps count (default: {-1})

        Returns:
            tuple -- use_last_result, current_step
        """
        use_last_result, current_step = self.build_rois(
            wrapper=wrapper,
            tools=None,
            use_last_result=use_last_result,
            progress_callback=progress_callback,
            current_step=current_step,
            total_steps=total_steps,
            target_raw_image=True,
            target_pp_image=False,
        )
        use_last_result, current_step = self.fix_exposure(
            wrapper=wrapper,
            use_last_result=use_last_result,
            progress_callback=progress_callback,
            current_step=current_step,
            total_steps=total_steps,
        )
        use_last_result, current_step = self.build_rois(
            wrapper=wrapper,
            tools=None,
            use_last_result=use_last_result,
            progress_callback=progress_callback,
            current_step=current_step,
            total_steps=total_steps,
            target_raw_image=False,
            target_pp_image=True,
        )
        wrapper.store_image(
            image=wrapper.retrieve_stored_image("exp_fixed_roi"),
            text="rois",
        )
        use_last_result = self.build_target_tools(
            wrapper=wrapper, tools=None, use_last_result=use_last_result
        )
        tools_ = self.get_operators(
            constraints=dict(enabled=True, kind=ToolFamily.PRE_PROCESSING)
        )
        for tool in tools_:
            wrapper.current_image, use_last_result = self.process_tool(
                tool_dict=tool, wrapper=wrapper, use_last_result=use_last_result
            )
            if progress_callback is not None and total_steps > 0:
                current_step = self.add_progress(
                    progress_callback,
                    current_step,
                    total_steps,
                    "Pre-processing image",
                    wrapper,
                )
        wrapper.store_image(
            wrapper.current_image, "pre_processed_image", force_store=True
        )
        self._last_wrapper_luid = wrapper.luid

        return use_last_result, current_step

    def build_target_tools(
        self, tools: Union[None, list], wrapper, use_last_result: bool
    ):
        if tools is None:
            tools = self.get_operators(
                constraints=dict(
                    kind=(
                        ToolFamily.PRE_PROCESSING,
                        ToolFamily.THRESHOLD,
                        ToolFamily.MASK_CLEANUP,
                    ),
                    enabled=True,
                )
            )
        for tool in tools:
            if tool["tool"].get_value_of("tool_target") not in [None, "", "none"]:
                ret, use_last_result = self.process_tool(
                    tool_dict=tool, wrapper=wrapper, use_last_result=use_last_result
                )
                if ret is not None:
                    wrapper.data_output[tool["tool"].result_name] = ret
        return use_last_result

    def build_rois(
        self,
        wrapper,
        tools: Union[None, list],
        use_last_result: bool,
        progress_callback=None,
        current_step: int = -1,
        total_steps: int = -1,
        target_raw_image=True,
        target_pp_image=True,
    ):
        if target_raw_image and target_pp_image:
            kinds = (ToolFamily.ROI_RAW_IMAGE_STR, ToolFamily.ROI_PP_IMAGE_STR)
        elif target_raw_image:
            kinds = (ToolFamily.ROI_RAW_IMAGE_STR,)
        elif target_pp_image:
            kinds = (ToolFamily.ROI_PP_IMAGE_STR,)
        else:
            kinds = ()
        if tools is None:
            tools = [op for op in self.get_operators(dict(kind=kinds, enabled=True))]
        for tool in tools:
            use_last_result = self.is_use_last_result(
                tool_dict=tool, wrapper=wrapper, previous_state=use_last_result
            )
            if use_last_result:
                last_result = tool.get("last_result", None)
            else:
                last_result = None
            if use_last_result and last_result is not None:
                wrapper.add_roi(new_roi=last_result)
            else:
                func = getattr(tool["tool"], "generate_roi", None)
                if callable(func):
                    roi = func(wrapper=wrapper)
                    if roi is not None:
                        wrapper.add_roi(new_roi=roi)
                        tool["last_result"] = roi
                else:
                    wrapper.error_list.add_error(
                        f'Unable to extract ROI from "{tool.name}"',
                        target_logger=logger,
                    )
            if progress_callback is not None and total_steps > 0:
                current_step = self.add_progress(
                    progress_callback, current_step, total_steps, "Building ROIs", None
                )
        return use_last_result, current_step

    def process_tool(self, tool_dict: dict, wrapper: BaseImageProcessor, use_last_result):
        use_last_result = self.is_use_last_result(
            tool_dict=tool_dict, wrapper=wrapper, previous_state=use_last_result
        )
        if use_last_result:
            last_result = tool_dict.get("last_result", None)
        else:
            last_result = None
        self._last_wrapper_luid = wrapper.luid
        tool_kind = tool_dict["kind"]
        if use_last_result and (last_result is not None):
            if isinstance(tool_dict["last_result"], np.ndarray):
                try:
                    wrapper.store_image(
                        image=tool_dict["last_result"],
                        text=f'cached_image_from_{tool_dict["tool"].name}',
                    )
                except Exception as e:
                    wrapper.error_list.add_error(
                        f"Unable to store cached image because: {repr(e)}",
                        target_logger=logger,
                    )
            ret = tool_dict["last_result"]
        else:
            tool = tool_dict["tool"].copy()
            if tool.process_wrapper(wrapper=wrapper):
                if (
                    tool_dict["kind"]
                    in [ToolFamily.FEATURE_EXTRACTION, ToolFamily.IMAGE_GENERATOR]
                ) and (hasattr(tool, "data_dict")):
                    ret = tool.data_dict
                else:
                    ret = tool.result
                tool_dict["last_result"] = ret
            else:
                self._last_wrapper_luid = ""
                return None, False

        if tool_kind == ToolFamily.EXPOSURE_FIXING:
            return ret, use_last_result
        if tool_kind == ToolFamily.PRE_PROCESSING:
            return ret, use_last_result
        elif tool_kind == ToolFamily.THRESHOLD:
            return ret, use_last_result
        elif tool_kind in [ToolFamily.ROI_RAW_IMAGE_STR, ToolFamily.ROI_PP_IMAGE_STR]:
            raise AttributeError("ROI tools should never be fed to process_tool")
        elif tool_kind == ToolFamily.MASK_CLEANUP:
            return ret, use_last_result
        elif tool_kind in [ToolFamily.FEATURE_EXTRACTION, ToolFamily.IMAGE_GENERATOR]:
            return ret, use_last_result
        else:
            self._last_wrapper_luid = ""
            raise AttributeError("Unknown tool kind")

    def add_progress(self, progress_callback, current_step, total_steps, msg, wrapper):
        if progress_callback is not None:
            progress_callback(current_step, total_steps, msg, wrapper)
        return current_step + 1

    def process_image(self, progress_callback=None, **kwargs):
        res = False
        wrapper = None
        self.last_error.clear()
        try:
            save_mask = False
            for tool in (
                op["tool"]
                for op in self.get_operators(
                    constraints=dict(
                        kind=(
                            ToolFamily.EXPOSURE_FIXING,
                            ToolFamily.PRE_PROCESSING,
                            ToolFamily.THRESHOLD,
                            ToolFamily.ROI_RAW_IMAGE_STR,
                            ToolFamily.ROI_PP_IMAGE_STR,
                            ToolFamily.MASK_CLEANUP,
                            ToolFamily.FEATURE_EXTRACTION,
                            ToolFamily.IMAGE_GENERATOR,
                        ),
                        enabled=True,
                    )
                )
            ):
                if tool.has_param("path") and self.image_output_path:
                    tool.set_value_of(key="path", value=self.image_output_path)
                save_mask = save_mask or tool.needs_previous_mask

            tools_ = self.group_tools(tool_only=False, conditions=dict(enabled=True))

            total_steps = self.get_operators_count(
                constraints=dict(
                    kind=(
                        ToolFamily.EXPOSURE_FIXING,
                        ToolFamily.PRE_PROCESSING,
                        ToolFamily.THRESHOLD,
                        ToolFamily.ROI_RAW_IMAGE_STR,
                        ToolFamily.ROI_PP_IMAGE_STR,
                        ToolFamily.MASK_CLEANUP,
                        ToolFamily.FEATURE_EXTRACTION,
                        ToolFamily.IMAGE_GENERATOR,
                    ),
                    enabled=True,
                )
            )
            total_steps += 4
            current_step = 0

            # Build wrapper
            current_step = self.add_progress(
                progress_callback, current_step, total_steps, "Building wrapper", None
            )
            wrapper = kwargs.get("wrapper", None)
            if wrapper is None:
                file_path = kwargs.get("file_path", None)
                if not file_path:
                    # Leave if no source
                    res = False
                    logger.error("Missing source image")
                    return False
                wrapper = BaseImageProcessor(file_path)
            wrapper.lock = True
            if self._target_data_base:
                wrapper.target_database = self._target_data_base

            wrapper.store_image(
                image=wrapper.current_image, text="true_source_image", force_store=True
            )

            # Pre process image
            use_last_result, current_step = self.pre_process_image(
                wrapper=wrapper,
                use_last_result=True,
                progress_callback=progress_callback,
                current_step=current_step,
                total_steps=total_steps,
            )

            # Build coarse mask
            if len(tools_[ToolFamily.THRESHOLD]) > 0:
                mask_list = []
                mask_names = []
                masks_failed_cpt = 0
                for i, tool in enumerate(tools_[ToolFamily.THRESHOLD]):
                    target = tool["tool"].get_value_of("tool_target")
                    if target not in [None, "", "none"]:
                        continue
                    mask, use_last_result = self.process_tool(
                        tool_dict=tool, wrapper=wrapper, use_last_result=use_last_result
                    )
                    if mask is not None:
                        mask_list.append(mask)
                        mask_names.append(tool["tool"].short_desc())
                    else:
                        self.last_error.add_error(
                            new_error_text=f'Failed to process {tool["tool"].name}',
                            new_error_kind="pipeline_process_error",
                            target_logger=logger,
                        )
                        masks_failed_cpt += 1
                    current_step = self.add_progress(
                        progress_callback,
                        current_step,
                        total_steps,
                        f"Building coarse masks, failed {masks_failed_cpt}"
                        if masks_failed_cpt != 0
                        else "Building coarse masks",
                        wrapper if mask is not None else None,
                    )

                for img_data, img_name in zip(mask_list, mask_names):
                    wrapper.store_image(img_data, img_name)

                func = getattr(wrapper, self.merge_method, None)
                if func:
                    wrapper.mask = func([mask for mask in mask_list if mask is not None])
                    wrapper.store_image(image=wrapper.mask, text="coarse_mask")
                else:
                    logger.error("Unable to merge coarse masks")
                    self.last_error.add_error(
                        new_error_text="Unable to merge coarse masks",
                        new_error_kind="pipeline_process_error",
                        target_logger=logger,
                    )
                    res = False
                    return
                current_step = self.add_progress(
                    progress_callback,
                    current_step,
                    total_steps,
                    "Merged coarse masks",
                    wrapper if func is not None else None,
                )

                # ROIs to be applied after mask merging
                handled_rois = ["keep", "delete", "erode", "dilate", "open", "close"]
                rois_list = [
                    roi
                    for roi in wrapper.rois_list
                    if roi.tag in handled_rois
                    and not (roi.target and roi.target != "none")
                ]
                wrapper.store_image(
                    wrapper.retrieve_stored_image("mask_on_exp_fixed_bw_roi"),
                    text="used_rois",
                )
                wrapper.mask = wrapper.apply_roi_list(
                    img=wrapper.mask, rois=rois_list, print_dbg=self.display_images
                )
                current_step = self.add_progress(
                    progress_callback,
                    current_step,
                    total_steps,
                    "Applied ROIs",
                    wrapper,
                )

                # Clean mask
                if len(tools_[ToolFamily.MASK_CLEANUP]) > 0:
                    res = True
                    for tool in tools_[ToolFamily.MASK_CLEANUP]:
                        tmp_mask, use_last_result = self.process_tool(
                            tool_dict=tool,
                            wrapper=wrapper,
                            use_last_result=use_last_result,
                        )
                        if tmp_mask is None:
                            res = False
                            self.last_error.add_error(
                                new_error_text=f'Failed to process {tool["tool"].name}',
                                new_error_kind="pipeline_process_error",
                                target_logger=logger,
                            )
                        else:
                            wrapper.mask = tmp_mask
                            res = res and True
                        current_step = self.add_progress(
                            progress_callback,
                            current_step,
                            total_steps,
                            "Cleaning mask",
                            wrapper,
                        )
                else:
                    res = True
                wrapper.store_image(image=wrapper.mask, text="clean_mask")

                # Check that the mask is where it belongs
                if res:
                    enforcers_list = wrapper.get_rois({"enforce"})
                    if len(enforcers_list) > 0:
                        for i, enforcer in enumerate(enforcers_list):
                            mask = wrapper.mask.copy()
                            mask = enforcer.keep(mask)
                            partial_ok = np.count_nonzero(mask) > 0
                            res = partial_ok and res
                            if partial_ok:
                                roi_img = np.dstack(
                                    (np.zeros_like(mask), mask, np.zeros_like(mask))
                                )
                            else:
                                roi_img = np.dstack(
                                    (np.zeros_like(mask), np.zeros_like(mask), mask)
                                )
                            background_img = cv2.bitwise_and(
                                wrapper.mask, wrapper.mask, mask=255 - mask
                            )
                            img = cv2.bitwise_or(
                                roi_img,
                                np.dstack(
                                    (background_img, background_img, background_img)
                                ),
                            )
                            enforcer.draw_to(img, line_width=4)
                            wrapper.store_image(img, f"enforcer_{i}_{enforcer.name}")
                        wrapper.store_image(
                            image=wrapper.draw_rois(
                                img=wrapper.retrieve_stored_image("mask_on_exp_fixed_bw"),
                                rois=enforcers_list,
                            ),
                            text="enforcer_rois",
                        )
                        fifth_image = "enforcer_rois"
                    else:
                        wrapper.store_image(
                            image=wrapper.retrieve_stored_image("exp_fixed_pseudo_on_bw"),
                            text="exp_fixed_pseudo_on_bw",
                        )
                        fifth_image = "exp_fixed_pseudo_on_bw"

                if res and wrapper.mask is not None:
                    wrapper.store_image(
                        wrapper.retrieve_stored_image("mask_on_exp_fixed_bw"),
                        text="mask_on_bw",
                    )
                current_step = self.add_progress(
                    progress_callback,
                    current_step,
                    total_steps,
                    "Checked mask enforcers",
                    wrapper,
                )
            else:
                handled_rois = ["keep", "delete"]
                rois_list = [
                    roi
                    for roi in wrapper.rois_list
                    if roi.tag in handled_rois
                    and not (roi.target and roi.target != "none")
                ]
                wrapper.store_image(
                    image=wrapper.draw_rois(
                        img=wrapper.retrieve_stored_image("exposure_fixed"),
                        rois=rois_list,
                    ),
                    text="used_rois",
                )
                wrapper.current_image = wrapper.apply_roi_list(
                    img=wrapper.current_image,
                    rois=rois_list,
                    print_dbg=self.display_images,
                )
                current_step = self.add_progress(
                    progress_callback,
                    current_step,
                    total_steps,
                    "Applied ROIs",
                    wrapper,
                )
                res = True

            # Prepare data holder
            if res and (
                (
                    not self.threshold_only
                    and len(tools_[ToolFamily.FEATURE_EXTRACTION]) > 0
                )
                or (len(tools_[ToolFamily.IMAGE_GENERATOR]) > 0)
            ):
                wrapper.csv_data_holder = AbstractCsvWriter()

            if save_mask and self.image_output_path and wrapper.mask is not None:
                force_directories(os.path.join(self.image_output_path, "masks"))
                cv2.imwrite(
                    filename=os.path.join(
                        self.image_output_path, "masks", wrapper.file_name
                    ),
                    img=wrapper.mask,
                )

            # Extract features
            if (
                res
                and not self.threshold_only
                and len(tools_[ToolFamily.FEATURE_EXTRACTION]) > 0
            ):
                wrapper.current_image = wrapper.retrieve_stored_image("exposure_fixed")
                for tool in tools_[ToolFamily.FEATURE_EXTRACTION]:
                    current_data, use_last_result = self.process_tool(
                        tool_dict=tool, wrapper=wrapper, use_last_result=use_last_result
                    )
                    if isinstance(current_data, dict):
                        wrapper.csv_data_holder.data_list.update(current_data)
                    else:
                        self.last_error.add_error(
                            new_error_text=f'{tool["tool"].name} failed to extract features',
                            new_error_kind="pipeline_process_error",
                            target_logger=logger,
                        )
                    current_step = self.add_progress(
                        progress_callback,
                        current_step,
                        total_steps,
                        "Extracting features",
                        wrapper,
                    )
                res = len(wrapper.csv_data_holder.data_list) > 0

            # Generate images
            if res and len(tools_[ToolFamily.IMAGE_GENERATOR]) > 0:
                for tool in tools_[ToolFamily.IMAGE_GENERATOR]:
                    current_data, use_last_result = self.process_tool(
                        tool_dict=tool,
                        wrapper=wrapper,
                        use_last_result=use_last_result,
                    )
                    if isinstance(current_data, dict):
                        wrapper.csv_data_holder.data_list.update(current_data)
                    else:
                        self.last_error.add_error(
                            new_error_text=f'{tool["tool"].name} failed to generate images',
                            new_error_kind="pipeline_process_error",
                            target_logger=logger,
                        )
                    current_step = self.add_progress(
                        progress_callback,
                        current_step,
                        total_steps,
                        "Copying images",
                        wrapper,
                    )
                res = len(wrapper.csv_data_holder.data_list) > 0

            # Set last image to be displayed
            if self.last_image:
                last_image = wrapper.retrieve_stored_image(self.last_image)
                if last_image is not None:
                    wrapper.store_image(image=last_image, text="last_" + self.last_image)

            if self.build_mosaic:
                old_mosaic = wrapper.store_mosaic
                wrapper.store_mosaic = "result"
                if wrapper.mask is not None:
                    wrapper.mosaic_data = np.array(
                        [
                            line.split(",")
                            for line in self.mosaic_items.replace(" ", "").split("\n")
                        ]
                    )
                else:
                    wrapper.mosaic_data = np.array(
                        ["source", "exposure_fixed", "current_image"]
                    )
                wrapper.print_mosaic(padding=4)
                wrapper.store_mosaic = old_mosaic
            else:
                res = True

            current_step = self.add_progress(
                progress_callback, total_steps, total_steps, "Done", wrapper
            )
        except Exception as e:
            logger.error(f'Unexpected failure: "{repr(e)}"')
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
            map(
                lambda x: f"import {x}",
                ["argparse", "csv", "cv2", "numpy as np", "os", "sys"],
            )
        )
        # Add paths
        import_lst.extend(
            [
                "",
                "abspath = os.path.abspath(__file__)",
                "fld_name = os.path.dirname(abspath)",
                "sys.path.insert(0, fld_name)",
                "sys.path.insert(0, os.path.dirname(fld_name))",
                "",
            ]
        )
        # IPSO Phen libraries
        import_lst.extend(
            [
                "from ipso_phen.ipapi.base.ip_abstract import BaseImageProcessor",
                "from ipso_phen.ipapi.base.ipt_functional import call_ipt, call_ipt_func",
                "from ipso_phen.ipapi.tools.csv_writer import AbstractCsvWriter",
            ]
        )

        return import_lst

    def code_body(self, root_white_spaces: str = "    "):
        def add_tab(tab_str):
            return tab_str + "    "

        def remove_tab(tab_str):
            return tab_str[: len(tab_str) - 4]

        tools_ = self.group_tools(tool_only=True, conditions=dict(enabled=True))

        code_ = "def main():\n"
        ws_ct = root_white_spaces

        # Get file name
        # _____________
        code_ += ws_ct + "# Get the file\n" + ws_ct + "# ____________\n"
        # Set working folder
        code_ += ws_ct + "# Set working folder\n"
        code_ += ws_ct + "old_wd = os.getcwd()\n"
        code_ += ws_ct + "abspath = os.path.abspath(__file__)\n"
        code_ += ws_ct + "fld_name = os.path.dirname(abspath)\n"
        code_ += ws_ct + "os.chdir(fld_name)\n\n"
        code_ += f"{ws_ct}# Construct the argument parser and parse the arguments\n"
        code_ += f"{ws_ct}ap = argparse.ArgumentParser()\n"
        code_ += f'{ws_ct}ap.add_argument("-i", "--image", required=True, help="Path to the image")\n'
        code_ += f'{ws_ct}ap.add_argument("-d", "--destination", required=False, help="Destination folder")\n'
        code_ += f'{ws_ct}ap.add_argument("-p", "--print_images", required=False, help="Print images, y or n")\n'
        code_ += f'{ws_ct}ap.add_argument("-m", "--print_mosaic", required=False, help="Print mosaic, y or n")\n'
        code_ += f"{ws_ct}args = vars(ap.parse_args())\n"
        code_ += f'{ws_ct}file_name = args["image"]\n'
        code_ += f'{ws_ct}print_images = args.get("print_images", "n") == "y"\n'
        code_ += f'{ws_ct}print_mosaic = args.get("print_mosaic", "n") == "y"\n'
        code_ += f'{ws_ct}dst_folder = args.get("destination", "")\n\n'
        code_ += ws_ct + "# Restore working folder\n"
        code_ += ws_ct + "os.chdir(old_wd)\n\n"

        code_ += f"{ws_ct}# Build wrapper\n"
        code_ += f"{ws_ct}# _____________\n"
        code_ += ws_ct + "wrapper = BaseImageProcessor(file_name)\n"
        code_ += ws_ct + "wrapper.lock = True\n"
        code_ += (
            ws_ct + "wrapper.store_image(wrapper.current_image, 'true_source_image')\n"
        )
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
        code_ += "\n"

        # Build ROIs using fixed image
        # _________________
        if len(tools_[ToolFamily.ROI_RAW_IMAGE_STR]) > 0:
            code_ += (
                ws_ct
                + "# Build ROIs using fixed image\n"
                + ws_ct
                + "# _________________\n"
            )
            for ef_tool in tools_[ToolFamily.ROI_RAW_IMAGE_STR]:
                code_ += call_ipt_func_code(
                    ipt=ef_tool,
                    function_name="generate_roi",
                    white_spaces=ws_ct,
                    result_name="roi",
                    generate_imports=False,
                )
                code_ += ws_ct + "if roi is not None:\n"
                ws_ct = add_tab(ws_ct)
                code_ += ws_ct + "wrapper.add_roi(new_roi=roi)\n"
                ws_ct = remove_tab(ws_ct)
                code_ += "\n"

        # Fix image exposition
        # ____________________
        if len(tools_[ToolFamily.EXPOSURE_FIXING]) > 0:
            code_ += ws_ct + "# Fix exposure\n" + ws_ct + "# ____________________\n"
            for ef_tool in tools_[ToolFamily.EXPOSURE_FIXING]:
                code_ += call_ipt_code(
                    ipt=ef_tool,
                    white_spaces=ws_ct,
                    result_name="wrapper.current_image",
                    generate_imports=False,
                )
                code_ += "\n"
            code_ += f"{ws_ct}# Store image name for analysis\n"
            code_ += (
                ws_ct + 'wrapper.store_image(wrapper.current_image, "exposure_fixed")\n'
            )
            code_ += ws_ct + 'analysis_image = "exposure_fixed"\n'
            code_ += "\n"
        else:
            code_ += f"{ws_ct}# Set default name for image analysis"
            code_ += ws_ct + "# No exposure fix needed\n"
            code_ += ws_ct + "analysis_image = NONE\n"
            code_ += "\n"
        code_ += ws_ct + "if print_mosaic:\n"
        ws_ct = add_tab(ws_ct)
        code_ += ws_ct + 'wrapper.store_image(wrapper.current_image, "fixed_source")\n'
        ws_ct = remove_tab(ws_ct)

        # Pre process image (make segmentation easier)
        # ____________________________________________
        if len(tools_[ToolFamily.PRE_PROCESSING]) > 0:
            code_ += (
                ws_ct
                + "# Pre process image (make segmentation easier)\n"
                + ws_ct
                + "# ____________________________________________\n"
            )
            for ef_tool in tools_[ToolFamily.PRE_PROCESSING]:
                code_ += call_ipt_code(
                    ipt=ef_tool,
                    white_spaces=ws_ct,
                    result_name="wrapper.current_image",
                    generate_imports=False,
                )
                code_ += "\n"
            code_ += ws_ct + "if print_mosaic:\n"
            ws_ct = add_tab(ws_ct)
            code_ += (
                ws_ct
                + 'wrapper.store_image(wrapper.current_image, "pre_processed_image")\n'
            )
            ws_ct = remove_tab(ws_ct)

        # Build ROIs using preprocessed image
        # __________________
        if len(tools_[ToolFamily.ROI_PP_IMAGE_STR]) > 0:
            code_ += ws_ct + "# Build dynamic ROIs\n" + ws_ct + "# __________________\n"
            for ef_tool in tools_[ToolFamily.ROI_PP_IMAGE_STR]:
                code_ += call_ipt_func_code(
                    ipt=ef_tool,
                    function_name="generate_roi",
                    white_spaces=ws_ct,
                    result_name="roi",
                    generate_imports=False,
                )
                code_ += ws_ct + "if roi is not None:\n"
                ws_ct = add_tab(ws_ct)
                code_ += ws_ct + "wrapper.add_roi(new_roi=roi)\n"
                ws_ct = remove_tab(ws_ct)
                code_ += "\n"

        # Build coarse masks
        # __________________
        if len(tools_[ToolFamily.THRESHOLD]) > 0:
            code_ += ws_ct + "# Build coarse masks\n" + ws_ct + "# __________________\n"
            code_ += ws_ct + "mask_list = []\n"
            for mask_tool in tools_[ToolFamily.THRESHOLD]:
                code_ += call_ipt_code(
                    ipt=mask_tool,
                    white_spaces=ws_ct,
                    result_name="current_mask_",
                    generate_imports=False,
                )
                code_ += ws_ct + "mask_list.append(current_mask_)\n"
                code_ += "\n"
            code_ += ws_ct + "# Merge masks\n"
            code_ += f'{ws_ct}func = getattr(wrapper, "{self.merge_method}", None)\n'
            code_ += f"{ws_ct}if func:\n"
            ws_ct = add_tab(ws_ct)
            code_ += (
                ws_ct
                + "wrapper.mask = func([mask for mask in mask_list if mask is not None])\n"
            )
            code_ += (
                ws_ct
                + f'wrapper.store_image(wrapper.mask, f"mask_{self.merge_method}")\n'
            )
            code_ += ws_ct + "if print_mosaic:\n"
            ws_ct = add_tab(ws_ct)
            code_ += ws_ct + 'wrapper.store_image(wrapper.mask, "coarse_mask")\n'
            ws_ct = remove_tab(ws_ct)
            ws_ct = remove_tab(ws_ct)
            code_ += ws_ct + "else:\n"
            ws_ct = add_tab(ws_ct)
            code_ += (
                ws_ct
                + 'wrapper.error_holder.add_error("Unable to merge coarse masks", target_logger=logger)\n'
            )
            code_ += ws_ct + "return\n"
            ws_ct = remove_tab(ws_ct)
            code_ += "\n"

        # ROIs to be applied after mask merging
        # _____________________________________
        code_ += (
            ws_ct
            + "# ROIs to be applied after mask merging\n"
            + ws_ct
            + "# _____________________________________\n"
        )
        code_ += (
            ws_ct
            + "handled_rois = ['keep', 'delete', 'erode', 'dilate', 'open', 'close']\n"
        )
        code_ += (
            ws_ct
            + "rois_list = [roi for roi in wrapper.rois_list if roi.tag in handled_rois and not (roi.target and roi.target != 'none')]\n"
        )
        code_ += (
            ws_ct
            + f"wrapper.mask = wrapper.apply_roi_list(img=wrapper.mask, rois=rois_list, print_dbg={self.display_images})\n"
        )
        code_ += ws_ct + "if print_mosaic:\n"
        ws_ct = add_tab(ws_ct)
        code_ += ws_ct + 'wrapper.store_image(wrapper.mask, "mask_after_roi")\n'
        ws_ct = remove_tab(ws_ct)
        code_ += "\n"

        # Clean mask
        # __________
        if len(tools_[ToolFamily.MASK_CLEANUP]) > 0:
            code_ += ws_ct + "# Clean merged mask\n" + ws_ct + "# _________________\n"
            for mc_tool in tools_[ToolFamily.MASK_CLEANUP]:
                code_ += call_ipt_code(
                    ipt=mc_tool,
                    white_spaces=ws_ct,
                    result_name="wrapper.mask",
                    generate_imports=False,
                )
                code_ += f"{ws_ct}if wrapper.mask is None:\n"
                ws_ct = add_tab(ws_ct)
                code_ += ws_ct + "return\n"
                ws_ct = remove_tab(ws_ct)
                code_ += "\n"
            code_ += ws_ct + "if print_mosaic:\n"
            ws_ct = add_tab(ws_ct)
            code_ += ws_ct + 'wrapper.store_image(wrapper.mask, "clean_mask")\n'
            ws_ct = remove_tab(ws_ct)
            code_ += "\n"

        # Check that the mask is where it belongs
        # _______________________________________
        code_ += (
            ws_ct
            + "# Check that the mask is where it belongs\n"
            + ws_ct
            + "# _______________________________________\n"
        )
        code_ += ws_ct + "if print_images:\n"
        ws_ct = add_tab(ws_ct)
        code_ += ws_ct + "res = True\n"
        code_ += ws_ct + 'enforcers_list = wrapper.get_rois({"enforce"})\n'
        code_ += ws_ct + "for i, enforcer in enumerate(enforcers_list):\n"
        ws_ct = add_tab(ws_ct)
        code_ += ws_ct + "mask = wrapper.mask.copy()\n"
        code_ += ws_ct + "mask = enforcer.keep(mask))\n"
        code_ += ws_ct + "partial_ok = np.count_nonzero(mask) > 0\n"
        code_ += ws_ct + "res = partial_ok and res\n"
        code_ += ws_ct + "if partial_ok:\n"
        ws_ct = add_tab(ws_ct)
        code_ += (
            ws_ct
            + "roi_img = np.dstack((np.zeros_like(mask), mask, np.zeros_like(mask)))\n"
        )
        ws_ct = remove_tab(ws_ct)
        code_ += ws_ct + "else:\n"
        ws_ct = add_tab(ws_ct)
        code_ += (
            ws_ct
            + "roi_img = np.dstack((np.zeros_like(mask), np.zeros_like(mask), mask))\n"
        )
        ws_ct = remove_tab(ws_ct)
        code_ += (
            ws_ct
            + "background_img = cv2.bitwise_and(wrapper.mask, wrapper.mask, mask=255 - mask)\n"
        )
        code_ += (
            ws_ct
            + "img = cv2.bitwise_or(roi_img, np.dstack((background_img, background_img, background_img)))\n"
        )
        code_ += ws_ct + "enforcer.draw_to(img, line_width=4)\n"
        code_ += ws_ct + "wrapper.store_image(img, f'enforcer_{i}_{enforcer.name}')\n"
        ws_ct = remove_tab(ws_ct)
        code_ += ws_ct + "if not res:\n"
        ws_ct = add_tab(ws_ct)
        code_ += ws_ct + "return\n"
        ws_ct = remove_tab(ws_ct)
        ws_ct = remove_tab(ws_ct)
        code_ += ws_ct + "else:\n"
        ws_ct = add_tab(ws_ct)
        code_ += ws_ct + 'enforcers_list = wrapper.get_rois({"enforce"})\n'
        code_ += ws_ct + "for i, enforcer in enumerate(enforcers_list):\n"
        ws_ct = add_tab(ws_ct)
        code_ += ws_ct + "mask = wrapper.mask.copy()\n"
        code_ += ws_ct + "mask = wrapper.keep_roi(mask, enforcer)\n"
        code_ += ws_ct + "if np.count_nonzero(mask) == 0:\n"
        ws_ct = add_tab(ws_ct)
        code_ += ws_ct + "return\n"
        ws_ct = remove_tab(ws_ct)
        ws_ct = remove_tab(ws_ct)
        ws_ct = remove_tab(ws_ct)
        code_ += "\n"

        # Prepare data holder
        # ___________________
        if (
            not self.threshold_only and len(tools_[ToolFamily.FEATURE_EXTRACTION]) > 0
        ) or (len(tools_[ToolFamily.IMAGE_GENERATOR]) > 0):
            code_ += ws_ct + "# Prepare data holder\n"
            code_ += ws_ct + "# ___________________\n"
            code_ += ws_ct + "wrapper.csv_data_holder = AbstractCsvWriter()\n"

        # Extract features
        # ________________
        if not self.threshold_only and (len(tools_[ToolFamily.FEATURE_EXTRACTION]) > 0):
            code_ += ws_ct + "# Extract features\n"
            code_ += ws_ct + "# ________________\n"
            code_ += (
                ws_ct
                + "wrapper.current_image = wrapper.retrieve_stored_image('exposure_fixed')\n"
            )
            for fe_tool in tools_[ToolFamily.FEATURE_EXTRACTION]:
                code_ += call_ipt_code(
                    ipt=fe_tool,
                    white_spaces=ws_ct,
                    result_name="current_data",
                    generate_imports=False,
                    return_type="data",
                )
                code_ += f"{ws_ct}if isinstance(current_data, dict):\n"
                ws_ct = add_tab(ws_ct)
                code_ += (
                    ws_ct + "wrapper.csv_data_holder.data_list.update(current_data)\n"
                )
                ws_ct = remove_tab(ws_ct)
                code_ += ws_ct + "else:\n"
                ws_ct = add_tab(ws_ct)
                code_ += (
                    ws_ct
                    + 'wrapper.error_holder.add_error("Failed to add extracted data", target_logger=logger)\n'
                )
                ws_ct = remove_tab(ws_ct)
                code_ += "\n"
            code_ += ws_ct + "# Save CSV\n"
            code_ += (
                ws_ct
                + "if dst_folder and (len(wrapper.csv_data_holder.data_list) > 0):\n"
            )
            ws_ct = add_tab(ws_ct)
            code_ += (
                ws_ct
                + "with open(os.path.join(dst_folder, '', wrapper.file_handler.file_name_no_ext + '.csv'), 'w', newline='') as csv_file_:\n"
            )
            ws_ct = add_tab(ws_ct)
            code_ += ws_ct + "wr = csv.writer(csv_file_, quoting=csv.QUOTE_NONE)\n"
            code_ += ws_ct + "wr.writerow(wrapper.csv_data_holder.header_to_list())\n"
            code_ += ws_ct + "wr.writerow(wrapper.csv_data_holder.data_to_list())\n"
            ws_ct = remove_tab(ws_ct)
            ws_ct = remove_tab(ws_ct)
        else:
            code_ += ws_ct + "# Print selection as color on bw background\n"
            code_ += ws_ct + "# ____________________________________________\n"
            code_ += (
                ws_ct
                + "id_objects, obj_hierarchy = cv2.findContours(wrapper.mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)[-2:]\n"
            )
            code_ += (
                ws_ct
                + "wrapper.object_composition(wrapper.current_image, id_objects, obj_hierarchy)\n"
            )
        code_ += "\n"

        # Generate images
        if len(tools_[ToolFamily.IMAGE_GENERATOR]) > 0:
            code_ += ws_ct + "# Generate images\n"
            code_ += ws_ct + "# _______________\n"
            for ig_tool in tools_[ToolFamily.IMAGE_GENERATOR]:
                ig_tool.set_value_of(key="path", value=self.image_output_path)
                code_ += call_ipt_code(
                    ipt=ig_tool,
                    white_spaces=ws_ct,
                    result_name="current_data",
                    generate_imports=False,
                    return_type="data",
                )
                code_ += f"{ws_ct}if isinstance(current_data, dict):\n"
                ws_ct = add_tab(ws_ct)
                code_ += (
                    ws_ct + "wrapper.csv_data_holder.data_list.update(current_data)\n"
                )
                ws_ct = remove_tab(ws_ct)
                code_ += ws_ct + "else:\n"
                ws_ct = add_tab(ws_ct)
                code_ += (
                    ws_ct
                    + 'wrapper.error_holder.add_error("Failed to add generate image", target_logger=logger)\n'
                )
                ws_ct = remove_tab(ws_ct)
                code_ += "\n"

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
        code_ += ws_ct + "wrapper.print_mosaic(padding=(4)\n"
        ws_ct = remove_tab(ws_ct)
        code_ += "\n"

        code_ += f'{ws_ct}print("Done.")'

        return code_

    @staticmethod
    def code_footer():
        code_ = 'if __name__ == "__main__":\n'
        code_ += "    main()\n"
        return code_

    def reset(self):
        self.ip_operators = []
        self._settings.reset(is_update_widgets=True)

    def code(self):
        return (
            "\n".join(self.code_imports())
            + "\n\n\n"
            + self.code_body()
            + "\n\n\n"
            + self.code_footer()
        )

    def add_operator(self, operator, kind: str, enabled_state: bool = True):
        self.ip_operators.append(
            dict(
                tool=operator,
                enabled=enabled_state,
                kind=kind,
                uuid=str(uuid4()),
                last_result=None,
            )
        )

    def delete_operators(self, constraints: dict):
        i = 0
        while i < len(self.ip_operators):
            current_op = self.ip_operators[i]
            if self.op_matches(current_op, constraints=constraints):
                op_to_delete = self.ip_operators.pop(self.ip_operators.index(current_op))
                self.delete_cache_if_tool_after(op_to_delete["kind"])
                for p in op_to_delete["tool"].gizmos:
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
        constraints = {k: v for k, v in constraints.items() if v is not None}
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
            self.ip_operators[i], self.ip_operators[j] = (
                self.ip_operators[j],
                self.ip_operators[i],
            )

    def get_something(self, key: str):
        """
        Return either an operator or a feature, priority is given to operators
        :param key: uuid of operator or name of feature
        """
        tool = self.get_operators(constraints=dict(uuid=key))
        if len(tool) > 0:
            return tool[0]
        return None

    @staticmethod
    def ops_after(tool_kind: str):
        if tool_kind in [ToolFamily.ROI_RAW_IMAGE_STR]:
            return [
                ToolFamily.WHITE_BALANCE,
                ToolFamily.EXPOSURE_FIXING,
                ToolFamily.ROI_RAW_IMAGE_STR,
                ToolFamily.PRE_PROCESSING,
                ToolFamily.ROI_PP_IMAGE_STR,
                ToolFamily.THRESHOLD,
                ToolFamily.MASK_CLEANUP,
                ToolFamily.FEATURE_EXTRACTION,
                ToolFamily.IMAGE_GENERATOR,
            ]
        if tool_kind in [ToolFamily.EXPOSURE_FIXING, ToolFamily.WHITE_BALANCE]:
            return [
                ToolFamily.WHITE_BALANCE,
                ToolFamily.EXPOSURE_FIXING,
                ToolFamily.PRE_PROCESSING,
                ToolFamily.ROI_PP_IMAGE_STR,
                ToolFamily.THRESHOLD,
                ToolFamily.MASK_CLEANUP,
                ToolFamily.FEATURE_EXTRACTION,
                ToolFamily.IMAGE_GENERATOR,
            ]
        if tool_kind in [ToolFamily.PRE_PROCESSING]:
            return [
                ToolFamily.PRE_PROCESSING,
                ToolFamily.ROI_PP_IMAGE_STR,
                ToolFamily.THRESHOLD,
                ToolFamily.MASK_CLEANUP,
                ToolFamily.FEATURE_EXTRACTION,
                ToolFamily.IMAGE_GENERATOR,
            ]
        if tool_kind in [ToolFamily.ROI_PP_IMAGE_STR]:
            return [
                ToolFamily.ROI_PP_IMAGE_STR,
                ToolFamily.THRESHOLD,
                ToolFamily.MASK_CLEANUP,
                ToolFamily.FEATURE_EXTRACTION,
                ToolFamily.IMAGE_GENERATOR,
            ]
        elif tool_kind == ToolFamily.THRESHOLD:
            return [
                ToolFamily.THRESHOLD,
                ToolFamily.MASK_CLEANUP,
                ToolFamily.FEATURE_EXTRACTION,
                ToolFamily.IMAGE_GENERATOR,
            ]
        elif tool_kind == ToolFamily.MASK_CLEANUP:
            return [
                ToolFamily.MASK_CLEANUP,
                ToolFamily.FEATURE_EXTRACTION,
                ToolFamily.IMAGE_GENERATOR,
            ]
        elif tool_kind == ToolFamily.FEATURE_EXTRACTION:
            return [
                ToolFamily.FEATURE_EXTRACTION,
                ToolFamily.IMAGE_GENERATOR,
            ]
        elif tool_kind == ToolFamily.IMAGE_GENERATOR:
            return [ToolFamily.IMAGE_GENERATOR]
        else:
            return []

    def delete_cache_if_tool_after(self, tool_kind: Union[str, None] = None):
        for tool_dict in self.get_operators(
            constraints=dict(kind=self.ops_after(tool_kind))
        ):
            tool_dict["last_result"] = None

    def toggle_enabled_state(self, key: str) -> None:
        """
        Toggles enabled of matching key
        :param key: uuid for tools, name for settings
        """
        if not key:
            return
        tool = self.get_operators(constraints=dict(uuid=key))
        if len(tool) == 1:
            tool[0]["enabled"] = not tool[0]["enabled"]
            self.delete_cache_if_tool_after(tool[0]["kind"])

    def invalidate(self, key: Union[str, None] = None):
        if key is not None:
            tool = self.get_operators(constraints=dict(uuid=key))
            if len(tool) > 0:
                self.delete_cache_if_tool_after(tool[0]["kind"])
        else:
            self.delete_cache_if_tool_after()

    @property
    def is_empty(self):
        return len(self.get_operators(dict(enabled=True))) == 0

    @property
    def is_functional(self):
        return len(self.get_operators(dict(kind=ToolFamily.THRESHOLD, enabled=True))) > 0

    @property
    def target_data_base(self):
        return self._target_data_base

    @target_data_base.setter
    def target_data_base(self, value):
        self._target_data_base = value

    @property
    def desc_merge_method(self):
        if self.merge_method == "multi_and":
            return "Partial masks will be merged with a logical AND"
        elif self.merge_method == "multi_or":
            return "Partial masks will be merged with a logical OR"
        else:
            return "Unknown mask merge method"

    @property
    def desc_display_images(self):
        return f"Display step images at the end: {self.display_images}"

    @property
    def settings(self):
        return self._settings

    @settings.setter
    def settings(self, value):
        self._settings = value

    @property
    def merge_method(self):
        tmp = self._settings.get_value_of("merge_method")
        if tmp == "l_and":
            self._settings.set_value_of("merge_method", "multi_and")
        elif tmp == "l_or":
            self._settings.set_value_of("merge_method", "multi_or")
        return self._settings.get_value_of("merge_method")

    @property
    def display_images(self):
        return self._settings.get_value_of("display_images") == 1

    @display_images.setter
    def display_images(self, value):
        self._settings.set_value_of(
            key="display_images", value=1 if value is True else 0, update_widgets=False
        )

    @property
    def threshold_only(self):
        return self._settings.get_value_of("threshold_only") == 1

    @threshold_only.setter
    def threshold_only(self, value):
        self._settings.set_value_of(
            key="threshold_only", value=1 if value is True else 0, update_widgets=False
        )

    @property
    def build_mosaic(self):
        return self._settings.get_value_of("build_mosaic") == 1

    @build_mosaic.setter
    def build_mosaic(self, value):
        self._settings.set_value_of(
            key="build_mosaic", value=1 if value is True else 0, update_widgets=False
        )

    @property
    def bound_position(self):
        return self._settings.get_value_of("bound_level")

    @property
    def pseudo_color_map(self):
        color_map = self._settings.get_value_of("color_map")
        _, color_map = color_map.split("_")
        return int(color_map)

    @property
    def pseudo_color_channel(self):
        return self._settings.get_value_of("pseudo_channel")

    @property
    def image_output_path(self):
        return self._settings.get_value_of("image_output_path")

    @image_output_path.setter
    def image_output_path(self, value):
        self._settings.set_value_of("image_output_path", value)

    @property
    def last_image(self):
        return self._settings.get_value_of("last_image")

    @last_image.setter
    def last_image(self, value):
        self._settings.set_value_of("last_image", value)

    @property
    def mosaic_items(self):
        return self._settings.get_value_of("mosaic_items")

    @mosaic_items.setter
    def mosaic_items(self, value):
        self._settings.set_value_of("mosaic_items", value)

    @property
    def pseudo_background_type(self):
        return self._settings.get_value_of("pseudo_background_type")

    @property
    def use_default_script(self):
        return self._settings.get_value_of("use_default_script")

    @property
    def ip_operators(self):
        return self._ip_operators

    @ip_operators.setter
    def ip_operators(self, value):
        self._ip_operators = value

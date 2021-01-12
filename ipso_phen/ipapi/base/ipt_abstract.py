import inspect
import sys
import itertools
import random
from abc import ABC, abstractproperty
from distutils.version import LooseVersion
import base64
import hashlib
import logging
import os
from typing import Union

import cv2
import numpy as np

from ipso_phen.ipapi.base.ip_abstract import BaseImageProcessor
from ipso_phen.ipapi.tools.common_functions import make_safe_name
import ipso_phen.ipapi.base.ip_common as ipc
from ipso_phen.ipapi.tools.common_functions import force_directories

CLASS_NAME_KEY = "class__name__"
MODULE_NAME_KEY = "module__name__"
PARAMS_NAME_KEY = "params"
GRID_SEARCH_PARAMS_NAME_KEY = "grid_search_params"

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))


class IptParam(object):
    def __init__(self, **kwargs):
        self.name = kwargs.get("name", "no_name")
        self.desc = kwargs.get("desc", "no desc")
        self.default_value = kwargs.get("default_value", "no default")
        self.allowed_values = kwargs.get("allowed_values", None)
        if self.allowed_values is not None and isinstance(self.allowed_values, list):
            self.allowed_values = tuple(self.allowed_values)
        self.hint = kwargs.get("hint", "no clue")
        self.widget_type = kwargs.get("widget_type", "unk_wt")
        self.kind = kwargs.get("kind", "unk_k")
        self.options = kwargs.get("options", {})
        self._value = kwargs.get("_value", self.default_value)
        self.on_change = None
        self._widgets = {}
        self._grid_search_options = kwargs.get(
            "_grid_search_options", str(self.default_value)
        )
        self.grid_search_mode = False

        self.ui_update_callbacks = {}

    def __str__(self):
        return f"[{self.name}:{self.value}]"

    def __repr__(self):
        return (
            f"{repr(self.name)}_"
            f"{repr(self.desc)}_"
            f"{repr(self.default_value)}_"
            f"{repr(self.allowed_values)}_"
            f"{repr(self.value)}"
        )

    def __eq__(self, other):
        return self.name == other.name

    def __ne__(self, other):
        return self.name != other.name

    def __copy__(self):
        new = type(self)(
            name=self.name,
            desc=self.desc,
            default_value=self.default_value,
            allowed_values=self.allowed_values,
            hint=self.hint,
            widget_type=self.widget_type,
            kind=self.kind,
            options=self.options,
        )
        return new

    def clear_widgets(self):
        self._widgets = {}

    def update_ui(self, callback: str, **kwargs):
        callback = self.ui_update_callbacks.get(callback, None)
        if callback is None:
            return
        callback(**kwargs)

    def init(self, tool_name, label, widget, grid_search_mode: bool = False, **kwargs):
        self.ui_update_callbacks = dict(**kwargs)

        self.update_ui(
            callback="set_name",
            widget=widget,
            new_name=f"ipt_param_{tool_name}_{self.name}",
        )
        self.update_ui(
            callback="set_name",
            widget=label,
            new_name=f"ipt_param_label_{tool_name}_{self.name}",
        )

        self.label = label
        self.update_label()
        self.grid_search_mode = grid_search_mode
        if self.is_input:
            self.input = widget
            if widget is None:
                return False
            elif grid_search_mode:
                self.update_ui(
                    callback="set_text",
                    widget=self.gs_input,
                    text=self.grid_search_options,
                )
            elif isinstance(self.allowed_values, dict):
                self.update_ui(
                    callback="add_items",
                    widget=widget,
                    items=self.allowed_values,
                    default=self.value,
                )
            elif isinstance(self.allowed_values, tuple):
                if self.allowed_values == (0, 1):
                    self.update_ui(
                        callback="set_checked",
                        widget=widget,
                        new_check_state=self.value == 1,
                    )
                    self.update_ui(callback="set_text", widget=widget, text=self.desc)
                elif len(self.allowed_values) == 2:
                    self.update_ui(
                        callback="set_range",
                        widget=widget,
                        min_val=self.allowed_values[0],
                        max_val=self.allowed_values[1],
                        default_val=int(self.value),
                    )
                else:
                    return False
            elif isinstance(self.allowed_values, str):
                if hasattr(widget, "textEdited"):
                    self.update_ui(callback="set_text", widget=widget, text=self.value)
                elif hasattr(widget, "clicked"):
                    self.update_ui(callback="set_text", widget=widget, text=self.desc)
                elif hasattr(widget, "insertPlainText"):
                    self.update_ui(callback="set_text", widget=widget, text=self.value)
            else:
                return False
        if self.is_output:
            self.output = widget
            self.update_output(label_text=self.desc, output_value=self.value)

        self.update_ui(callback="set_tool_tip", widget=widget, tool_tip=self.hint)
        self.update_ui(callback="set_tool_tip", widget=label, tool_tip=self.hint)

        self.update_ui(callback="connect_call_back", widget=widget, param=self)

        return True

    def update_label(self):
        lbl = self.label
        if lbl is None:
            return False
        if (
            isinstance(self.allowed_values, dict)
            or isinstance(self.allowed_values, str)
            or (self.widget_type == "spin_box")
        ):
            self.update_ui(callback="set_text", widget=lbl, text=self.desc)
        elif isinstance(self.allowed_values, tuple) and (len(self.allowed_values) == 2):
            self.update_ui(
                callback="set_text", widget=lbl, text=f"{self.desc}: {self.value}"
            )
        else:
            return False
        self.update_ui(callback="set_tool_tip", widget=lbl, tool_tip=self.hint)
        return True

    def update_input(self, new_values=None):
        if not self.is_input:
            return False
        widget = self.input
        if widget is None:
            return False
        if self.kind == "button":
            return True
        elif isinstance(self.allowed_values, dict):
            if (
                (new_values is not None)
                and isinstance(new_values, dict)
                and (self.allowed_values.keys() - new_values.keys() != {})
            ):
                if self.options.get("enable_none", False) is True:
                    self.allowed_values = {**{"none": "none"}, **new_values}
                else:
                    self.allowed_values = new_values
                bck_value = self.value
                self.update_ui(callback="clear", widget=widget)
                self.update_ui(
                    callback="add_items",
                    widget=widget,
                    items=self.allowed_values,
                    default=bck_value,
                )
                self._value = bck_value
            else:
                for i, key in enumerate(self.allowed_values):
                    if self.value == key:
                        self.update_ui(
                            callback="set_current_index", widget=widget, index=i
                        )
                        break
        elif isinstance(self.allowed_values, tuple):
            if self.allowed_values == (0, 1):
                self.update_ui(
                    callback="set_checked",
                    widget=widget,
                    new_check_state=self.value == 1,
                )
            elif len(self.allowed_values) == 2:
                if (
                    (new_values is not None)
                    and isinstance(new_values, tuple)
                    and (self.allowed_values != new_values)
                ):
                    self.allowed_values = new_values
                    self.update_ui(
                        callback="set_range",
                        widget=widget,
                        min_val=self.allowed_values[0],
                        max_val=self.allowed_values[1],
                        default_val=None,
                    )
                self.update_ui(
                    callback="set_value",
                    widget=widget,
                    value=int(self.value),
                )
            else:
                return False
        elif isinstance(self.allowed_values, str):
            self.update_ui(callback="set_text", widget=widget, text=self.value)
        else:
            return False
        self.update_ui(callback="set_tool_tip", widget=widget, tool_tip=self.hint)
        return True

    def update_output(
        self, label_text: str = "", output_value=None, ignore_list=(), invert=False
    ):
        if not self.is_output:
            return False
        self._value = output_value
        if label_text and isinstance(label_text, str):
            self.desc = label_text
            self.update_label()
        widget = self.output
        if widget is None:
            return True
        elif self.allowed_values == "single_line_text_output":
            self.update_ui(callback="set_text", widget=widget, text=self.value)
        elif self.allowed_values == "multi_line_text_output":
            self.update_ui(callback="clear", widget=widget)
            self.update_ui(callback="set_text", widget=widget, text=self.value)
        elif self.allowed_values == "table_output":
            self.update_ui(callback="clear", widget=widget)
            self.update_ui(
                callback="update_table",
                widget=widget,
                items=self._value,
                ignore_list=ignore_list,
                invert_order=invert,
            )
        else:
            return False

        return True

    def add_option_to_grid_search(self, new_option: str):
        self.grid_search_options = f"{self._grid_search_options},{new_option}"

    @staticmethod
    def decode_string(gs_code: str):
        res = []
        for opt_ in gs_code.replace(" ", "").split(","):
            try:
                if ("|" in opt_) and (";" in opt_):
                    bd, step = opt_.split(";")
                    left, right = bd.split("|")
                    left, right = min(int(left), int(right) + 1), max(
                        int(left), int(right) + 1
                    )
                    res.extend([i for i in range(left, right, int(step))])
                else:
                    res.append(opt_)
            except ValueError as e:
                logger.exception(f'String decoding failed: "{repr(e)}"')
        return [str(i) for i in sorted(list(set(res)))]

    def decode_grid_search_options(self):
        return self.decode_string(self._grid_search_options)

    def auto_fill_grid_search(self, step=None):
        if not self.is_input:
            return False
        widget = self.input
        if widget is None:
            return False
        if isinstance(self.allowed_values, dict):
            return ",".join([k for k in self.allowed_values.keys()])
        elif isinstance(self.allowed_values, tuple):
            if self.allowed_values == (0, 1):
                return "0,1"
            elif len(self.allowed_values) == 2:
                min_ = min(self.allowed_values[0], self.allowed_values[1])
                max_ = max(self.allowed_values[0], self.allowed_values[1])
                if step is None:
                    step = (max_ - min_) // 10
                return f"{min_}|{max_};{step}"
            else:
                return ""
        else:
            return ""

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        if value != self._value:
            self._value = value
            if self.on_change is not None:
                self.on_change(self)

    @property
    def str_value(self):
        if isinstance(self.value, str):
            return f"'{self.value}'"
        else:
            return str(self.value)

    @property
    def grid_search_options(self):
        return self._grid_search_options

    @grid_search_options.setter
    def grid_search_options(self, value):
        if self._grid_search_options != value:
            self._grid_search_options = value
            widget = self.gs_input
            if widget is not None:
                self.update_ui(callback="set_text", widget=widget, text=value)

    @property
    def input(self):
        return self._widgets.get("input", None)

    @input.setter
    def input(self, value):
        self._widgets["input"] = value

    @property
    def output(self):
        return self._widgets.get("output", None)

    @output.setter
    def output(self, value):
        self._widgets["output"] = value

    @property
    def label(self):
        return self._widgets.get("label", None)

    @label.setter
    def label(self, value):
        self._widgets["label"] = value

    @property
    def gs_label(self):
        return self._widgets.get("gs_label", None)

    @gs_label.setter
    def gs_label(self, value):
        self._widgets["gs_label"] = value
        self.update_ui(callback="set_text", widget=value, text=self.desc)

    @property
    def gs_input(self):
        return self._widgets.get("gs_input", None)

    @gs_input.setter
    def gs_input(self, value):
        self._widgets["gs_input"] = value

    @property
    def gs_auto_fill(self):
        return self._widgets.get("gs_auto_fill", None)

    @gs_auto_fill.setter
    def gs_auto_fill(self, value):
        self._widgets["gs_auto_fill"] = value

    @property
    def gs_copy_from_param(self):
        return self._widgets.get("gs_copy_from_param", None)

    @gs_copy_from_param.setter
    def gs_copy_from_param(self, value):
        self._widgets["gs_copy_from_param"] = value

    @property
    def gs_reset(self):
        return self._widgets.get("gs_reset", None)

    @gs_reset.setter
    def gs_reset(self, value):
        self._widgets["gs_reset"] = value

    @property
    def is_input(self):
        return not isinstance(self.allowed_values, str) or (
            "input" in self.allowed_values
        )

    @property
    def is_output(self):
        return isinstance(self.allowed_values, str) and not (
            "input" in self.allowed_values
        )

    @property
    def is_neutral(self):
        return self.is_output and (self.allowed_values in ["label"])

    @property
    def is_default(self):
        return self.value == self.default_value


class IptParamHolder(object):
    def __init__(self, **kwargs):
        super(IptParamHolder, self).__init__()

        self.block_feedback = False
        self._kwargs = None
        self._param_list = kwargs.get("_param_list", None)
        if self._param_list is None:
            self._param_list = []
            self.build_params()
            for key, value in kwargs.items():
                self.set_or_add_value(key, value)

    def __eq__(self, other) -> bool:
        if (other is None) or (len(self.gizmos) != len(other.gizmos)):
            return False
        else:
            for s, o in zip(self.gizmos, other.gizmos):
                if (s.value != o.value) or (s.name != o.name):
                    return False
        return True

    def copy(self):
        return self.__class__(**self.params_to_dict())

    def build_params(self):
        pass

    def reset(self, is_update_widgets: bool = True):
        self.block_feedback = True
        try:
            for p in self._param_list:
                p.value = p.default_value
                if is_update_widgets:
                    p.update_label()
                    p.update_input()
                    p.update_output()
        finally:
            self.block_feedback = False

    def add(self, new_item) -> IptParam:
        try:
            self._param_list.append(new_item)
        except Exception as e:
            logger.exception(f'Failed to add param "{repr(e)}')
        else:
            return new_item

    def add_combobox(
        self,
        name: str,
        desc: str,
        default_value: str = "",
        values: dict = {},
        hint: str = "",
    ) -> IptParam:
        try:
            param = IptParam(
                name=name,
                desc=desc,
                default_value=default_value,
                allowed_values=values,
                hint=hint,
            )
            param.widget_type = "combo_box"
            return self.add(param)
        except Exception as e:
            logger.exception(f'Failed to add param "{repr(e)}')

    def add_slider(
        self,
        name: str,
        desc: str,
        default_value: int = 0,
        minimum: int = 0,
        maximum: int = 100,
        hint: str = "",
    ) -> IptParam:
        param = IptParam(
            name=name,
            desc=desc,
            default_value=default_value,
            allowed_values=(minimum, maximum),
            hint=hint,
        )
        param.widget_type = "slider"
        return self.add(param)

    def add_checkbox(self, name, desc, default_value, hint="") -> IptParam:
        """Add a checkbox to the widgets

        Arguments:
            name {str} -- name used to access the widget
            desc {str} -- name used for the label associated to the comobobox
            default_value {str} -- default value, dictionary key

        Keyword Arguments:
            hint {str} -- hover hint (default: {''})

        Returns:
            IptParam -- built param
        """
        param = IptParam(
            name=name,
            desc=desc,
            default_value=default_value,
            allowed_values=(0, 1),
            hint=hint,
        )
        param.widget_type = "checkbox"
        return self.add(param)

    def add_text_input(
        self,
        name: str,
        desc: str,
        default_value: str = "-",
        hint: str = "",
        is_single_line: bool = True,
    ) -> IptParam:
        if is_single_line:
            mode_ = "single_line_text_input"
        else:
            mode_ = "multi_line_text_input"
        param = IptParam(
            name=name,
            desc=desc,
            default_value=default_value,
            allowed_values=mode_,
            hint=hint,
        )
        param.widget_type = mode_
        return self.add(param)

    def add_text_output(
        self,
        is_single_line: bool,
        name: str,
        desc: str,
        default_value: str = "-",
        hint: str = "",
    ) -> IptParam:
        if is_single_line:
            mode_ = "single_line_text_output"
        else:
            mode_ = "multi_line_text_output"
        param = IptParam(
            name=name,
            desc=desc,
            default_value=default_value,
            allowed_values=mode_,
            hint=hint,
        )
        param.widget_type = mode_
        return self.add(param)

    def add_table_output(
        self, name: str, desc: tuple, default_value: dict = {}, hint: str = ""
    ) -> IptParam:
        param = IptParam(
            name=name,
            desc=desc,
            default_value=default_value,
            allowed_values="table_output",
            hint=hint,
        )
        param.widget_type = "table_output"
        return self.add(param)

    def add_text_overlay(self, default_value: int = 0) -> IptParam:
        param = IptParam(
            name="text_overlay",
            desc="Overlay text on top of images",
            default_value=default_value,
            allowed_values=(0, 1),
            hint="Draw description text on top of images",
        )
        param.widget_type = "checkbox"
        param.kind = "text_overlay_cb"
        return self.add(param)

    def add_label(self, name: str, desc: str, hint: str = "") -> IptParam:
        param = IptParam(
            name=name, desc=desc, default_value=desc, allowed_values="label", hint=hint
        )
        param.widget_type = "label"
        return self.add(param)

    def add_separator(self, name: str) -> IptParam:
        param = IptParam(
            name=name, desc="", default_value="", allowed_values="label", hint=""
        )
        param.widget_type = "label"
        return self.add(param)

    def add_color_selector(
        self,
        name="color",
        desc="Select color",
        default_value="light_steel_blue",
        hint="",
        enable_none: bool = False,
    ) -> IptParam:
        if enable_none:
            values = {"none": "none"}
        else:
            values = {}
        values = {**values, **{k: k for k in ipc.all_colors_dict}}
        param = IptParam(
            name=name,
            desc=desc,
            default_value=default_value,
            allowed_values=values,
            hint=hint,
        )
        param.widget_type = "combo_box"
        param.kind = "color_selector"
        return self.add(param)

    def add_enabled_checkbox(self) -> IptParam:
        return self.add_checkbox(
            name="enabled",
            desc="Activate tool",
            default_value=1,
            hint="Toggle whether or not tool is active",
        )

    def add_file_naming(
        self,
        output_format: str = "source",
        output_name: str = "as_source",
        global_prefix: str = "",
    ) -> IptParam:
        self.add_combobox(
            name=f"{global_prefix}output_format",
            desc="Image output format",
            default_value=output_format,
            values=dict(source="As source image", jpg="JPEG", png="PNG", tiff="TIFF"),
        )
        self.add_text_input(
            name=f"{global_prefix}subfolders",
            desc="Subfolders",
            default_value="",
            hint='Subfolder names separated byt ","',
        )
        self.add_combobox(
            name=f"{global_prefix}output_name",
            desc="Output naming convention",
            default_value=output_name,
            values=dict(
                as_source="Same as source",
                hash="Use hash for anonymous names",
            ),
        )
        self.add_text_input(
            name=f"{global_prefix}prefix",
            desc="Prefix",
            default_value="",
            hint="Use text as prefix",
        )
        self.add_text_input(
            name=f"{global_prefix}suffix",
            desc="Suffix",
            default_value="",
            hint="Use text as suffix",
        )
        self.add_checkbox(
            name=f"{global_prefix}make_safe_name",
            desc="Replace unsafe caracters",
            default_value=1,
            hint='Will replace *"/\\[]:;|=,<> with "_"',
        )

    def build_output_path(self, file_prefix: str = "") -> str:
        """Creates a fully qualified filename from data generated by add_file_naming

        Returns:
            str: File name
        """
        return os.path.join(
            self.build_output_folder_path(file_prefix=file_prefix),
            self.build_output_filename(file_prefix=file_prefix),
        )

    def build_output_folder_path(self, file_prefix: str = "") -> str:
        fld = self.output_path
        subfolders = self.get_value_of(f"{file_prefix}subfolders")
        if subfolders:
            fld = os.path.join(fld, *[make_safe_name(sf) for sf in subfolders.split(",")])

        return fld

    def build_output_filename(self, file_prefix: str = "") -> str:
        wrapper = self.wrapper
        # Build output file name
        output_name_mode = self.get_value_of(f"{file_prefix}output_name")
        if output_name_mode == "as_source":
            dst_name = wrapper.file_handler.file_name_no_ext
        elif output_name_mode == "hash":
            dst_name = self.hash_luid()
        else:
            dst_name = "unk"
            logger.error(f"Unknown output name convention: '{output_name_mode}'")

        prefix = self.get_value_of(f"{file_prefix}prefix")
        if prefix:
            dst_name = prefix + dst_name

        suffix = self.get_value_of(f"{file_prefix}suffix")
        if suffix:
            dst_name += suffix

        if self.get_value_of(f"{file_prefix}make_safe_name"):
            dst_name = make_safe_name(dst_name)

        # Get new extension
        file_ext = self.get_value_of(f"{file_prefix}output_format")
        if file_ext == "source":
            file_ext = self.wrapper.file_handler.file_ext
        else:
            file_ext = f".{file_ext}"

        return f"{dst_name}{file_ext}"

    def save_images(self, additional_images: list, file_prefix: str = "", **kwargs):
        wrapper = self.init_wrapper(**kwargs)
        dst_path = self.build_output_path(file_prefix=file_prefix)
        self.add_value(
            key=self.get_value_of("img_name"),
            value=os.path.basename(dst_path),
            force_add=True,
        )
        force_directories(os.path.join(os.path.dirname(dst_path), ""))
        cv2.imwrite(filename=dst_path, img=self.result)
        # Add linked images
        if (
            self.get_value_of("grab_linked_images", default_value=0) == 1
        ) and additional_images:
            file_ext = (
                wrapper.file_handler.file_ext
                if self.get_value_of(f"{file_prefix}output_format") == "source"
                else f".{self.get_value_of(f'{file_prefix}output_format')}"
            )
            base_name, _ = os.path.splitext(os.path.basename(dst_path))
            root_folder = os.path.join(os.path.dirname(dst_path), "")

            for k, v in additional_images.items():
                self.add_value(
                    key=f'{self.get_value_of("img_name")}_{k}',
                    value=f"{base_name}_{k}{file_ext}",
                    force_add=True,
                )
                cv2.imwrite(
                    filename=os.path.join(
                        root_folder,
                        f"{base_name}_{k}{file_ext}",
                    ),
                    img=v,
                )

    def add_channel_selector(
        self,
        default_value,
        name="channel",
        desc="Channel",
        hint: str = "",
        enable_none: bool = False,
    ) -> IptParam:
        if enable_none:
            values = {"none": "none"}
        else:
            values = {}
        values = {
            **values,
            **{
                channel_info[1]: ipc.get_hr_channel_name(channel_info[1])
                for channel_info in ipc.create_channel_generator(include_msp=True)
            },
        }
        param = IptParam(
            name=name,
            desc=desc,
            default_value=default_value,
            allowed_values=values,
            hint=hint,
        )
        if enable_none:
            param.options["enable_none"] = True
        param.widget_type = "combo_box"
        param.kind = "channel_selector"
        return self.add(param)

    def add_arithmetic_operator(
        self,
        default_value="plus",
        name="operator",
        desc="Arithmetic operator",
        hint="Operator to use with operands",
    ) -> IptParam:
        param = IptParam(
            name=name,
            desc=desc,
            default_value=default_value,
            allowed_values=dict(plus="+", minus="-", mult="*", div="/", power="^"),
            hint=hint,
        )
        param.widget_type = "combo_box"
        param.kind = "arithmetic_operator"
        return self.add(param)

    def add_source_selector(
        self,
        name: str = "source_file",
        desc: str = "Select source file type",
        default_value: str = "source",
    ) -> IptParam:
        param = IptParam(
            name=name,
            desc=desc,
            default_value=default_value,
            allowed_values=dict(
                source="source",
                mask="mask",
                source_roi="Source with ROIs applied",
                process_roi="Use roi created for process",
                masked_source="masked source",
                cropped_source="source cropped to keep ROI (if available)",
                source_median="source with median filter (5 if not set)",
            ),
        )
        param.widget_type = "combo_box"
        param.kind = "source_selector"
        return self.add(param)

    def add_color_map_selector(
        self,
        name="color_map",
        default_value="c_2",
        desc="Select pseudo color map",
        hint="",
    ) -> IptParam:
        param = IptParam(
            name=name,
            desc=desc,
            default_value=default_value,
            allowed_values=dict(
                a_0="Autumn",
                b_1="Bone",
                c_2="Jet",
                d_3="Winter",
                e_4="Rainbow",
                f_5="Ocean",
                g_6="Summer",
                h_7="Spring",
                i_8="Cool",
                j_9="HSV",
                k_10="Pink",
                l_11="Hot",
            ),
            hint=hint,
        )
        param.widget_type = "combo_box"
        param.kind = "color_map_selector"
        return self.add(param)

    def add_color_space(self, default_value) -> IptParam:
        param = IptParam(
            name="color_space",
            desc="Color space",
            default_value=default_value,
            allowed_values=dict(HSV="HSV", LAB="LAB", RGB="RGB"),
        )
        param.widget_type = "combo_box"
        param.kind = "color_space_selector"
        return self.add(param)

    def add_roi_type(self, default_value="other") -> IptParam:
        param = IptParam(
            name="roi_type",
            desc="Select action linked to ROI",
            default_value=default_value,
            allowed_values=dict(
                keep="Keep region inside ROI",
                delete="Delete region inside ROI",
                crop="Crop image to ROI (most tools don not support this option)",
                safe="Region inside ROI is safe",
                enforce="Check mask position",
                erode="Erode region inside ROI - mask only",
                dilate="Dilate region inside ROI - mask only",
                open="Open region inside ROI - mask only",
                close="Close region inside ROI - mask only",
                other="No predefined behavior",
            ),
        )
        param.kind = "roi_type_selector"
        return self.add(param)

    def add_roi_name(self, default_value: str = "unnamed_roi") -> IptParam:
        param = self.add_text_input(
            name="roi_name", desc="ROI name", default_value="unnamed_roi"
        )
        param.kind = "roi_name_selector"
        return param

    def add_tool_target(self) -> IptParam:
        param = IptParam(
            name="tool_target",
            desc="Target IPT",
            default_value="none",
            allowed_values=dict(none="None"),
        )
        param.kind = "tool_target_selector"
        return self.add(param)

    def add_roi_shape(self, default_value="rectangle") -> IptParam:
        param = IptParam(
            name="roi_shape",
            desc="Select ROI shape",
            default_value=default_value,
            allowed_values=dict(
                rectangle="Rectangle",
                circle="Circle, will be treated as rectangle for morphology",
            ),
        )
        param.kind = "roi_shape_selector"
        return self.add(param)

    def add_roi_settings(
        self,
        default_name: str = "unnamed_roi",
        default_type: str = "other",
        default_shape: str = "",
    ) -> IptParam:
        self.add_roi_name(default_value=default_name)
        self.add_roi_type(default_value=default_type)
        if default_shape:
            self.add_roi_shape(default_value=default_shape)
        self.add_tool_target()

    def add_hierarchy_threshold(self, default_value: int = 35) -> IptParam:
        self.add_slider(
            name="hierarchy_threshold",
            desc="Label merger threshold",
            default_value=default_value,
            minimum=0,
            maximum=1000,
            hint="Regions connected by an edge with weight smaller than thresh are merged",
        )

    def add_edge_detector(self, default_operator: str = "canny_opcv"):
        self.add_combobox(
            name="operator",
            desc="Select edge detection operator",
            default_value=default_operator,
            values=dict(
                canny_opcv="Canny OpenCV",
                canny_scik="Canny Scikit",
                laplacian="Laplacian",
                sobel="Sobel",
                sobel_v="Sobel vertical",
                sobel_h="Sobel horizontal",
                roberts="Roberts",
                prewitt="Prewitt",
            ),
        )
        self.add_spin_box(
            name="canny_sigma",
            desc="Canny's sigma for scikit, aperture for OpenCV",
            default_value=2,
            minimum=0,
            maximum=20,
            hint="Sigma.",
        )
        self.add_spin_box(
            name="canny_first",
            desc="Canny's first Threshold",
            default_value=0,
            minimum=0,
            maximum=255,
            hint="First threshold for the hysteresis procedure.",
        )
        self.add_spin_box(
            name="canny_second",
            desc="Canny's second Threshold",
            default_value=255,
            minimum=0,
            maximum=255,
            hint="Second threshold for the hysteresis procedure.",
        )
        self.add_spin_box(
            name="kernel_size",
            desc="Kernel size",
            default_value=5,
            minimum=0,
            maximum=27,
        )
        self.add_spin_box(
            name="threshold",
            desc="Threshold",
            default_value=130,
            minimum=0,
            maximum=255,
            hint="Threshold for kernel based operators",
        )
        self.add_checkbox(name="apply_threshold", desc="Apply threshold", default_value=1)

    def add_binary_threshold(self, add_morphology: bool = True):
        self.add_spin_box(
            name="min_t",
            desc="Threshold min value",
            default_value=0,
            minimum=0,
            maximum=255,
        )
        self.add_spin_box(
            name="max_t",
            desc="Threshold max value",
            default_value=255,
            minimum=0,
            maximum=255,
        )
        self.add_slider(
            name="median_filter_size",
            desc="Median filter size (odd values only)",
            default_value=0,
            minimum=0,
            maximum=51,
        )
        if add_morphology:
            self.add_morphology_operator()

    def add_roi_selector(self):
        self.add_text_input(
            name="roi_names",
            desc="Name of ROI to be used",
            default_value="",
            hint="Operation will only be applied inside of ROI",
        )
        self.add_combobox(
            name="roi_selection_mode",
            desc="ROI selection mode",
            default_value="all_linked",
            values=dict(
                all_linked="Select all linked ROIs",
                linked_and_named="Select all ROIs named in the list that are linked",
                all_named="Select all named ROIs regardless if they're linked or not",
            ),
        )

    def add_morphology_operator(self, default_operator: str = "none"):
        self.add_combobox(
            name="morph_op",
            desc="Morphology operator",
            default_value=default_operator,
            values=dict(
                none="none", erode="erode", dilate="dilate", open="open", close="close"
            ),
        )
        self.add_spin_box(
            name="kernel_size",
            desc="Kernel size",
            default_value=3,
            minimum=3,
            maximum=101,
        )
        self.add_combobox(
            name="kernel_shape",
            desc="Kernel shape",
            default_value="ellipse",
            values=dict(ellipse="ellipse", rectangle="rectangle", cross="cross"),
        )
        self.add_spin_box(
            name="proc_times",
            desc="Iterations",
            default_value=1,
            minimum=1,
            maximum=100,
        )

    def add_exposure_viewer_switch(self):
        self.add_checkbox(
            name="show_over_under",
            desc="Show over an under exposed parts",
            default_value=0,
        )

    def add_button(
        self, name: str, desc: str, index: int = 0, hint: str = ""
    ) -> IptParam:
        param = IptParam(
            name=name,
            desc=desc,
            default_value=index,
            allowed_values="input_button",
            hint=hint,
        )
        param.kind = "button"
        self.add(param)

    def add_spin_box(
        self,
        name: str,
        desc: str,
        default_value: int = 0,
        minimum: int = 0,
        maximum: int = 100,
        hint: str = "",
    ):
        param = IptParam(
            name=name,
            desc=desc,
            default_value=default_value,
            allowed_values=(minimum, maximum),
            hint=hint,
        )
        param.widget_type = "spin_box"
        self.add(param)

    def add_date_picker(
        self, name: str, desc: str, default_value: int = 0, hint: str = ""
    ):
        pass

    def reset_grid_search(self):
        for p in self._param_list:
            p.grid_search_options = str(p.default_value)
            gsw = p.gs_input
            if gsw is not None:
                self.update_ui(
                    callback="set_text", widget=gsw, text=p.grid_search_options
                )

    def update_grid_search(self, ignore_composite: bool = True) -> None:
        for p in self._param_list:
            values = p.grid_search_options
            if ignore_composite and (
                (";" in values) or ("|" in values) or ("," in values)
            ):
                continue
            p.grid_search_options = str(p.value)
            gsw = p.gs_input
            if gsw is not None:
                self.update_ui(
                    callback="set_text", widget=gsw, text=p.grid_search_options
                )

    def reset_input(self) -> None:
        for p in self._param_list:
            if p.is_input:
                p.value = p.default_value

    def reset_output(self) -> None:
        for p in self._param_list:
            if p.is_output:
                p.value = p.default_value

    def find_by_name(self, name) -> IptParam:
        for p in self._param_list:
            if p.name == name:
                return p
        return None

    def get_value_of(self, key, default_value=None, scale_factor=1) -> str:
        if (self._kwargs is not None) and (key in self._kwargs):
            res = self._kwargs.get(key, None)
            if res is not None:
                return res
        p = self.find_by_name(key)
        if p is not None:
            res = p.value
        else:
            res = default_value
        try:
            tmp = int(res)
        except ValueError:
            return res
        except TypeError:
            return res
        else:
            if scale_factor != 1:
                return round(tmp * scale_factor)
            else:
                return tmp

    def has_param(self, key: str) -> bool:
        d = {} if self._kwargs is None else dict(self._kwargs)
        d.update(self.params_to_dict())
        return key in d.keys()

    def has_key_matching(self, partial: str) -> bool:
        d = {} if self._kwargs is None else dict(self._kwargs)
        d.update(self.params_to_dict())
        for k in d.keys():
            if partial in k:
                return True
        return False

    def has_keys(self, keys) -> int:
        res = 0
        for key in keys:
            if self.has_param(key):
                res += 1
        return res

    def set_value_of(self, key, value, update_widgets: bool = False):
        p = self.find_by_name(key)
        if p is not None:
            if value is not None:
                p.value = value
            else:
                p.value = p.default_value
            if update_widgets:
                p.update_label()
                p.update_input()
                p.update_output()

    def set_or_add_value(self, key, value):
        p = self.find_by_name(key)
        if p is None:
            self.add(
                IptParam(name=key, desc="", default_value=value, allowed_values=None)
            )
        else:
            if value is not None:
                p.value = value
            else:
                p.value = p.default_value

    def set_or_add_param(self, src_param, allow_add):
        if src_param is None:
            return False
        p = self.find_by_name(src_param.name)
        if (p is None) and not allow_add:
            return False
        elif p is not None:
            self._param_list.remove(p)
        self.add(src_param.copy())

    def get(self, key, value, default=None):
        p = self.find_by_name(key)
        if p is not None:
            return getattr(p, value)
        else:
            return default

    def update_output_from_dict(self, data: dict):
        self.reset_output()
        for p in self._param_list:
            val = data.get(p.name, None)
            if val is not None:
                p.update_output(output_value=str(val))

    def input_params(
        self,
        exclude_defaults: bool = False,
        excluded_params: tuple = (),
        forced_params: tuple = (),
    ):
        return [
            p
            for p in self.gizmos
            if (
                p.is_input
                and not (exclude_defaults and p.is_default)
                and (p.name not in excluded_params)
            )
            or (p.name in forced_params)
        ]

    def output_params(
        self,
        exclude_defaults: bool = False,
        excluded_params: tuple = (),
        forced_params: tuple = (),
    ):
        return [
            p
            for p in self.gizmos
            if (
                p.is_output
                and not (exclude_defaults and p.is_default)
                and (p.name not in excluded_params)
            )
            or (p.name in forced_params)
        ]

    def all_params(
        self,
        exclude_defaults: bool = False,
        excluded_params: tuple = (),
        forced_params: tuple = (),
    ):
        return [
            p
            for p in self.gizmos
            if (
                not (exclude_defaults and p.is_default)
                and (p.name not in excluded_params)
            )
            or (p.name in forced_params)
        ]

    def params_to_dict(
        self,
        include_input: bool = True,
        include_output: bool = False,
        include_neutral: bool = False,
    ):
        dic = {}
        for p in self.gizmos:
            if (
                (include_input and p.is_input)
                or (include_output and p.is_output)
                or (include_neutral and p.is_neutral)
            ):
                dic[p.name] = p.value
        return dic

    def update_inputs(self, update_values: dict = {}):
        channels = update_values.get("channels", None)
        ipt_list = update_values.get("ipt_list", None)
        for p in self._param_list:
            if (p.kind == "channel_selector") and (channels is not None):
                p.update_input(new_values=channels)
            elif (p.kind == "tool_target_selector") and (ipt_list is not None):
                p.update_input(new_values={**{"none": "None"}, **ipt_list})

    @property
    def gizmos(self):
        return self._param_list

    @property
    def has_input(self):
        for p in self._param_list:
            if p.is_input:
                return True
        return False

    @property
    def has_output(self):
        for p in self._param_list:
            if p.is_output:
                return True
        return False


class IptBase(IptParamHolder, ABC):
    def __init__(self, wrapper=None, **kwargs):
        super(IptBase, self).__init__(**kwargs)

        self._wrapper = wrapper
        self._result = None
        self.result = None
        self.demo_image = None
        self._old_lock_state = False

        self.output_path = ""

    def __repr__(self):
        return (
            f"{type(self).__name__}("
            + f",".join([f"{p.name}={p.str_value}" for p in self.gizmos])
            + ")"
        )

    def __str__(self):
        return f"{type(self).__name__}_" + self.input_params_as_str(
            exclude_defaults=True,
            excluded_params=("progress_callback",),
            forced_params=("channel",),
        )

    def __enter__(self):
        wrapper = self.wrapper
        if wrapper is not None:
            self._old_lock_state = wrapper.lock
            wrapper.lock = True
        return self.process_wrapper(), self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.wrapper.lock = self._old_lock_state

    def short_desc(self):
        res = f"{type(self).__name__}_"
        gizmos_info = {}
        for p in self.gizmos:
            if p.kind not in gizmos_info.keys():
                gizmos_info[p.kind] = str(p)
        if "channel_selector" in gizmos_info.keys():
            res += str(gizmos_info["channel_selector"])
        elif "roi_name_selector" in gizmos_info.keys():
            res += str(gizmos_info["roi_name_selector"])
        elif "color_space_selector" in gizmos_info.keys():
            res += str(gizmos_info["color_space_selector"])
        return res

    def copy(self, copy_wrapper: bool = True):
        if copy_wrapper:
            return self.__class__(wrapper=self.wrapper, **self.params_to_dict())
        else:
            return self.__class__(**self.params_to_dict())

    def to_json(self):
        return {
            "name": self.name,
            "package": self.package,
            CLASS_NAME_KEY: type(self).__name__,
            MODULE_NAME_KEY: type(self).__module__,
            PARAMS_NAME_KEY: self.params_to_dict(),
            GRID_SEARCH_PARAMS_NAME_KEY: {
                p.name: p.grid_search_options for p in self.gizmos
            },
        }

    @classmethod
    def from_json(cls, json_data: dict):
        class_name = json_data[CLASS_NAME_KEY]
        module_name: str = json_data[MODULE_NAME_KEY].replace("ip_tools", "ipt")
        if "ipt" in module_name and "ipapi" not in module_name:
            module_name = module_name.replace("ipt", "ipso_phen.ipapi.ipt", 1)
        if "ipapi" in module_name and "ipso_phen" not in module_name:
            module_name = module_name.replace("ipapi", "ipso_phen.ipapi", 1)
        __import__(module_name)
        for _, obj in inspect.getmembers(sys.modules[module_name]):
            if inspect.isclass(obj) and (obj.__name__ == class_name):
                try:
                    ipt = obj(**json_data[PARAMS_NAME_KEY])
                    break
                except Exception as e:
                    return e
        else:
            ipt = None
        if ipt is None:
            return None
        gs_params = json_data.get(GRID_SEARCH_PARAMS_NAME_KEY, None)
        if gs_params:
            for p in ipt.gizmos:
                gp = gs_params.get(p.name, None)
                if gp:
                    p.grid_search_options = gp
        return ipt

    def execute(self, param, **kwargs):
        pass

    def init_wrapper(self, **kwargs) -> BaseImageProcessor:
        """Initializes wrapper according to key arguments

        Returns:
            BaseImageProcessor -- Wrapper
        """
        self._kwargs = kwargs
        wrapper = self._get_wrapper()
        self.demo_image = None
        if kwargs.get("reset_wrapper", True) is True:
            wrapper.reset()
        return wrapper

    def process_grid_search(self, **kwargs):
        progress_callback = kwargs.get("progress_callback", None)
        random_grid_search = kwargs.get("random_grid_search", False)

        def lcl_callback(step, total, msg, image_dict={}):
            if progress_callback is not None:
                return progress_callback(step, total, msg, image_dict)
            else:
                print(msg)
                return True

        tmp_wrapper = kwargs.get("wrapper", None)
        if tmp_wrapper is not None:
            self.wrapper = tmp_wrapper
        elif self.wrapper is None:
            self._kwargs = kwargs
            self._wrapper = self._get_wrapper()
            self._wrapper.reset()
            self._kwargs = None

        if self.wrapper is None:
            return False

        procs = list(
            itertools.product(*[p.decode_grid_search_options() for p in self.gizmos])
        )
        if random_grid_search:
            random.shuffle(procs)
        tot_ = len(procs)
        keys = [p.name for p in self.gizmos]
        lcl_callback(0, tot_, f"_____________________________________")
        lcl_callback(0, tot_, f"Instantiated tools")
        for i, p in enumerate(procs):
            kwargs_ = {k: (int(v) if str.isdigit(v) else v) for k, v in zip(keys, p)}
            kwargs_["progress_callback"] = progress_callback
            ip = self.__class__(**kwargs_)
            self.wrapper.image_list = []
            kwargs_["wrapper"] = self.wrapper
            kwargs_["reset_wrapper"] = False
            if ip.process_wrapper(**kwargs_):
                img_lst_ = ip.wrapper.image_list
                if len(img_lst_) > 0:
                    if kwargs.get("send_all_images", False):
                        for dic in ip.wrapper.image_list:
                            go_on = lcl_callback(
                                i + 1,
                                tot_,
                                f"""{ip.name}:
                                 {ip.input_params_as_str(exclude_defaults=True,
                                 excluded_params=("progress_callback",))}""",
                                dic,
                            )
                            if go_on is False:
                                return
                    else:
                        dic = ip.wrapper.retrieve_image_dict("mosaic_out")
                        if dic is None:
                            dic = ip.wrapper.retrieve_image_dict("mosaic")
                            if dic is None:
                                dic = img_lst_[len(img_lst_) - 1]
                        go_on = lcl_callback(
                            i + 1,
                            tot_,
                            f"""{ip.name}:
                             {ip.input_params_as_str(exclude_defaults=True, 
                             excluded_params=("progress_callback",))}""",
                            dic,
                        )
                        if go_on is False:
                            return
                else:
                    go_on = lcl_callback(i + 1, tot_, f"Failed {str(ip)}")
                    if not go_on:
                        return

    def do_channel_failure(self, channel):
        self.wrapper.store_image(
            self.wrapper.current_image, f"Missing {channel} channel", text_overlay=True
        )
        logger.error(f"Missing {channel} channel")

    def _get_wrapper(self):
        if "wrapper" in self.kwargs:
            value = self.kwargs.get("wrapper", None)
            if isinstance(value, str):
                self.wrapper = BaseImageProcessor(value)
            else:
                self._wrapper = value
        return self._wrapper

    def get_mask(self):
        mask = self.wrapper.mask
        if mask is None:
            img = self.wrapper.current_image
            if np.sum(img[img != 255]) == 0:
                mask = self.wrapper.get_channel(src_img=img, channel="bl")
        return mask

    def to_uint8(self, img, normalize: bool = False):
        if str(img.dtype) == "bool":
            img = img.astype(np.uint8)
            img[img != 0] = 255
            return img
        elif (
            (str(img.dtype) == "float64")
            or (str(img.dtype) == "float16")
            or (str(img.dtype) == "int32")
        ):
            return ((img - img.min()) / (img.max() - img.min()) * 255).astype(np.uint8)
        elif str(img.dtype) == "uint8":
            if normalize:
                if len(img.shape) == 2:
                    return ((img - img.min()) / (img.max() - img.min()) * 255).astype(
                        np.uint8
                    )
                else:
                    c1, c2, c3 = cv2.split(img)
                    c1, c2, c3 = (
                        cv2.equalizeHist(c1),
                        cv2.equalizeHist(c2),
                        cv2.equalizeHist(c3),
                    )
                    return np.dstack((c1, c2, c3))
            else:
                return img.copy()
        else:
            logger.error(f"Unknown source format {str(img.type)}")

    def to_fuzzy(self, img):
        """
        Converts image to float numbers constrained between 0 & 1
        :param img:
        :return: image
        """
        if str(img.dtype) == "bool":
            img = img.astype(np.uint8)
            return img
        elif (
            (str(img.dtype) == "float64")
            or (str(img.dtype) == "int32")
            or (str(img.dtype) == "uint8")
        ):
            return ((img - img.min()) / (img.max() - img.min()) * 1).astype(np.float)
        else:
            logger.error(f"Unknown source format {str(img.type)}")

    def to_bit(self, img, threshold=255):
        """
        Converts image data to either 0 or 1, be careful with what you wish for
        :param img:
        :param threshold:
        :return: image
        """
        if str(img.dtype) == "bool":
            img = img.astype(np.uint8)
            return img
        elif str(img.dtype) == "uint8":
            img[img < threshold] = 0
            img[img >= threshold] = 1
            return img
        elif (str(img.dtype) == "float64") or (str(img.dtype) == "int32"):
            return ((img - img.min()) / (img.max() - img.min()) * 1).astype(np.uint8)
        else:
            logger.error(f"Unknown source format {str(img.type)}")

    @staticmethod
    def apply_mask(image, mask):
        return cv2.bitwise_and(image, image, mask=mask)

    def match_image_size_to_source(
        self,
        img,
        source_mode: str = "source_file",
        ignore_list: tuple = (),
    ):
        if not (source_mode in ignore_list):
            source_type = self.get_value_of(source_mode, "source")
        else:
            return img

        if source_type == "process_roi":
            self.wrapper.init_rois()
            return self.wrapper.crop_to_roi(img, type(self).__name__.lower())
        elif source_type == "cropped_source":
            self.wrapper.init_rois()
            return self.wrapper.crop_to_keep_roi(img=img)
        else:
            return img

    def get_ipt_roi(
        self,
        wrapper,
        roi_names: list = [],
        selection_mode: str = "all_linked",
    ) -> list:
        res = []
        for roi in wrapper.rois_list:
            if selection_mode == "all_linked":
                if roi.target == type(self).__name__:
                    res.append(roi)
            elif selection_mode == "linked_and_named":
                if (roi.target == type(self).__name__) and (roi.name in roi_names):
                    res.append(roi)
            elif selection_mode == "all_named":
                if roi.name in roi_names:
                    res.append(roi)
            else:
                raise NotImplementedError
        return res

    def get_short_hash(
        self,
        exclude_list: tuple = (),
        add_plant_name: bool = True,
    ) -> Union[str, None]:
        wrapper = self.wrapper
        if wrapper is None:
            return None
        p_str = self.input_params_as_str(
            exclude_defaults=False, excluded_params=exclude_list
        ).encode("utf-8")
        w_str = str(wrapper).encode("utf-8")
        long_hash = hashlib.sha1(p_str + w_str)

        if add_plant_name:
            return (
                wrapper.plant
                + "_"
                + make_safe_name(
                    str(base64.urlsafe_b64encode(long_hash.digest()[0:20]))
                ).replace("_", "")
            )
        else:
            return make_safe_name(
                str(base64.urlsafe_b64encode(long_hash.digest()[0:20]))
            ).replace("_", "")

    def hash_luid(self):
        return make_safe_name(
            str(
                base64.urlsafe_b64encode(
                    hashlib.sha1(self.wrapper.luid.encode("utf-8")).digest()[0:20]
                )
            )
        ).replace("_", "")

    def apply_binary_threshold(self, wrapper, img, channel):
        min_ = self.get_value_of("min_t")
        max_ = self.get_value_of("max_t")
        median_filter_size = self.get_value_of("median_filter_size")
        median_filter_size = (
            0 if median_filter_size == 1 else ipc.ensure_odd(median_filter_size)
        )

        min_, max_ = min(min_, max_), max(min_, max_)

        mask, _ = wrapper.get_mask(
            src_img=img,
            channel=channel,
            min_t=min_,
            max_t=max_,
            median_filter_size=median_filter_size,
        )

        return self.apply_morphology_from_params(mask)

    def apply_morphology_from_params(self, mask, store_result: bool = False):
        if mask is None:
            return None

        kernel_size = self.get_value_of("kernel_size", 0)
        iter_ = self.get_value_of("proc_times", 1)
        kernel_shape = self.get_value_of("kernel_shape", None)

        if not (len(mask.shape) == 2 or (len(mask.shape) == 3 and mask.shape[2] == 1)):
            logger.error("Morphology works only on mask images")
            return None

        if kernel_shape == "rectangle":
            k_shape = cv2.MORPH_RECT
        elif kernel_shape == "cross":
            k_shape = cv2.MORPH_CROSS
        else:
            k_shape = cv2.MORPH_ELLIPSE

        if kernel_size <= 1:
            return mask
        elif (kernel_size % 2 == 0) and (kernel_size > 0):
            kernel_size += 1

        func = getattr(self._wrapper, self.get_value_of("morph_op"), None)
        if func:
            mask = func(
                mask, kernel_size=kernel_size, proc_times=iter_, kernel_shape=k_shape
            )

        if store_result:
            self.wrapper.store_image(image=mask, text="morphology_applied")

        return mask

    def print_segmentation_labels(
        self, watershed_image, labels, dbg_suffix="", min_size=-1, source_image=None
    ):
        if source_image is None:
            source_image = self._wrapper.current_image
        # loop over the unique labels returned by the Watershed
        # algorithm
        for label in np.unique(labels):
            # if the label is zero, we are examining the 'background'
            # so simply ignore it
            if label == 0:
                continue

            # otherwise, allocate memory for the label region and draw
            # it on the mask
            mask = np.zeros(watershed_image.shape[:2], dtype="uint8")
            mask[labels == label] = 255

            # detect contours in the mask and grab the largest one
            contours_ = ipc.get_contours(
                mask=mask,
                retrieve_mode=cv2.RETR_EXTERNAL,
                method=cv2.CHAIN_APPROX_SIMPLE,
            )
            c = max(contours_, key=cv2.contourArea)

            # Draw min area rect enclosing object
            rect = cv2.minAreaRect(c)
            box = cv2.boxPoints(rect)
            box = np.int0(box)
            x = int(rect[0][0])
            y = int(rect[0][1])
            area_ = round(rect[1][0] * rect[1][1])
            is_area_enough = area_ > min_size
            draw_color = (255, 255, 255) if is_area_enough else (0, 0, 0)
            cv2.drawContours(watershed_image, [box], 0, draw_color, 2)
            cv2.drawContours(watershed_image, [c], 0, draw_color, 4)
            cv2.putText(
                watershed_image,
                f"#{label}: {area_}",
                (x - 10, y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                draw_color,
                2,
            )
            cv2.drawContours(source_image, [c], 0, draw_color, 4)
            cv2.putText(
                source_image,
                f"#{label}: {area_}",
                (x - 10, y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                draw_color,
                2,
            )

        self._wrapper.store_image(
            watershed_image, f"{dbg_suffix}_vis_labels", text_overlay=True
        )
        self._wrapper.store_image(
            source_image, f"{dbg_suffix}_labels_on_source_image", text_overlay=True
        )

        return watershed_image, source_image

    def help_stub(self):
        res = '"""\n'
        res += f"{self.name}:\n"
        res += self.description
        res += "\n"
        res += f"Real time: {str(self.real_time)}\n"
        res += "\n"
        res += "Keyword Arguments (in parentheses, argument name):\n"
        if self.has_input:
            for p in self.gizmos:
                if p.is_input:
                    res += f"    * {p.desc} ({p.name}): {p.hint}".rstrip() + "\n"
        if self.has_input and self.has_output:
            res += "--------------\n"
        if self.has_output:
            for p in self.gizmos:
                if p.is_output and not p.is_neutral:
                    res += f"    * output  ({p.name}): {p.desc}".rstrip() + "\n"
        res += '"""\n'

        return res

    def input_params_as_str(
        self,
        exclude_defaults: bool = True,
        excluded_params: tuple = (),
        forced_params: tuple = (),
    ):
        return ", ".join(
            [
                f"{p.name}={p.str_value}"
                for p in self.input_params(
                    exclude_defaults=exclude_defaults,
                    excluded_params=excluded_params,
                    forced_params=forced_params,
                )
            ]
        )

    def input_params_as_html(
        self,
        exclude_defaults: bool = True,
        excluded_params: tuple = (),
        forced_params: tuple = (),
    ):
        return (
            "<ul>"
            + "".join(
                f"<li>{p.name}={p.str_value}</li>"
                for p in self.input_params(
                    exclude_defaults=exclude_defaults,
                    excluded_params=excluded_params,
                    forced_params=forced_params,
                )
            )
            + "</ul>"
        )

    def code_imports(self, **kwargs):
        ret = [f"from {self.__module__} import {type(self).__name__}"]
        if kwargs.get("build_wrapper", "yes") is not False:
            ret.append("from ipso_phen.ipapi.base.ip_abstract import BaseImageProcessor")
        return ret

    def code_apply_roi(self, print_result=None, white_spaces=""):
        ws = "".join(
            [" " for _ in range(0, len(f"{white_spaces}ipt_res = ipt.process_wrapper("))]
        )
        params_ = f",\n{ws}".join(
            [f"{p.name}={p.str_value}" for p in self.input_params(exclude_defaults=True)]
        )
        code_ = f'{white_spaces}if wrapper is None:\n{white_spaces}    raise RuntimeError("Missing wrapper")\n'

        code_ += f"{white_spaces}ipt = {type(self).__name__}({params_})\n"
        code_ += f'{white_spaces}if callable(getattr(ipt, "apply_roy")):\n'
        add_ws = "    "
        code_ += f"{white_spaces}{add_ws}wrapper.current_image = ipt.apply_roy(wrapper=wrapper)\n"

        return code_

    def code_body(self, **kwargs):
        use_with_clause = kwargs.get("use_with_clause", False)
        build_wrapper = kwargs.get("build_wrapper", "yes")
        file_name = kwargs.get("file_name", "")
        white_spaces = kwargs.get("white_spaces", "")
        target_data_base = kwargs.get("target_data_base", None)

        if file_name:
            wrapper_ = file_name
        else:
            wrapper_ = self.file_name

        wrapper_ = "{file}"
        if use_with_clause:
            ws = "".join(
                [" " for _ in range(0, len(f"{white_spaces}with {type(self).__name__}("))]
            )
        else:
            ws = "".join(
                [
                    " "
                    for _ in range(
                        0, len(f"{white_spaces}ipt_res = ipt.process_wrapper(")
                    )
                ]
            )
        params_ = f",\n{ws}".join(
            [f"{p.name}={p.str_value}" for p in self.input_params(exclude_defaults=True)]
        )
        if use_with_clause or (build_wrapper is False):
            if build_wrapper is False:
                wrapper_param = wrapper_
            else:
                wrapper_param = "wrapper"
            if params_:
                params_ = f",\n{ws}".join([f"wrapper={wrapper_param}", params_])
            else:
                params_ = f"wrapper={wrapper_param}"

        if (build_wrapper is True) or (build_wrapper == "yes"):
            code_ = f"{white_spaces}wrapper = BaseImageProcessor({wrapper_})\n"
            if target_data_base:
                code_ += f"{white_spaces}wrapper.target_database = target_data_base\n"
            code_ += f"{white_spaces}wrapper.lock = True\n"
        elif build_wrapper == "expected":
            code_ = f'{white_spaces}if wrapper is None:\n{white_spaces}    raise RuntimeError("Missing wrapper")\n'
        else:
            code_ = ""

        if use_with_clause:
            code_ += (
                f"{white_spaces}with {type(self).__name__}({params_}) as (res, ed):\n"
            )
            add_ws = "    "
            code_ += f"{white_spaces}{add_ws}if res:\n"
            code_ += f"{white_spaces}{add_ws}{add_ws}return ed.result\n"
            code_ += f"{white_spaces}{add_ws}else:\n"
            code_ += (
                f"{white_spaces}{add_ws}{add_ws}"
                + 'print(f"Process error: {str(wrapper.error_holder)}")\n'
            )
        else:
            code_ += f"{white_spaces}ipt = {type(self).__name__}()\n"
            if build_wrapper is not False:
                code_ += f"{white_spaces}ipt.wrapper = wrapper\n"
            code_ += f"{white_spaces}ipt_res = ipt.process_wrapper({params_})\n"
            if self.result_name and (self.result_name != "none"):
                code_ += f"{white_spaces}{self.result_name} = ipt.result\n"
            code_ += f"{white_spaces}if not ipt_res:\n"
            code_ += (
                f"{white_spaces}    "
                + 'print(f"Process error: {str(ipt.wrapper.error_holder)}")\n'
            )

        return code_

    def code(self, **kwargs):
        return (
            "\n".join(self.code_imports(**kwargs)) + "\n\n\n" + self.code_body(**kwargs)
        )

    def apply_test_values_overrides(self, use_cases: tuple = ()):
        pass

    @abstractproperty
    def name(self):
        return "Base abstract image processing tool"

    @property
    def description(self):
        return "\n"

    @property
    def hint(self):
        if self.process_wrapper.__doc__ is not None:
            return inspect.getdoc(self.process_wrapper)
        else:
            return self.help_stub()

    @property
    def needs_doc_string(self):
        return self.process_wrapper.__doc__ is None

    @property
    def real_time(self):
        return False

    @property
    def wrapper(self) -> BaseImageProcessor:
        return self._wrapper

    @wrapper.setter
    def wrapper(self, value):
        self._wrapper = value

    @property
    def is_ready(self):
        return self._wrapper is not None

    @property
    def order(self):
        return 9999

    @property
    def output_kind(self):
        return ""

    @property
    def use_case(self):
        return ["none"]

    @property
    def result(self):
        return self._result

    @result.setter
    def result(self, value):
        self._result = value

    @property
    def result_name(self):
        return "none"

    @property
    def kwargs(self):
        return self._kwargs

    @property
    def lock_once_added(self):
        return False

    @property
    def file_name(self):
        if self.wrapper is not None:
            return f'"{self.wrapper.file_path}"'
        else:
            return "{file}"

    @property
    def package(self):
        return "IPSO Phen"

    @property
    def is_wip(self):
        return False

    @property
    def is_deprecated(self):
        return False

    @property
    def short_test_script(self):
        return self.is_wip or self.is_deprecated

    @property
    def needs_previous_mask(self):
        return False

    @property
    def input_type(self):
        if set(self.use_case).intersection(
            set(
                (
                    ipc.ToolFamily.EXPOSURE_FIXING,
                    ipc.ToolFamily.IMAGE_GENERATOR,
                    ipc.ToolFamily.PRE_PROCESSING,
                    ipc.ToolFamily.THRESHOLD,
                    ipc.ToolFamily.WHITE_BALANCE,
                    ipc.ToolFamily.ROI,
                )
            )
        ):
            return ipc.IO_IMAGE
        elif set(self.use_case).intersection(
            set((ipc.ToolFamily.FEATURE_EXTRACTION, ipc.ToolFamily.MASK_CLEANUP))
        ):
            return ipc.IO_MASK
        else:
            return ipc.IO_NONE

    @property
    def output_type(self):
        if set(self.use_case).intersection(
            set(
                (
                    ipc.ToolFamily.EXPOSURE_FIXING,
                    ipc.ToolFamily.PRE_PROCESSING,
                    ipc.ToolFamily.WHITE_BALANCE,
                )
            )
        ):
            return ipc.IO_IMAGE
        elif set(self.use_case).intersection(
            set((ipc.ToolFamily.THRESHOLD, ipc.ToolFamily.MASK_CLEANUP))
        ):
            return ipc.IO_MASK
        elif set(self.use_case).intersection(set((ipc.ToolFamily.ROI,))):
            return ipc.IO_ROI
        elif set(self.use_case).intersection(
            set((ipc.ToolFamily.IMAGE_GENERATOR, ipc.ToolFamily.FEATURE_EXTRACTION))
        ):
            return ipc.IO_DATA
        elif set(self.use_case).intersection(set((ipc.ToolFamily.VISUALIZATION,))):
            return ipc.IO_IMAGE
        else:
            return ipc.IO_NONE

    @property
    def required_images(self):
        return []

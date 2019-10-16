import inspect
import itertools
import random
from abc import ABC, abstractproperty
from distutils.version import LooseVersion

import cv2
import numpy as np
from PyQt5.QtWidgets import QTableWidgetItem

from ip_base.ip_common import (
    C_BLACK,
    C_LIGHT_STEEL_BLUE,
    C_SILVER,
    C_WHITE,
    all_colors_dict,
    enclose_image,
    resize_image,
    get_hr_channel_name,
    create_channel_generator,
    TOOL_GROUP_ANCILLARY_STR,
    ensure_odd,
    TOOL_GROUP_CLUSTERING_STR,
    TOOL_GROUP_DEMO_STR,
    TOOL_GROUP_DEFAULT_PROCESS_STR,
    TOOL_GROUP_FEATURE_EXTRACTION_STR,
    TOOL_GROUP_EXPOSURE_FIXING_STR,
    TOOL_GROUP_IMAGE_CHECK_STR,
    TOOL_GROUP_IMAGE_GENERATOR_STR,
    TOOL_GROUP_IMAGE_INFO_STR,
    TOOL_GROUP_MASK_CLEANUP_STR,
    TOOL_GROUP_PRE_PROCESSING_STR,
    TOOL_GROUP_ROI_DYNAMIC_STR,
    TOOL_GROUP_ROI_STATIC_STR,
    TOOL_GROUP_THRESHOLD_STR,
    TOOL_GROUP_VISUALIZATION_STR,
    TOOL_GROUP_WHITE_BALANCE_STR,
    TOOL_GROUP_UNKNOWN_STR,
)
from ip_base.ip_abstract import AbstractImageProcessor


class IptParam(object):
    def __init__(self, **kwargs):
        self.name = kwargs.get("name", "no_name")
        self.desc = kwargs.get("desc", "no desc")
        self.default_value = kwargs.get("default_value", "no default")
        self.allowed_values = kwargs.get("allowed_values", None)
        self.hint = kwargs.get("hint", "no clue")
        self.widget_type = kwargs.get("widget_type", "unk_wt")
        self.kind = kwargs.get("kind", "unk_k")
        self.options = kwargs.get("options", {})

        self._value = self.default_value
        self._widgets = {}
        self._grid_search_options = str(self.default_value)

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

    def update_label(self):
        lbl = self.label
        if lbl is None:
            return False
        if (
            isinstance(self.allowed_values, dict)
            or isinstance(self.allowed_values, str)
            or (self.widget_type == "spin_box")
        ):
            lbl.setText(self.desc)
        elif isinstance(self.allowed_values, tuple) and (len(self.allowed_values) == 2):
            lbl.setText(f"{self.desc}: {self.value}")
        else:
            return False
        lbl.setToolTip(self.hint)
        return True

    def init_input(self, call_back):
        widget = self.input
        if widget is None:
            return False
        elif isinstance(self.allowed_values, dict):
            for key, value in self.allowed_values.items():
                widget.addItem(value, key)
                if self.value == key:
                    widget.setCurrentIndex(widget.count() - 1)
            widget.currentIndexChanged.connect(call_back)
        elif isinstance(self.allowed_values, tuple):
            if self.allowed_values == (0, 1):
                widget.setChecked(self.value == 1)
                widget.setText(self.desc)
                widget.stateChanged.connect(call_back)
            elif len(self.allowed_values) == 2:
                widget.setMinimum(self.allowed_values[0])
                widget.setMaximum(self.allowed_values[1])
                widget.setValue(int(self.value))
                widget.valueChanged.connect(call_back)
            else:
                return False
        elif isinstance(self.allowed_values, str):
            if call_back is not None:
                if hasattr(widget, "textEdited"):
                    widget.setText(self.value)
                    widget.textEdited.connect(call_back)
                elif hasattr(widget, "clicked"):
                    widget.setText(self.desc)
                    widget.clicked.connect(call_back)
        else:
            return False
        widget.setToolTip(self.hint)
        return True

    def update_input(self, new_values=None):
        if not self.is_input:
            return False
        widget = self.input
        if widget is None:
            return False
        if isinstance(self.allowed_values, dict):
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
                widget.clear()
                for key, value in self.allowed_values.items():
                    widget.addItem(value, key)
                    if bck_value == key:
                        widget.setCurrentIndex(widget.count() - 1)
                self._value = bck_value
            else:
                for i, key in enumerate(self.allowed_values):
                    if self.value == key:
                        widget.setCurrentIndex(i)
                        break
        elif isinstance(self.allowed_values, tuple):
            if self.allowed_values == (0, 1):
                widget.setChecked(self.value == 1)
            elif len(self.allowed_values) == 2:
                if (
                    (new_values is not None)
                    and isinstance(new_values, tuple)
                    and (self.allowed_values != new_values)
                ):
                    self.allowed_values = new_values
                    widget.setMinimum(self.allowed_values[0])
                    widget.setMaximum(self.allowed_values[1])
                widget.setValue(int(self.value))
            else:
                return False
        elif isinstance(self.allowed_values, str):
            widget.setText(self.value)
        else:
            return False
        widget.setToolTip(self.hint)
        return True

    def update_output(self, label_text: str = "", output_value=None, ignore_list=(), invert=False):
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
            widget.setText(self._value)
        elif self.allowed_values == "multi_line_text_output":
            widget.clear()
            widget.insertPlainText(self._value)
        elif self.allowed_values == "table_output":
            while widget.rowCount() > 0:
                widget.removeRow(0)
            if isinstance(self._value, dict):
                for k, v in self._value.items():
                    if ignore_list and (k in ignore_list):
                        continue
                    if invert:
                        insert_pos = 0
                    else:
                        insert_pos = widget.rowCount()
                    widget.insertRow(insert_pos)
                    widget.setItem(insert_pos, 0, QTableWidgetItem(f"{k}"))
                    if isinstance(v, list) or isinstance(v, tuple):
                        for i, value in enumerate(v):
                            widget.setItem(insert_pos, i + 1, QTableWidgetItem(f"{value}"))
                    else:
                        widget.setItem(insert_pos, 1, QTableWidgetItem(f"{v}"))
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
                if ("-" in opt_) and (";" in opt_):
                    bd, step = opt_.split(";")
                    left, right = bd.split("-")
                    left, right = min(int(left), int(right) + 1), max(int(left), int(right) + 1)
                    res.extend([i for i in range(left, right, int(step))])
                else:
                    res.append(opt_)
            except ValueError as e:
                print(f'String decoding failed: "{repr(e)}"')
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
                return f"{min_}-{max_};{step}"
            else:
                return ""
        else:
            return ""

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = value

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
                widget.setText(value)

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
        value.setText(self.desc)

    @property
    def gs_input(self):
        return self._widgets.get("gs_input", None)

    @gs_input.setter
    def gs_input(self, value):
        self._widgets["gs_input"] = value

    @property
    def is_input(self):
        return not isinstance(self.allowed_values, str) or ("input" in self.allowed_values)

    @property
    def is_output(self):
        return isinstance(self.allowed_values, str) and not ("input" in self.allowed_values)

    @property
    def is_neutral(self):
        return self.is_output and (self.allowed_values in ["label"])

    @property
    def is_default(self):
        return self.value == self.default_value


class IptParamHolder(object):
    def __init__(self, **kwargs):
        super(IptParamHolder, self).__init__()

        self._param_list = []
        self._kwargs = None
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
        for p in self._param_list:
            p.value = p.default_value
            if is_update_widgets:
                p.update_label()
                p.update_input()
                p.update_output()

    def add(self, new_item) -> IptParam:
        try:
            self._param_list.append(new_item)
        except Exception as e:
            print(f'Failed to add param "{repr(e)}')
        else:
            return new_item

    def add_combobox(
        self, name: str, desc: str, default_value: str = "", values: dict = {}, hint: str = ""
    ) -> IptParam:
        try:
            param = IptParam(
                name=name, desc=desc, default_value=default_value, allowed_values=values, hint=hint
            )
            param.widget_type = "combo_box"
            return self.add(param)
        except Exception as e:
            print(f'Failed to add param "{repr(e)}')

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
            name=name, desc=desc, default_value=default_value, allowed_values=(0, 1), hint=hint
        )
        param.widget_type = "checkbox"
        return self.add(param)

    def add_text_input(
        self, name: str, desc: str, default_value: str = "-", hint: str = ""
    ) -> IptParam:
        param = IptParam(
            name=name,
            desc=desc,
            default_value=default_value,
            allowed_values="single_line_text_input",
            hint=hint,
        )
        param.widget_type = "single_line_text_input"
        return self.add(param)

    def add_text_output(
        self, is_single_line: bool, name: str, desc: str, default_value: str = "-", hint: str = ""
    ) -> IptParam:
        if is_single_line:
            mode_ = "single_line_text_output"
        else:
            mode_ = "multi_line_text_output"
        param = IptParam(
            name=name, desc=desc, default_value=default_value, allowed_values=mode_, hint=hint
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
        param = IptParam(name=name, desc="", default_value="", allowed_values="label", hint="")
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
        values = {**values, **{k: k for k in all_colors_dict}}
        param = IptParam(
            name=name, desc=desc, default_value=default_value, allowed_values=values, hint=hint
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
                channel_info[1]: get_hr_channel_name(channel_info[1])
                for channel_info in create_channel_generator()
            },
        }
        param = IptParam(
            name=name, desc=desc, default_value=default_value, allowed_values=values, hint=hint
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
        self, name="color_map", default_value="c_2", desc="Select pseudo color map", hint=""
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
        param = self.add_text_input(name="roi_name", desc="ROI name", default_value="unnamed_roi")
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
                rectangle="Rectangle", circle="Circle, will be treated as rectangle for morphology"
            ),
        )
        param.kind = "roi_shape_selector"
        return self.add(param)

    def add_roi_settings(
        self,
        default_name: str = "unnamed_roi",
        default_type: str = "other",
        default_shape: str = "rectangle",
    ) -> IptParam:
        self.add_roi_name(default_value=default_name)
        self.add_roi_type(default_value=default_type)
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
        self.add_slider(
            name="canny_sigma",
            desc="Canny's sigma",
            default_value=2,
            minimum=0,
            maximum=20,
            hint="Sigma.",
        )
        self.add_slider(
            name="canny_first",
            desc="Canny's first Threshold",
            default_value=0,
            minimum=0,
            maximum=255,
            hint="First threshold for the hysteresis procedure.",
        )
        self.add_slider(
            name="canny_second",
            desc="Canny's second Threshold",
            default_value=255,
            minimum=0,
            maximum=255,
            hint="Second threshold for the hysteresis procedure.",
        )
        self.add_slider(
            name="kernel_size", desc="Kernel size", default_value=5, minimum=0, maximum=27
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
            name="min_t", desc="Threshold min value", default_value=0, minimum=0, maximum=255
        )
        self.add_spin_box(
            name="max_t", desc="Threshold max value", default_value=255, minimum=0, maximum=255
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
            values=dict(none="none", erode="erode", dilate="dilate", open="open", close="close"),
        )
        self.add_spin_box(
            name="kernel_size", desc="Kernel size", default_value=3, minimum=3, maximum=101
        )
        self.add_combobox(
            name="kernel_shape",
            desc="Kernel shape",
            default_value="ellipse",
            values=dict(ellipse="ellipse", rectangle="rectangle", cross="cross"),
        )
        self.add_spin_box(
            name="proc_times", desc="Iterations", default_value=1, minimum=1, maximum=100
        )

    def add_button(self, name: str, desc: str, index: int = 0, hint: str = "") -> IptParam:
        param = IptParam(
            name=name, desc=desc, default_value=index, allowed_values="input_button", hint=hint
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

    def add_date_picker(self, name: str, desc: str, default_value: int = 0, hint: str = ""):
        pass

    def reset_grid_search(self):
        for p in self._param_list:
            p.grid_search_options = str(p.default_value)
            gsw = p.gs_input
            if gsw is not None:
                gsw.setText(p.grid_search_options)

    def update_grid_search(self, ignore_composite: bool = True) -> None:
        for p in self._param_list:
            values = p.grid_search_options
            if ignore_composite and ((";" in values) or ("-" in values) or ("," in values)):
                continue
            p.grid_search_options = str(p.value)
            gsw = p.gs_input
            if gsw is not None:
                gsw.setText(p.grid_search_options)

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

    def get_value_of(self, key, default_value=None) -> str:
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
            return tmp

    def has_key(self, key: str) -> bool:
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
            if self.has_key(key):
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
            self.add(IptParam(name=key, desc="", default_value=value, allowed_values=None))
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

    def params_to_dict(self):
        dic = {}
        for p in self.gizmos:
            if p.is_input:
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
        self._old_lock_state = False

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

    def clone_params(self, source):
        for dst in self.gizmos:
            src = source.params.find_by_name(dst.name)
            if src is not None:
                dst.value = src.value

    def execute(self, param, **kwargs):
        pass

    def init_wrapper(self, **kwargs) -> AbstractImageProcessor:
        """Initializes wrapper according to key arguments

        Returns:
            AbstractImageProcessor -- Wrapper
        """
        self._kwargs = kwargs
        wrapper = self._get_wrapper()
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

        procs = list(itertools.product(*[p.decode_grid_search_options() for p in self.gizmos]))
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
        self.wrapper.error_holder.add_error(
            f"Missing {channel} channel", new_error_kind="source_issue"
        )

    def _get_wrapper(self):
        if "wrapper" in self.kwargs:
            value = self.kwargs.get("wrapper", None)
            if isinstance(value, str):
                self.wrapper = AbstractImageProcessor(value)
            else:
                self._wrapper = value
        return self._wrapper

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
                    return ((img - img.min()) / (img.max() - img.min()) * 255).astype(np.uint8)
                else:
                    c1, c2, c3 = cv2.split(img)
                    c1, c2, c3 = cv2.equalizeHist(c1), cv2.equalizeHist(c2), cv2.equalizeHist(c3)
                    return np.dstack((c1, c2, c3))
            else:
                return img.copy()
        else:
            self.wrapper.error_holder.add_error(f"Unknown source format {str(img.type)}")

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
            self.wrapper.error_holder.add_error(f"Unknown source format {str(img.type)}")

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
            self.wrapper.error_holder.add_error(f"Unknown source format {str(img.type)}")

    @staticmethod
    def apply_mask(image, mask):
        return cv2.bitwise_and(image, image, mask=mask)

    def match_image_size_to_source(
        self, img, source_mode: str = "source_file", ignore_list: tuple = ()
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
        self, wrapper, roi_names: list = [], selection_mode: str = "all_linked"
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

    def extract_source_from_args(self, source_mode: str = "source_file", ignore_list: tuple = ()):
        if not (source_mode in ignore_list):
            source_type = self.get_value_of(source_mode, "source")
        else:
            source_type = "source"
        if not ("median_filter_size" in ignore_list):
            median_filter_size = self.get_value_of("median_filter_size", 0)
        else:
            median_filter_size = 0
        if not ("color_space" in ignore_list):
            color_space = self.get_value_of("color_space", "RGB")
        else:
            color_space = "RGB"

        median_filter_size = 0 if median_filter_size == 1 else ensure_odd(median_filter_size)

        if source_type == "source":
            src_img = self.wrapper.current_image
        elif source_type == "mask":
            mask = self.wrapper.mask
            if mask is None:
                mask = self.wrapper.process_image(threshold_only=True)
                if mask is None:
                    self.wrapper.error_holder.add_error("Failed to build mask")
                    return None
                else:
                    src_img = self.wrapper.mask
            else:
                return mask
        elif source_type == "source_median":
            src_img = self.wrapper.current_image
            if median_filter_size == 0:
                median_filter_size = 5
        elif source_type == "source_roi":
            self.wrapper.init_rois()
            src_img = self.wrapper.apply_rois(self.wrapper.current_image)
        elif source_type == "process_roi":
            self.wrapper.init_rois()
            src_img = self.wrapper.crop_to_roi(
                img=self.wrapper.current_image, roi=type(self).__name__
            )
        elif source_type == "cropped_source":
            src_img = self.wrapper.crop_to_keep_roi(img=self.wrapper.current_image)
        elif source_type == "masked_source":
            thresh = self.wrapper.mask
            ret = (thresh is not None) or self.wrapper.process_image(threshold_only=True)
            if ret:
                masked_whole = self.wrapper.retrieve_stored_image("masked_whole")
                if masked_whole is not None:
                    src_img = masked_whole
                else:
                    masked_whole = self.wrapper.apply_mask(
                        self.wrapper.current_image, self.wrapper.mask, "white"
                    )
                    src_img = masked_whole
            else:
                self.wrapper.error_holder.add_error("Failed to build masked source")
                return None

        else:
            self.wrapper.error_holder.add_error(f"Unknown source mode: {source_type}")
            return None

        if color_space == "HSV":
            src_img = cv2.cvtColor(src_img, cv2.COLOR_BGR2HSV)
        elif color_space == "LAB":
            src_img = cv2.cvtColor(src_img, cv2.COLOR_BGR2LAB)

        if median_filter_size > 0:
            return cv2.medianBlur(src_img, median_filter_size)
        else:
            return src_img

    def apply_binary_threshold(self, wrapper, img, channel):
        min_ = self.get_value_of("min_t")
        max_ = self.get_value_of("max_t")
        median_filter_size = self.get_value_of("median_filter_size")
        median_filter_size = 0 if median_filter_size == 1 else ensure_odd(median_filter_size)

        min_, max_ = min(min_, max_), max(min_, max_)

        mask, _ = wrapper.get_mask(
            src_img=img,
            channel=channel,
            min_t=min_,
            max_t=max_,
            median_filter_size=median_filter_size,
        )

        return self.apply_morphology_from_params(mask)

    def apply_morphology_from_params(self, mask):
        kernel_size = self.get_value_of("kernel_size", 0)
        iter_ = self.get_value_of("proc_times", 1)
        kernel_shape = self.get_value_of("kernel_shape", None)

        if not (len(mask.shape) == 2 or (len(mask.shape) == 3 and mask.shape[2] == 1)):
            self._wrapper.error_holder.add_error("Morphology works only on mask images")
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
            return func(mask, kernel_size=kernel_size, proc_times=iter_, kernel_shape=k_shape)
        else:
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
            if LooseVersion(cv2.__version__) > LooseVersion("4.0.0"):
                contours_, _ = cv2.findContours(
                    mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
                )[-2]
            else:
                _, contours_, _ = cv2.findContours(
                    mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
                )[-2]
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

        self._wrapper.store_image(watershed_image, f"{dbg_suffix}_vis_labels", text_overlay=True)
        self._wrapper.store_image(
            source_image, f"{dbg_suffix}_labels_on_source_image", text_overlay=True
        )

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
        self, exclude_defaults: bool = True, excluded_params: tuple = (), forced_params: tuple = ()
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
        self, exclude_defaults: bool = True, excluded_params: tuple = (), forced_params: tuple = ()
    ):
        return (
            f"<ul>"
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
            ret.append("from ip_base.ip_abstract import AbstractImageProcessor")
        return ret

    def code_apply_roi(self, print_result=None, white_spaces=""):
        ws = "".join([" " for _ in range(0, len(f"{white_spaces}ipt_res = ipt.process_wrapper("))])
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
                [" " for _ in range(0, len(f"{white_spaces}ipt_res = ipt.process_wrapper("))]
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
            code_ = f"{white_spaces}wrapper = AbstractImageProcessor({wrapper_})\n"
            if target_data_base:
                code_ += f"{white_spaces}wrapper.target_database = target_data_base\n"
            code_ += f"{white_spaces}wrapper.lock = True\n"
        elif build_wrapper == "expected":
            code_ = f'{white_spaces}if wrapper is None:\n{white_spaces}    raise RuntimeError("Missing wrapper")\n'
        else:
            code_ = ""

        if use_with_clause:
            code_ += f"{white_spaces}with {type(self).__name__}({params_}) as (res, ed):\n"
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
        return "\n".join(self.code_imports(**kwargs)) + "\n\n\n" + self.code_body(**kwargs)

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
    def wrapper(self) -> AbstractImageProcessor:
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
    def use_case_order(self):
        if TOOL_GROUP_EXPOSURE_FIXING_STR in self.use_case:
            return 0
        elif TOOL_GROUP_ROI_DYNAMIC_STR in self.use_case:
            return 1
        elif TOOL_GROUP_ROI_STATIC_STR in self.use_case:
            return 2
        elif TOOL_GROUP_PRE_PROCESSING_STR in self.use_case:
            return 3
        elif TOOL_GROUP_THRESHOLD_STR in self.use_case:
            return 4
        elif TOOL_GROUP_MASK_CLEANUP_STR in self.use_case:
            return 5
        elif TOOL_GROUP_FEATURE_EXTRACTION_STR in self.use_case:
            return 6
        elif TOOL_GROUP_ANCILLARY_STR in self.use_case:
            return 7
        elif TOOL_GROUP_CLUSTERING_STR in self.use_case:
            return 8
        elif TOOL_GROUP_DEMO_STR in self.use_case:
            return 9
        elif TOOL_GROUP_DEFAULT_PROCESS_STR in self.use_case:
            return 10
        elif TOOL_GROUP_IMAGE_CHECK_STR in self.use_case:
            return 11
        elif TOOL_GROUP_IMAGE_GENERATOR_STR in self.use_case:
            return 12
        elif TOOL_GROUP_IMAGE_INFO_STR in self.use_case:
            return 13
        elif TOOL_GROUP_VISUALIZATION_STR in self.use_case:
            return 14
        elif TOOL_GROUP_WHITE_BALANCE_STR in self.use_case:
            return 15
        elif TOOL_GROUP_UNKNOWN_STR in self.use_case:
            return 16
        else:
            return 17

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


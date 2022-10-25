import numpy as np

from PySide2 import QtWidgets
from xml.etree import ElementTree
from io import StringIO

from PySide2.QtGui import QImage, QPixmap, QIcon
from PySide2.QtWidgets import (
    QLabel,
    QWidget,
    QHBoxLayout,
    QLineEdit,
    QTextBrowser,
    QTableWidget,
    QHeaderView,
    QTextEdit,
)

from ipso_phen.ui.qt_param_widgets import (
    QLineEditWthParam,
    QPushButtonWthParam,
    QComboBoxWthParam,
    QTextBrowserWthParam,
    QCheckBoxWthParam,
    QSliderWthParam,
    QSpinnerWthParam,
)


def scale(val, src, dst):
    return int(((val - src[0]) / float(src[1] - src[0])) * (dst[1] - dst[0]) + dst[0])


def cv2_to_qimage(img):
    qformat = QImage.Format_Indexed8
    if len(img.shape) == 3:
        if img.shape[2] == 4:
            qformat = QImage.Format_RGBA8888
        else:
            qformat = QImage.Format_RGB888
        height_, width_, *_ = img.shape
    elif len(img.shape) == 2:
        img = np.dstack((img, img, img))
        qformat = QImage.Format_RGB888
        height_, width_, *_ = img.shape
    else:
        height_, width_ = img.shape

    return QPixmap.fromImage(
        QImage(img, width_, height_, width_ * 3, qformat).rgbSwapped()
    )


def build_widgets(
    tool,
    param,
    allow_real_time: bool,
    call_backs: dict,
    do_feedback=None,
    grid_search_mode: bool = False,
):
    widget = None
    if grid_search_mode:
        if not param.is_input:
            return None, None
        label = QLabel(param.desc)
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        le = QLineEditWthParam(tool=tool, param=param)
        param.gs_input = le
        layout.addWidget(le)

        bt_af = QPushButtonWthParam(tool=tool, param=param, allow_real_time=False)
        bt_af.setIcon(QIcon(":/common/resources/Lightning.png"))
        bt_af.setToolTip("Auto fill grid search params")
        param.gs_auto_fill = bt_af
        layout.addWidget(bt_af)

        bt_update_from_param = QPushButtonWthParam(
            tool=tool, param=param, allow_real_time=False
        )
        bt_update_from_param.setIcon(QIcon(":/common/resources/Down.png"))
        bt_update_from_param.setToolTip("Copy value from tool")
        param.gs_copy_from_param = bt_update_from_param
        layout.addWidget(bt_update_from_param)

        bt_reset = QPushButtonWthParam(tool=tool, param=param, allow_real_time=False)
        bt_reset.setIcon(QIcon(":/common/resources/Refresh.png"))
        bt_reset.setToolTip("Reset to default value")
        param.gs_reset = bt_reset
        layout.addWidget(bt_reset)
    elif isinstance(param.allowed_values, dict):
        label = QLabel(param.desc)
        widget = QComboBoxWthParam(
            tool=tool, param=param, label=label, allow_real_time=allow_real_time
        )
    elif isinstance(param.allowed_values, str):
        if param.allowed_values == "single_line_text_output":
            label = QLabel(param.desc)
            widget = QLineEdit()
            widget.setReadOnly(True)
        elif param.allowed_values == "multi_line_text_output":
            label = QLabel(param.desc)
            widget = QTextBrowser()
            widget.setMaximumHeight(72)
        elif param.allowed_values == "label":
            label = QLabel(param.desc)
            widget = None
        elif param.allowed_values == "table_output":
            label = None
            widget = QTableWidget()
            widget.setColumnCount(len(param.desc))
            widget.setHorizontalHeaderLabels(param.desc)
            widget.horizontalHeader().setStretchLastSection(True)
            widget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        elif param.allowed_values == "single_line_text_input":
            label = QLabel(param.desc)
            widget = QLineEditWthParam(
                tool=tool, param=param, allow_real_time=allow_real_time
            )
        elif param.allowed_values == "multi_line_text_input":
            label = QLabel(param.desc)
            widget = QTextBrowserWthParam(
                tool=tool, param=param, allow_real_time=allow_real_time
            )
            widget.setLineWrapMode(QTextEdit.NoWrap)
            widget.setReadOnly(False)
            widget.setMaximumHeight(72)
        elif param.allowed_values == "input_button":
            label = None
            widget = QPushButtonWthParam(
                tool=tool, param=param, allow_real_time=allow_real_time
            )
        else:
            if do_feedback is not None:
                do_feedback(
                    status_message="Widget initialization: unknown param",
                    log_message=f"Widget initialization: unknown param {param.name}, allowed values {param.allowed_values}",
                )
            return None, None
    elif isinstance(param.allowed_values, tuple) or isinstance(
        param.allowed_values, list
    ):
        pa = tuple(param.allowed_values)
        if pa == (0, 1):
            label = None
            widget = QCheckBoxWthParam(
                tool=tool, param=param, label=label, allow_real_time=allow_real_time
            )
        elif len(pa) == 2:
            label = QLabel(param.desc)
            if param.widget_type == "slider":
                widget = QSliderWthParam(
                    tool=tool, param=param, label=label, allow_real_time=allow_real_time
                )
            elif param.widget_type == "spin_box":
                widget = QSpinnerWthParam(
                    tool=tool, param=param, label=label, allow_real_time=allow_real_time
                )
        else:
            if do_feedback is not None:
                do_feedback(
                    status_message="Widget initialization: unknown param",
                    log_message=f"Widget initialization: unknown param {param.name}, allowed values {param.allowed_values}",
                )
            return None, None
    else:
        if do_feedback is not None:
            do_feedback(
                status_message="Widget initialization: unknown param",
                log_message=f"Widget initialization: unknown param {param.name}, allowed values {param.allowed_values}",
            )
        return None, None

    if isinstance(tool, dict):
        tool_name = tool["uuid"]
    elif type(tool).__name__ in ("SettingsHolder", "PipelineSettings"):
        tool_name = "settings_holder"
    else:
        tool_name = tool.name
    param.init(
        tool_name=tool_name,
        label=label,
        widget=widget,
        grid_search_mode=grid_search_mode,
        **call_backs,
    )

    return widget, label

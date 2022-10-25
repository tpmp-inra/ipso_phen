from PySide2.QtWidgets import (
    QComboBox,
    QSlider,
    QSpinBox,
    QCheckBox,
    QLineEdit,
    QTextBrowser,
    QPushButton,
)

from PySide2.QtCore import Qt

from ipso_phen.ui.qt_custom_widgets import QCheckableComboBox


class QParamHandler(object):
    def __init__(self, tool, param, label=None, allow_real_time: bool = True):
        self._param = param
        if label:
            self._label = label
        self._tool = tool
        self._allow_real_time = allow_real_time

    @property
    def param(self):
        return self._param

    @property
    def label(self):
        if hasattr(self, "_label"):
            return self._label
        else:
            return None

    @property
    def tool(self):
        return self._tool

    @property
    def allow_real_time(self):
        return self._allow_real_time


class QComboBoxWthParam(QComboBox, QParamHandler):
    def __init__(self, tool, param, label, allow_real_time: bool = True, parent=None):
        QComboBox.__init__(self, parent)
        QParamHandler.__init__(self, tool, param, label, allow_real_time)


class QSliderWthParam(QSlider, QParamHandler):
    def __init__(self, tool, param, label, allow_real_time: bool = True):
        QSlider.__init__(self, Qt.Horizontal)
        QParamHandler.__init__(self, tool, param, label, allow_real_time)


class QSpinnerWthParam(QSpinBox, QParamHandler):
    def __init__(self, tool, param, label, allow_real_time: bool = True):
        QSpinBox.__init__(self)
        QParamHandler.__init__(self, tool, param, label, allow_real_time)


class QCheckBoxWthParam(QCheckBox, QParamHandler):
    def __init__(self, tool, param, label, allow_real_time: bool = True, parent=None):
        QCheckBox.__init__(self, parent)
        QParamHandler.__init__(self, tool, param, label, allow_real_time)


class QLineEditWthParam(QLineEdit, QParamHandler):
    def __init__(self, tool, param, allow_real_time: bool = True, parent=None):
        QLineEdit.__init__(self, parent)
        QParamHandler.__init__(self, tool, param, allow_real_time)


class QTextBrowserWthParam(QTextBrowser, QParamHandler):
    def __init__(self, tool, param, allow_real_time: bool = True, parent=None):
        QTextBrowser.__init__(self, parent)
        QParamHandler.__init__(self, tool, param, allow_real_time)


class QPushButtonWthParam(QPushButton, QParamHandler):
    def __init__(self, tool, param, allow_real_time: bool = False, parent=None):
        QPushButton.__init__(self, parent)
        QParamHandler.__init__(self, tool, param, allow_real_time)

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


class QComboBoxWthParam(QComboBox):
    def __init__(self, tool, param, label, allow_real_time: bool = True, parent=None):
        QComboBox.__init__(self, parent)
        self._param = param
        self._label = label
        self._tool = tool
        self._allow_real_time = allow_real_time

    @property
    def param(self):
        return self._param

    @property
    def label(self):
        return self._label

    @property
    def tool(self):
        return self._tool

    @property
    def allow_real_time(self):
        return self._allow_real_time


class QSliderWthParam(QSlider):
    def __init__(self, tool, param, label, allow_real_time: bool = True):
        QSlider.__init__(self, Qt.Horizontal)
        self._param = param
        self._label = label
        self._tool = tool
        self._allow_real_time = allow_real_time

    @property
    def param(self):
        return self._param

    @property
    def label(self):
        return self._label

    @property
    def tool(self):
        return self._tool

    @property
    def allow_real_time(self):
        return self._allow_real_time


class QSpinnerWthParam(QSpinBox):
    def __init__(self, tool, param, label, allow_real_time: bool = True):
        QSpinBox.__init__(self)
        self._param = param
        self._label = label
        self._tool = tool
        self._allow_real_time = allow_real_time

    @property
    def param(self):
        return self._param

    @property
    def label(self):
        return self._label

    @property
    def tool(self):
        return self._tool

    @property
    def allow_real_time(self):
        return self._allow_real_time


class QCheckBoxWthParam(QCheckBox):
    def __init__(self, tool, param, label, allow_real_time: bool = True, parent=None):
        QCheckBox.__init__(self, parent)
        self._param = param
        self._label = label
        self._tool = tool
        self._allow_real_time = allow_real_time

    @property
    def param(self):
        return self._param

    @property
    def label(self):
        return self._label

    @property
    def tool(self):
        return self._tool

    @property
    def allow_real_time(self):
        return self._allow_real_time


class QLineEditWthParam(QLineEdit):
    def __init__(self, tool, param, allow_real_time: bool = True, parent=None):
        QLineEdit.__init__(self, parent)
        self._param = param
        self._tool = tool
        self._allow_real_time = allow_real_time

    @property
    def param(self):
        return self._param

    @property
    def tool(self):
        return self._tool

    @property
    def allow_real_time(self):
        return self._allow_real_time


class QTextBrowserWthParam(QTextBrowser):
    def __init__(self, tool, param, allow_real_time: bool = True, parent=None):
        QTextBrowser.__init__(self, parent)
        self._param = param
        self._tool = tool
        self._allow_real_time = allow_real_time

    @property
    def param(self):
        return self._param

    @property
    def tool(self):
        return self._tool

    @property
    def allow_real_time(self):
        return self._allow_real_time


class QPushButtonWthParam(QPushButton):
    def __init__(self, tool, param, allow_real_time: bool = False, parent=None):
        QPushButton.__init__(self, parent)
        self._param = param
        self._tool = tool
        self._allow_real_time = allow_real_time

    @property
    def param(self):
        return self._param

    @property
    def tool(self):
        return self._tool

    @property
    def allow_real_time(self):
        return self._allow_real_time


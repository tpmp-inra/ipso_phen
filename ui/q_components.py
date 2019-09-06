from PyQt5.QtCore import Qt, pyqtSignal

from PyQt5.QtWidgets import (QCheckBox, QSlider, QComboBox, QPushButton, QLineEdit, QTreeWidgetItem, QTreeWidget,
                             QSpinBox)


def scale(val, src, dst):
    return int(((val - src[0]) / float(src[1] - src[0])) * (dst[1] - dst[0]) + dst[0])


class CTreeWidgetItem(QTreeWidgetItem):

    def setData(self, column, role, value):
        state = self.checkState(column)
        QTreeWidgetItem.setData(self, column, role, value)
        if (role == Qt.CheckStateRole) and (state != self.checkState(column)):
            tree_widget = self.treeWidget()
            if tree_widget is not None:
                tree_widget.itemChecked.emit(self, column)


class CTreeWidget(QTreeWidget):
    itemChecked = pyqtSignal(object, int)

    def __init__(self):
        QTreeWidget.__init__(self)
        self.itemChecked.connect(self.handle_item_checked)
        self.initializing_tree = False
        self.script_generator = None

    def handle_item_checked(self, item, column):
        if not self.initializing_tree:
            data = item.data(0, Qt.UserRole)
            self.script_generator.toggle_enabled_state(key=data)


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

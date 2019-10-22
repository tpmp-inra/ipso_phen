import numpy as np

from PyQt5.QtCore import Qt, pyqtSignal

from PyQt5.QtWidgets import (
    QCheckBox,
    QSlider,
    QComboBox,
    QLabel,
    QPushButton,
    QLineEdit,
    QTreeWidgetItem,
    QTreeWidget,
    QSpinBox,
    QApplication,
    QGraphicsView,
    QGraphicsScene,
)
from PyQt5.QtGui import QImage, QPixmap

# from ip_base import ip_common as ipc
from tools import shapes


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


class QMouseGraphicsView(QGraphicsView):
    def __init__(self, parent=None):
        super(QMouseGraphicsView, self).__init__(parent)
        self.auto_fit = True

        self.setScene(QGraphicsScene())
        self.zoom_in_factor = 1.1
        self.zoom_out_factor = 0.9
        self._main_image = None

        # self.setDragMode(QGraphicsView.ScrollHandDrag)

    def wheelEvent(self, event):
        modifiers = QApplication.keyboardModifiers()
        if modifiers == Qt.ControlModifier:
            self.auto_fit = False

            # Set Anchors
            self.setTransformationAnchor(QGraphicsView.NoAnchor)
            self.setResizeAnchor(QGraphicsView.NoAnchor)

            # Save the scene pos
            oldPos = self.mapToScene(event.pos())

            # Zoom
            if event.angleDelta().y() > 0:
                zoomFactor = self.zoom_in_factor
            else:
                zoomFactor = self.zoom_out_factor
            self.scale(zoomFactor, zoomFactor)

            # Get the new position
            newPos = self.mapToScene(event.pos())

            # Move scene to old position
            delta = newPos - oldPos
            self.translate(delta.x(), delta.y())
        else:
            super(QMouseGraphicsView, self).wheelEvent(event)

    def resizeEvent(self, event):
        if self.auto_fit:
            self.fitInView(self.sceneRect(), Qt.KeepAspectRatio)
        else:
            super(QMouseGraphicsView, self).resizeEvent(event)

    def mouseDoubleClickEvent(self, event):
        self.fit_to_canvas()

    def mousePressEvent(self, event):
        modifiers = QApplication.keyboardModifiers()
        if modifiers == Qt.ControlModifier:
            self.setDragMode(QGraphicsView.ScrollHandDrag)
        super(QMouseGraphicsView, self).mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        self.setDragMode(QGraphicsView.NoDrag)
        super(QMouseGraphicsView, self).mouseReleaseEvent(event)

    def fit_to_canvas(self):
        self.auto_fit = True
        self.fitInView(self.sceneRect(), Qt.KeepAspectRatio)

    def zoom_by_factor(self, factor):
        self.auto_fit = False
        self.scale(factor, factor)

    def zoom_in(self):
        self.zoom_by_factor(self.zoom_in_factor)

    def zoom_out(self):
        self.zoom_by_factor(self.zoom_out_factor)

    @property
    def main_image(self):
        return self._main_image

    @main_image.setter
    def main_image(self, value):
        if self._main_image is not None:
            self.scene().removeItem(self._main_image)
            self._main_image = None
        if value is not None:
            if isinstance(value, str):
                q_pix = QPixmap(value)
            else:
                qformat = QImage.Format_Indexed8
                if len(value.shape) == 3:
                    if value.shape[2] == 4:
                        qformat = QImage.Format_RGBA8888
                    else:
                        qformat = QImage.Format_RGB888
                    height_, width_, *_ = value.shape
                elif len(value.shape) == 2:
                    value = np.dstack((value, value, value))
                    qformat = QImage.Format_RGB888
                    height_, width_, *_ = value.shape
                else:
                    height_, width_ = value.shape

                q_pix = QPixmap.fromImage(
                    QImage(value, width_, height_, width_ * 3, qformat).rgbSwapped()
                )
            self._main_image = self.scene().addPixmap(q_pix)
            self.setSceneRect(self._main_image.boundingRect())
            self.fit_to_canvas()

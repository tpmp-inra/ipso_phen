import os

import numpy as np
import pandas as pd

from PyQt5.QtCore import Qt, pyqtSignal, QAbstractTableModel

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
    QFileDialog,
    QTableView,
    QItemDelegate,
    QStyle,
)
from PyQt5.QtGui import QImage, QPixmap, QBrush, QPen, QPalette, QColor

from tools import shapes
from ip_base import ip_common as ipc


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


class QColorDelegate(QItemDelegate):
    def __init__(self, parent=None, *args, **kwargs):
        QItemDelegate.__init__(self, parent, *args)
        self._palette: QPalette = kwargs.get("palette")

    def paint(self, painter, option, index):
        painter.save()

        df: pd.DataFrame = self.parent().model().df
        # set background color
        is_error_column = "error" in df.columns[index.column()]
        painter.setPen(QPen(Qt.NoPen))
        if is_error_column:
            try:
                num_val = int(index.data(Qt.DisplayRole))
                max_val = df[df.columns[index.column()]].max()
            except ValueError:
                num_val = None
                max_val = None
            if (num_val is not None) and (max_val is not None):
                colors = ipc.build_color_steps(
                    start_color=ipc.C_LIME, stop_color=ipc.C_RED, step_count=max_val + 1
                )
                painter.setBrush(QBrush(QColor(*ipc.bgr_to_rgb(colors[num_val]))))
        else:
            if option.state & QStyle.State_Selected:
                painter.setBrush(self._palette.highlight())
            else:
                painter.setBrush(self._palette.window())
        painter.drawRect(option.rect)

        # set text color
        value = index.data(Qt.DisplayRole)
        if option.state & QStyle.State_Selected:
            painter.setPen(QPen(self._palette.color(QPalette.HighlightedText)))
        else:
            painter.setPen(QPen(self._palette.color(QPalette.Text)))
        painter.drawText(option.rect, Qt.AlignCenter, str(value))

        painter.restore()

    def set_palette(self, new_palette):
        self._palette: QPalette = new_palette


class QPandasModel(QAbstractTableModel):
    def __init__(self, data):
        QAbstractTableModel.__init__(self)
        self._df = data

    def rowCount(self, parent=None):
        return 0 if self._df is None else self._df.shape[0]

    def columnCount(self, parnet=None):
        return 0 if self._df is None else self._df.shape[1]

    def data(self, index, role=Qt.DisplayRole):
        if index.isValid() and (self._df is not None):
            if role == Qt.DisplayRole:
                return str(self._df.iloc[index.row(), index.column()])
            elif role == Qt.ToolTipRole:
                return str(self._df.iloc[index.row(), index.column()])
        return None

    def setData(self, index, value, role):
        if (self._df is None) or not index.isValid() or (role != Qt.EditRole):
            return False
        row = index.row()
        if row < 0 or row >= len(self._df.values):
            return False
        column = index.column()
        if column < 0 or column >= self._df.columns.size:
            return False
        dt = self._df.iloc[:, column].dtypes
        if dt in [np.int64, np.int32, np.int16]:
            try:
                val = int(value)
            except ValueError:
                return False
        elif dt in [np.float64, np.float32, np.float16]:
            try:
                val = float(value)
            except ValueError:
                return False
        else:
            val = value
        self._df.iloc[[row], [column]] = val
        self.dataChanged.emit(index, index)
        return True

    def headerData(self, col, orientation, role):
        if (self._df is not None) and (orientation == Qt.Horizontal) and (role == Qt.DisplayRole):
            return self._df.columns[col]
        return None

    def flags(self, index):
        flags = super(self.__class__, self).flags(index)
        flags |= Qt.ItemIsEditable
        flags |= Qt.ItemIsSelectable
        flags |= Qt.ItemIsEnabled
        flags |= Qt.ItemIsDragEnabled
        flags |= Qt.ItemIsDropEnabled
        return flags

    @property
    def df(self):
        return self._df


class QPandasColumnsModel(QAbstractTableModel):
    def __init__(self, data):
        QAbstractTableModel.__init__(self)
        self._df = data

    def rowCount(self, parent=None):
        return 0 if self._df is None else len(list(self._df.columns))

    def columnCount(self, parnet=None):
        return 2

    def data(self, index, role=Qt.DisplayRole):
        if (
            index.isValid()
            and (self._df is not None)
            and (role == Qt.DisplayRole)
            or (role == Qt.ToolTipRole)
        ):
            if index.column() == 0:
                return self._df.columns[index.row()]
            elif index.column() == 1:
                return str(self._df[self._df.columns[index.row()]].dtypes)
        return None

    def headerData(self, col, orientation, role):
        if (self._df is not None) and (orientation == Qt.Horizontal) and (role == Qt.DisplayRole):
            if col == 0:
                return "Name"
            elif col == 1:
                return "Type"
        return None

    def flags(self, index):
        flags = super(self.__class__, self).flags(index)
        # flags |= Qt.ItemIsEditable
        flags |= Qt.ItemIsSelectable
        flags |= Qt.ItemIsEnabled
        # flags |= Qt.ItemIsDragEnabled
        # flags |= Qt.ItemIsDropEnabled
        return flags

    @property
    def df(self):
        return self._df


class QImageDatabaseModel(QAbstractTableModel):
    def __init__(self, dataframe, **kwargs):
        QAbstractTableModel.__init__(self)
        self.images = dataframe
        self.annotations = {}

    def rowCount(self, parent=None):
        return 0 if self.images is None else self.images.shape[0]

    def columnCount(self, parnet=None):
        return 0 if self.images is None else self._df.shape[1]

    def data(self, index, role=Qt.DisplayRole):
        if index.isValid() and (self._df is not None):
            if role == Qt.DisplayRole:
                return str(self.images.iloc[index.row(), index.column()])
            elif role == Qt.ToolTipRole:
                return str(self.images.iloc[index.row(), index.column()])
        return None

    def headerData(self, col, orientation, role):
        if (self._df is not None) and (orientation == Qt.Horizontal) and (role == Qt.DisplayRole):
            return self._df.columns[col]
        return None

    def flags(self, index):
        flags = super(self.__class__, self).flags(index)
        flags |= Qt.ItemIsSelectable
        flags |= Qt.ItemIsEnabled
        return flags

    def set_images(self, dataframe):
        self.images = dataframe
        self.modelReset.emit()

    def append_images(self, dataframe):
        self.columnsInserted.emit(0, 0)

    def remove_images(self, luis: list = []):
        self.modelReset.emit()

    def clear_images(self):
        self.images.drop(self.images.index, inplace=True)
        self.modelReset.emit()
